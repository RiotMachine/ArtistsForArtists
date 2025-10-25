# Implements a CMS (content management system)

## Pypandoc is a Python wrapper for pandoc (file conversion software)
### https://github.com/JessicaTegner/pypandoc
### https://pandoc.org/
## flask_login for session management
### https://flask-login.readthedocs.io/en/latest
from flask import (Flask, Blueprint, abort, flash, g, jsonify, make_response, 
                   redirect, render_template, request, session, url_for)
from classes import Subdomain, User, Work
from helpers import (allowed_file, dbQuery, getPrevURL, getSubdomainID, noCache, 
                     urlEscape, userInput, loggedin_notallowed, subdomain_req)
from forms import (ChangePassForm, LoginForm, ModifyWorkForm, NewPassForm, 
                   NewWorkForm, RegisterForm, SubdomainSettingsForm)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from pypandoc import convert_text
from urllib.parse import urlparse
from werkzeug.exceptions import BadRequest
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

## SECRET_KEY is req for Flask cookies
## .loopcontrols is for jinja2 control {% break %}
## wsgi_app is Windows-provided code for default Python Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'RubberJamEatPolyTankAllenFolly'
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.jinja_env.filters["urlEscape"] = urlEscape
wsgi_app = app.wsgi_app

## setup for flask_login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access that page."
login_manager.login_message_category = "errorMessage"
@login_manager.user_loader
def load_user(user_id):
    userInfo = dbQuery("SELECT id, username, passwordhash "
                       "FROM users WHERE id = ?", [user_id], jen=True)
    if userInfo is None:
        return None
    else:
        return User(userInfo['id'], userInfo['username'], userInfo['passwordhash'])

## Globals
### Used to initalize error messages
### If error message has changed from this value, we know error has been enountered
ERRORCHECKVALUE = "VOID"

## see: dbOpenDict()
@app.teardown_appcontext
def close_connection(exception):
    con = getattr(g, '_database', None)
    if con is not None:
        con.close()


## routing for JSON fetch('/darkmode')
### allows for Dark Mode button selection to carry over from page to page
### does not change the user's pref
@app.route("/darkmode", methods=["GET", "POST"])
def darkmode():
    if request.method == "POST":
        if session.get('darkmode') is None:
            session['darkmode'] = 1
        else:
            session['darkmode'] = not session['darkmode']
        return {'darkmode_val': session['darkmode']}
    else:
        abort(403)


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

@app.errorhandler(BadRequest)
def handle_misc_bad_request(e):
    return redirect('/', code=400)


# User Auth Pages
@app.route("/register", methods=["GET", "POST"])
@loggedin_notallowed
def register():

    form = RegisterForm()
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
@loggedin_notallowed
def login():

    form = LoginForm()
    username = form.username.data
    password = form.password.data

    if form.validate_on_submit():
        userInfo = dbQuery("SELECT id, username, passwordhash FROM users WHERE username = ?", 
                        [username], jen=True)
        if userInfo is None or not check_password_hash(userInfo['passwordhash'], password):
            flash("Your username or password is incorrect", 'errorMessage')
            response = make_response(render_template("login.html", form=form))
        else:
            user = User(userInfo['id'], userInfo['username'], userInfo['passwordhash'])
            login_user(user, remember=form.rememberMe.data)
            current_user.setupUserPrefs()
            if session.get("url") is not None and ((urlparse(session['url'])[2] != url_for('login')) and 
                                                   (urlparse(session['url'])[2] != url_for('register')) and
                                                   (urlparse(session['url'])[2] != url_for('homepage'))):
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
@app.route("/account")
@login_required
def account():
    subdomain = dbQuery("SELECT pagename FROM subdomains WHERE id = ?",
                        [current_user.subdomainID], jen=True)
    return render_template("accountindex.html", subdomain=subdomain)

@app.route("/account/settings", methods=["GET", "POST"])
@login_required
def accountSettings():
    prefsQuery = dbQuery("SELECT prefString FROM prefs")
    prefs = []
    for prefQuery in prefsQuery:
        prefs.append(prefQuery['prefString'])

    form = ChangePassForm()
    passErrorMsg = None

    if form.validate_on_submit():
        errorBool = False
        changepassBool = False

        if form.oldpass.data:
            if not check_password_hash(current_user.passhash, form.oldpass.data):
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
            flash('Settings saved', 'successtext')
            current_user.modUserSettings(changepassBool, newprefsDict)

    userprefs = current_user.getUserPrefsDict()
    response = make_response(render_template("accountsettings.html", 
                                             form=form, passErrorMsg=passErrorMsg,
                                             prefs=prefs, userprefs=userprefs))
    return noCache(response)

@app.route("/account/subdomain", methods=["GET", "POST"])
@login_required
@subdomain_req
def subdomainSettings():
    subdomain = Subdomain(current_user.subdomainID)
    works = subdomain.getWorksTable()

    form = SubdomainSettingsForm()
    passErrorMsg = None

    if form.validate_on_submit():
        changepassBool = False
        # Only displaying the change pass option if authreqBool
        if form.oldpass.data:
            if not check_password_hash(subdomain.authPassHash, userInput("oldpass")):
                passErrorMsg = "Provide the correct current password to change it"
            else:
                changepassBool = True

        elif form.setauth.data and not subdomain.authReq:
            response = make_response(redirect(url_for('subdomainAddAuth'), code=307))
            return noCache(response)

        elif not form.setauth.data and subdomain.authReq:
            dbQuery("UPDATE subdomains SET authreq = 0 where id = ?", [subdomain.id])
            flash('Authentication turned off', 'successtext')

        if changepassBool:
            dbQuery("UPDATE subdomains SET authpasshash = ? WHERE id = ?", 
                    [generate_password_hash(userInput("newpass")), subdomain.id])
            flash('Subdomain password changed', 'successtext')
    
        subdomain = Subdomain(current_user.subdomainID)

    response = make_response(render_template("acctsubsettings.html", 
                                             works=works, authreqBool=subdomain.authReq,
                                             passErrorMsg=passErrorMsg, form=form))
    return noCache(response)

@app.route("/account/subdomain/addauth", methods=['POST'])
@login_required
@subdomain_req
def subdomainAddAuth():
    form = NewPassForm()

    if form.validate_on_submit():
        dbQuery("UPDATE subdomains SET authpasshash = ?, authreq = 1 WHERE id = ?", 
                [generate_password_hash(form.newpass.data), current_user.subdomainID])
        flash('Authentication added', 'successtext')
        response = make_response(redirect(url_for('subdomainSettings')))
    else:
        response = make_response(render_template("acctsubauthadd.html", form=form))

    return noCache(response)

@app.route("/account/subdomain/add", methods=['POST'])
@login_required
@subdomain_req
def subdomainAddText():
    genres = dbQuery("SELECT id, genreString FROM genres")
    form = NewWorkForm()
    form.genres.choices = [(genre['id'], genre['genreString']) for genre in genres]

    if form.validate_on_submit():
        Work.newWork(form.newTitle.data, current_user.getUserArtistID(), 
                     userInput("workText"), form.genres.data)
        flash('Work added', 'successtext')
        response = make_response(redirect(url_for('subdomainSettings')))

    else:
        text = None
        textUpload = False
        if 'fileUpload' in request.files:
            ### https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
            textUpload = False
            file = request.files['fileUpload']
            if file.filename == '':
                flash('No selected file', 'errorMessage')
            elif file and allowed_file(file.filename):
                filetext = file.read()
                extension = file.filename.rsplit('.', 1)[1].lower()
                text = convert_text(filetext, 'md', format=extension)
                textUpload = True
            else:
                flash('Invalid file type', 'errorMessage')
        response = make_response(render_template("acctsubupload.html", 
                                                 form=form, text=text, textUpload=textUpload))

    return noCache(response)

@app.route("/account/subdomain/modify", methods=["POST"])
@login_required
@subdomain_req
def subdomainModifyText():
    form = ModifyWorkForm()

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
        response = make_response(redirect(url_for('subdomainSettings')))

    return noCache(response)

@app.route("/account/subdomain/delete", methods=["POST"])
@login_required
@subdomain_req
def subdomainDeleteText():
    if userInput("workID"):
        work = Work(userInput("workID"))
        work.deleteWork()
        flash('Work deleted', 'errorMessage')
    else: 
        flash('Something went wrong. Did you leave a field blank?', 'errorMessage')

    response = make_response(redirect(url_for('subdomainSettings')))
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
@app.route('/r/<artistpage>')
def artistpage(artistpage):
    subdomain = Subdomain(getSubdomainID(artistpage))
    return render_template("artistpage.html", artistpage=subdomain.name)

@app.route('/r/<artistpage>/aboutme')
def aboutme(artistpage):
    subdomain = Subdomain(getSubdomainID(artistpage))

    aboutmeRow = subdomain.getAboutmeRow()
    htmlAboutme = convert_text(aboutmeRow['aboutme'], 'html', format='md')
    hasphoto = aboutmeRow['hasphoto']

    return render_template("aboutme.html", 
                           artistpage=subdomain.name, hasphoto=hasphoto, htmlAboutme=htmlAboutme)

@app.route('/r/<artistpage>/work')
def workindex(artistpage):
    subdomain = Subdomain(getSubdomainID(artistpage))

    if not subdomain.verifyAuth():
        return redirect(url_for('authenticate', artistpage=subdomain.name))

    return render_template("workindex.html", 
                           artistpage=subdomain.name, worktitles=subdomain.getWorkList())

@app.route('/r/<artistpage>/authenticate', methods=["GET", "POST"])
def authenticate(artistpage):
    subdomain = Subdomain(getSubdomainID(artistpage))
    errorText = None

    if request.method == "POST":
        authTry = userInput('password')
        if check_password_hash(subdomain.authPassHash, authTry):
            session[subdomain.name] = authTry
            return redirect(url_for('workindex', artistpage=subdomain.name))
        else:
            errorText = "Sorry, that password is incorrect."

    if subdomain.verifyAuth():
        return redirect(url_for('workindex', artistpage=subdomain.name))

    return render_template("authenticate.html", 
                           artistpage=subdomain.name, errortext=errorText)

## files are stored in DB as markdown then converted to HTML when pulled
@app.route('/r/<artistpage>/work/<worktitle>')
def displaywork(artistpage, worktitle):
    subdomain = Subdomain(getSubdomainID(artistpage))

    if not subdomain.verifyAuth():
        return redirect(url_for('authenticate', artistpage=subdomain.name))

    text = subdomain.getWork(worktitle)
    if text is None:
        abort(404)
    htmlText = convert_text(text['content'], 'html', format='md')

    name = dbQuery("SELECT firstname, lastname FROM artists, subdomains "
                   "WHERE subdomains.artistID = artists.ID AND subdomains.id = ?", 
                   [subdomain.id], jen=True)
    artistString = name['firstname'] + " " + name['lastname']
   
    return render_template("text.html", 
                           artistpage=subdomain.name, worktitle=worktitle, artist=artistString, 
                           htmlText=htmlText)


# Windows-provided default Python Flask app code
if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
