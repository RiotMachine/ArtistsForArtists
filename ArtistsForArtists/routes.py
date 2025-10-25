import urllib.parse as urllib
from flask                      import (Blueprint, abort, flash, g, jsonify, make_response, redirect, 
                                        render_template, request, session, url_for)
from flask_login                import current_user, login_required, login_user, logout_user
import pypandoc
import werkzeug.exceptions
from werkzeug.security          import check_password_hash as check_pass, generate_password_hash
from ArtistsForArtists          import app, login_manager
from ArtistsForArtists.helpers  import (dbQuery, getPrevURL, getSubdomainID, noCache, userInput,
                                        loggedOutReq, subdomainReq)
import ArtistsForArtists.forms as wtforms
from ArtistsForArtists.classes  import Subdomain, User, Work

subdomain = Blueprint('subdomain', __name__, url_prefix='/r/<subName>', template_folder='templates/subdomains')
account = Blueprint('account', __name__, url_prefix='/account', template_folder='templates/accounts')

GENRES = None
with app.app_context():
    GENRES = dbQuery("SELECT id, genreString FROM genres")

@login_manager.user_loader
def load_user(user_id):
    userInfo = dbQuery("SELECT id, username, passwordhash "
                       "FROM users WHERE id = ?", [user_id], jen=True)
    if userInfo is None:
        return None
    else:
        return User(userInfo['id'], userInfo['username'], userInfo['passwordhash'])

## routing for JSON fetch('/darkmode')
### allows for Dark Mode button selection to carry over from page to page
@app.route("/darkmode", methods=["POST"])
def darkmode():
    if session.get('darkmode') is None:
        session['darkmode'] = True
    else:
        session['darkmode'] = not session['darkmode']
    return {'darkmode_val': session['darkmode']}

## see: dbOpenDict()
@app.teardown_appcontext
def close_connection(exception):
    con = getattr(g, '_database', None)
    if con is not None:
        con.close()

# Error Pages
@app.errorhandler(403)
def handle_admin_url(e):
    flash('Nope, you''re not allowed to go there.', 'errorMessage')
    return redirect(url_for('homepage'))

@app.errorhandler(404)
def handle_invalid_url(e):
    flash('That url does not exist.')
    return redirect(url_for('homepage'))

@app.errorhandler(405)
def handle_invalid_url(e):
    flash('You cant get there that way.', 'errorMessage')
    return redirect(url_for('homepage'))

@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_misc_bad_request(e):
    flash('Something went wrong.')
    return redirect(url_for('homepage'), code=400)


# AfA Pages
@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/search', methods=["GET", "POST"])
def search():
    subNamesList = []
    q = request.args.get("q")

    if q:
        subNames = dbQuery("SELECT pagename FROM subdomains WHERE pagename LIKE ? LIMIT 5", 
                             ["%" + q + "%"])
    else:
        subNames = dbQuery("SELECT pagename FROM subdomains")
    for subName in subNames:
        subNamesList.append(subName['pagename'])

    if request.method == "GET":
        return render_template("search.html", subNames=subNamesList)
    if request.method == "POST":
        return subNamesList


# User Auth Pages
@app.route("/register", methods=["GET", "POST"])
@loggedOutReq
def register():

    form = wtforms.RegisterForm()
    username = form.username.data
    password = form.password.data

    if form.validate_on_submit():
        nameCheck = dbQuery("SELECT username FROM users WHERE username = ?",
                               [username], jen=True)
        if nameCheck is not None:
            flash("That username is unavailable", 'errorMessage')
            response = make_response(render_template("register.html", form=form))
        else:
            userInfo = dbQuery("INSERT INTO users (username, passwordhash) VALUES (?, ?) "
                               "RETURNING id, username, passwordhash",
                               [username, generate_password_hash(password)], jen=True)
            user = User(userInfo['id'], userInfo['username'], userInfo['passwordhash'])
            login_user(user, remember=form.rememberMe.data)
            flash('Registration successful!', 'successtext')
            response = make_response(redirect(url_for('homepage')))
    else:
        response = make_response(render_template("register.html", form=form))
    
    return noCache(response)

@app.route("/login", methods=["GET", "POST"])
@loggedOutReq
def login():

    form = wtforms.LoginForm()
    username = form.username.data
    password = form.password.data

    if form.validate_on_submit():
        userInfo = dbQuery("SELECT id, username, passwordhash FROM users WHERE username = ?", 
                            [username], jen=True)
        if userInfo is None or not check_pass(userInfo['passwordhash'], password):
            flash("Your username or password is incorrect", 'errorMessage')
            response = make_response(render_template("login.html", form=form))
        else:
            user = User(userInfo['id'], userInfo['username'], userInfo['passwordhash'])
            login_user(user, remember=form.rememberMe.data)
            current_user.setupPrefs()
            if session.get("url") is not None and ((urllib.urlparse(session['url'])[2] != url_for('login')) and 
                                                   (urllib.urlparse(session['url'])[2] != url_for('register')) and
                                                   (urllib.urlparse(session['url'])[2] != url_for('homepage'))):
                response = make_response(redirect(session["url"]))
            else:
                flash('Login successful!', 'successtext')
                response = make_response(redirect(url_for('homepage')))
    else:
        session["url"] = getPrevURL()
        response = make_response(render_template("login.html", form=form))

    return noCache(response)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'errorMessage')
    return redirect(url_for('homepage'))


# Account Pages
@account.route("/")
@login_required
def index():
    subdomain = None
    if current_user.subdomainID is not None:
        subdomain = Subdomain(current_user.subdomainID)
    return render_template("acctIndex.html", subdomain=subdomain)

@account.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    prefsQuery = dbQuery("SELECT prefString FROM prefs")
    prefs = []
    for prefQuery in prefsQuery:
        prefs.append(prefQuery['prefString'])

    form = wtforms.ChangePassForm()

    if form.validate_on_submit():
        if form.oldpass.data:
            if not check_pass(current_user.passhash, form.oldpass.data):
                flash('Password not saved. Enter the correct current password')
            else:
                current_user.changePass(form.newpass.data)
                flash('Password changed', 'successtext')

        newprefsDict = {}
        for pref in prefs:
            newprefsDict[pref] = False
            if userInput(pref):
                newprefsDict[pref] = True

        current_user.updatePrefs(newprefsDict)

    userprefs = current_user.getPrefsDict()
    response = make_response(render_template("acctSettings.html", 
                                             form=form, prefs=prefs, userprefs=userprefs))
    return noCache(response)

@account.route("/subdomain", methods=["GET", "POST"])
@login_required
@subdomainReq
def subdomainSettings():
    subdomain = Subdomain(current_user.subdomainID)
    works = subdomain.getWorksTable()
    form = wtforms.SubdomainSettingsForm()

    if form.validate_on_submit():

        if form.oldpass.data:
            if not check_pass(subdomain.authPassHash, form.oldpass.data):
                flash('Password not saved. Enter the correct current password')
            else:
                subdomain.changePass(form.newpass.data)
                flash('Subdomain password changed', 'successtext')

        elif form.setAuth.data and not subdomain.authReq:
            response = make_response(redirect(url_for('account.subdomainAuthEdit')))
            return noCache(response)

        elif not form.setAuth.data and subdomain.authReq:
            dbQuery("UPDATE subdomains SET authreq = 0 where id = ?", [subdomain.id])
            flash('Authentication turned off', 'successtext')

        subdomain = Subdomain(current_user.subdomainID)

    response = make_response(render_template("acctSubSettings.html", 
                                             works=works, authreqBool=subdomain.authReq,
                                             form=form))
    return noCache(response)

@account.route("/subdomain/addauth", methods=['GET', 'POST'])
@login_required
@subdomainReq
def subdomainAuthEdit():
    form = wtforms.NewPassForm()

    if form.validate_on_submit():
        dbQuery("UPDATE subdomains SET authpasshash = ?, authreq = 1 WHERE id = ?", 
                [generate_password_hash(form.newpass.data), current_user.subdomainID])
        flash('Authentication added', 'successtext')
        response = make_response(redirect(url_for('account.subdomainSettings')))
    else:
        response = make_response(render_template("acctSubAuthEdit.html", form=form))

    return noCache(response)

@account.route("/subdomain/mod", methods=['GET', 'POST'])
@login_required
@subdomainReq
def subdomainTextMod():
    modForm = wtforms.ModWorkForm()
    modForm.genres.choices = [(genre['id'], genre['genreString']) for genre in GENRES]
    uploadForm = wtforms.UploadWorkForm()
    text = None
    oldTitle = None
    genre = None

    if "submit" in request.form and modForm.validate_on_submit():
        ### https://stackoverflow.com/questions/5074803/retrieving-parameters-from-a-url
        referer = urllib.urlparse(request.referrer)
        if (refererQuery := urllib.parse_qs(referer.query)):
            work = Work(refererQuery['workID'][0])
            work.modifyWork(userInput("workText"), modForm.newTitle.data, modForm.genres.data)
        else:
            Work.newWork(modForm.newTitle.data, current_user.subdomainID, 
                        userInput("workText"), modForm.genres.data)
        flash('Changes saved', 'successtext')
        response = make_response(redirect(url_for('account.subdomainSettings')))


    else:
        if "upload" in request.form and uploadForm.validate_on_submit():
            file = uploadForm.upload.data
            ### https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
            filetext = file.read()
            extension = file.filename.rsplit('.', 1)[1].lower()
            text = pypandoc.convert_text(filetext, 'md', format=extension)

        if request.args.get("workID"):
            workID = dbQuery("SELECT id FROM works WHERE id = ?", [request.args.get("workID")], jen=True)
            if workID is None:
                abort(404)
            work = Work(workID['id'])
            workDeets = work.getWorkRow()
            oldTitle = workDeets['title']
            genre = workDeets['genreID']
            if text is None:
                text = workDeets['content']

        response = make_response(render_template("acctSubTxtMod.html", 
                                                form=modForm, uploadForm=uploadForm,
                                                oldTitle=oldTitle, text=text, genre=genre))
    return noCache(response)

@account.route("/subdomain/delete", methods=["POST"])
@login_required
@subdomainReq
def subdomainTextDelete():
    work = Work(userInput("workID"))
    work.deleteWork()
    flash('Work deleted', 'errorMessage')
    response = make_response(redirect(url_for('account.subdomainSettings')))
    return noCache(response)

    
# Subdomain Pages
@subdomain.route('/')
def index(subName):
    subdomain = Subdomain(getSubdomainID(subName))
    return render_template("subIndex.html", subName=subdomain.name)

@subdomain.route('/aboutme')
def aboutme(subName):
    subdomain = Subdomain(getSubdomainID(subName))

    aboutmeRow = subdomain.getAboutmeRow()
    htmlAboutme = pypandoc.convert_text(aboutmeRow['aboutme'], 'html', format='md')
    hasphoto = bool(aboutmeRow['hasphoto'])

    return render_template("subAboutme.html", 
                           subName=subdomain.name, hasphoto=hasphoto, 
                           htmlAboutme=htmlAboutme)

@subdomain.route('/work')
def works(subName):
    subdomain = Subdomain(getSubdomainID(subName))
    
    if not subdomain.verifyAuth():
        return redirect(url_for('subdomain.authenticate', subName=subdomain.name))

    return render_template("subWorks.html", 
                           subName=subdomain.name, works=subdomain.getWorksList(),
                           genres = GENRES)

@subdomain.route('/authenticate', methods=["GET", "POST"])
def authenticate(subName):
    subdomain = Subdomain(getSubdomainID(subName))
    form = wtforms.AuthForm()
    errorText = None

    if form.validate_on_submit():
        authTry = form.password.data
        if check_pass(subdomain.authPassHash, authTry):
            session[subdomain.name] = authTry
            return redirect(url_for('subdomain.works', subName=subdomain.name))
        else:
            errorText = "Sorry, that password is incorrect."

    elif subdomain.verifyAuth():
        return redirect(url_for('subdomain.works', subName=subdomain.name))

    return render_template("subAuth.html", form=form,
                           subName=subdomain.name, errortext=errorText)

## files are stored in DB as markdown then converted to HTML when pulled
@subdomain.route('/work/<worktitle>')
def text(subName, worktitle):
    subdomain = Subdomain(getSubdomainID(subName))

    if not subdomain.verifyAuth():
        return redirect(url_for('subdomain.authenticate', subName=subdomain.name))

    text = subdomain.getWork(worktitle)
    if text is None:
        abort(404)
    htmlText = pypandoc.convert_text(text['content'], 'html', format='md')
   
    return render_template("subText.html", 
                           subName=subdomain.name, worktitle=worktitle, 
                           artist=subdomain.getArtistName(), htmlText=htmlText)