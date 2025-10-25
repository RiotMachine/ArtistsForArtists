import urllib.parse as urllib
from flask                      import (Blueprint, abort, flash, g, jsonify, make_response, redirect, 
                                        render_template, request, session, url_for)
from flask_login                import current_user, login_required, login_user, logout_user
import pypandoc
import werkzeug.exceptions
from werkzeug.security          import check_password_hash as check_pass, generate_password_hash
from ArtistsForArtists          import app, login_manager
from ArtistsForArtists.helpers  import (allowedFile, dbQuery, getPrevURL, getSubdomainID, noCache, 
                                        userInput, loggedOutReq, subdomainReq)
import ArtistsForArtists.forms as wtforms
from ArtistsForArtists.classes  import Subdomain, User, Work

subdomain = Blueprint('subdomain', __name__, url_prefix='/r/<subName>', template_folder='templates/subdomains')
accounts = Blueprint('accounts', __name__, url_prefix='/account', template_folder='templates/accounts')

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
        session['darkmode'] = 1
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
    return render_template("apology.html"), 404

@app.errorhandler(405)
def handle_invalid_url(e):
    flash('You cant get there that way.', 'errorMessage')
    return redirect(url_for('homepage'))

@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_misc_bad_request(e):
    return redirect('/', code=400)


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
                               [username, generate_password_hash(password)])
            user = User(userInfo['id'], userInfo['username'], userInfo['passwordhash'])
            login_user(user, remember=form.rememberMe.data)
            flash('Registration successful!', 'successtext')
            response = make_response(redirect("/"))
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
                response = make_response(redirect("/"))
    else:
        session["url"] = getPrevURL()
        response = make_response(render_template("login.html", form=form))

    return noCache(response)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'errorMessage')
    return redirect("/")


# Account Pages
@accounts.route("/")
@login_required
def account():
    subdomain = dbQuery("SELECT pagename FROM subdomains WHERE id = ?",
                        [current_user.subdomainID], jen=True)
    return render_template("accountindex.html", subdomain=subdomain)

@accounts.route("/settings", methods=["GET", "POST"])
@login_required
def accountSettings():
    prefsQuery = dbQuery("SELECT prefString FROM prefs")
    prefs = []
    for prefQuery in prefsQuery:
        prefs.append(prefQuery['prefString'])

    form = wtforms.ChangePassForm()
    passErrorMsg = None

    if form.validate_on_submit():
        errorBool = False
        changepassBool = False

        if form.oldpass.data:
            if not check_pass(current_user.passhash, form.oldpass.data):
                passErrorMsg = "Enter the correct current password if you want to change it"
                errorBool = True
            else:
                changepassBool = True

        newprefsDict = {}
        for pref in prefs:
            newprefsDict[pref] = False
            if userInput(pref):
                newprefsDict[pref] = True

        if not errorBool:
            if changepassBool:
                current_user.changePass(form.newpass.data) 
            currentUser.updatePrefs(newprefsDict)
            flash('Settings saved', 'successtext')

    userprefs = current_user.getPrefsDict()
    response = make_response(render_template("accountsettings.html", 
                                             form=form, passErrorMsg=passErrorMsg,
                                             prefs=prefs, userprefs=userprefs))
    return noCache(response)

@accounts.route("/subdomain", methods=["GET", "POST"])
@login_required
@subdomainReq
def subdomainSettings():
    subdomain = Subdomain(current_user.subdomainID)
    works = subdomain.getWorksTable()

    form = wtforms.SubdomainSettingsForm()
    passErrorMsg = None

    if form.validate_on_submit():
        changepassBool = False
        # Only displaying the change pass option if authreqBool
        if form.oldpass.data:
            if not check_pass(subdomain.authPassHash, userInput("oldpass")):
                passErrorMsg = "Provide the correct current password to change it"
            else:
                changepassBool = True

        elif form.setauth.data and not subdomain.authReq:
            response = make_response(redirect(url_for('accounts.subdomainAddAuth'), code=307))
            return noCache(response)

        elif not form.setauth.data and subdomain.authReq:
            dbQuery("UPDATE subdomains SET authreq = 0 where id = ?", [subdomain.id])
            flash('Authentication turned off', 'successtext')

        if changepassBool:
            subdomain.changePass(form.newpass.data)
            flash('Subdomain password changed', 'successtext')
    
        subdomain = Subdomain(current_user.subdomainID)

    response = make_response(render_template("acctsubsettings.html", 
                                             works=works, authreqBool=subdomain.authReq,
                                             passErrorMsg=passErrorMsg, form=form))
    return noCache(response)

@accounts.route("/subdomain/addauth", methods=['POST'])
@login_required
@subdomainReq
def subdomainAddAuth():
    form = wtforms.NewPassForm()

    if form.validate_on_submit():
        dbQuery("UPDATE subdomains SET authpasshash = ?, authreq = 1 WHERE id = ?", 
                [generate_password_hash(form.newpass.data), current_user.subdomainID])
        flash('Authentication added', 'successtext')
        response = make_response(redirect(url_for('accounts.subdomainSettings')))
    else:
        response = make_response(render_template("acctsubauthadd.html", form=form))

    return noCache(response)

@accounts.route("/subdomain/add", methods=['POST'])
@login_required
@subdomainReq
def subdomainAddText():
    form = wtforms.NewWorkForm()
    form.genres.choices = [(genre['id'], genre['genreString']) for genre in GENRES]

    if form.validate_on_submit():
        Work.newWork(form.newTitle.data, current_user.subdomainID, 
                     userInput("workText"), form.genres.data)
        flash('Work added', 'successtext')
        response = make_response(redirect(url_for('accounts.subdomainSettings')))

    else:
        text = None
        textUpload = False
        if 'fileUpload' in request.files:
            ### https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
            textUpload = False
            file = request.files['fileUpload']
            if file.filename == '':
                flash('No selected file', 'errorMessage')
            elif file and allowedFile(file.filename):
                filetext = file.read()
                extension = file.filename.rsplit('.', 1)[1].lower()
                text = pypandoc.convert_text(filetext, 'md', format=extension)
                textUpload = True
            else:
                flash('Invalid file type', 'errorMessage')
        response = make_response(render_template("acctsubupload.html", 
                                                 form=form, text=text, textUpload=textUpload))

    return noCache(response)

@accounts.route("/subdomain/modify", methods=["POST"])
@login_required
@subdomainReq
def subdomainModifyText():
    form = wtforms.ModifyWorkForm()

    if userInput("workID"):
        work = Work(userInput("workID"))
        session['workID'] = work.id
        response = make_response(render_template("acctsubedit.html", 
                                                 form=form, work=work.getWorkRow()))
    else:
        if form.validate_on_submit():
            work = Work(session['workID'])
            work.modifyWork(userInput("workText"), form.newTitle.data)
            flash('Changes saved', 'successtext')
        else:
            flash('Something went wrong. Did you leave a field blank?', 'errorMessage')
        session.pop('workID', None)
        response = make_response(redirect(url_for('accounts.subdomainSettings')))

    return noCache(response)

@accounts.route("/subdomain/delete", methods=["POST"])
@login_required
@subdomainReq
def subdomainDeleteText():
    if userInput("workID"):
        work = Work(userInput("workID"))
        work.deleteWork()
        flash('Work deleted', 'errorMessage')
    else: 
        flash('Something went wrong. Did you leave a field blank?', 'errorMessage')

    response = make_response(redirect(url_for('accounts.subdomainSettings')))
    return noCache(response)


# AfA Pages
@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/search', methods=["GET", "POST"])
def search():
    subdomainsList = []
    q = request.args.get("q")

    if q:
        subdomains = dbQuery("SELECT pagename FROM subdomains WHERE pagename LIKE ? LIMIT 5", 
                             ["%" + q + "%"])
    else:
        subdomains = dbQuery("SELECT pagename FROM subdomains")
    for subdomain in subdomains:
        subdomainsList.append(subdomain['pagename'])

    if request.method == "GET":
        return render_template("search.html", pagenames=subdomainsList)
    if request.method == "POST":
        return subdomainsList

    
# Subdomain Pages
@subdomain.route('/')
def artistpage(subName):
    subdomain = Subdomain(getSubdomainID(subName))
    return render_template("artistpage.html", artistpage=subdomain.name)

@subdomain.route('/aboutme')
def aboutme(subName):
    subdomain = Subdomain(getSubdomainID(subName))

    aboutmeRow = subdomain.getAboutmeRow()
    htmlAboutme = pypandoc.convert_text(aboutmeRow['aboutme'], 'html', format='md')
    hasphoto = aboutmeRow['hasphoto']

    return render_template("aboutme.html", 
                           artistpage=subdomain.name, hasphoto=hasphoto, 
                           htmlAboutme=htmlAboutme)

@subdomain.route('/work')
def workindex(subName):
    subdomain = Subdomain(getSubdomainID(subName))
    
    if not subdomain.verifyAuth():
        return redirect(url_for('subdomain.authenticate', artistpage=subdomain.name))

    return render_template("workindex.html", 
                           artistpage=subdomain.name, worktitles=subdomain.getWorksList(),
                           genres = GENRES)

@subdomain.route('/authenticate', methods=["GET", "POST"])
def authenticate(subName):
    subdomain = Subdomain(getSubdomainID(subName))
    errorText = None

    if request.method == "POST":
        authTry = userInput('password')
        if check_pass(subdomain.authPassHash, authTry):
            session[subdomain.name] = authTry
            return redirect(url_for('subdomain.workindex', artistpage=subdomain.name))
        else:
            errorText = "Sorry, that password is incorrect."

    if subdomain.verifyAuth():
        return redirect(url_for('subdomain.workindex', artistpage=subdomain.name))

    return render_template("authenticate.html", 
                           artistpage=subdomain.name, errortext=errorText)

## files are stored in DB as markdown then converted to HTML when pulled
@subdomain.route('/work/<worktitle>')
def displaywork(subName, worktitle):
    subdomain = Subdomain(getSubdomainID(subName))

    if not subdomain.verifyAuth():
        return redirect(url_for('subdomain.authenticate', artistpage=subdomain.name))

    text = subdomain.getWork(worktitle)
    if text is None:
        abort(404)
    htmlText = pypandoc.convert_text(text['content'], 'html', format='md')
   
    return render_template("text.html", 
                           artistpage=subdomain.name, worktitle=worktitle, 
                           artist=subdomain.getArtistName(), htmlText=htmlText)