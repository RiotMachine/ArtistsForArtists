from flask          import Flask
from flask_login    import LoginManager
from flask_talisman import Talisman
from dotenv         import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

## SECRET_KEY is req for Flask cookies
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['RECAPTCHA_PUBLIC_KEY'] = os.environ.get('RECAPTCHA_PUBLIC_KEY')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.environ.get('RECAPTCHA_PRIVATE_KEY')
DB_LOCATION = os.environ.get('DB_LOCATION')

## .loopcontrols is for jinja2 control {% break %}
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

## Filter for titles with chars needing escaped when referenced in links
def urlEscape(string):
    return string.replace("?", "%3F")
app.jinja_env.filters["urlEscape"] = urlEscape

## setup for flask_login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access that page."

## setup for flask-talisman
### worth setting a csp at some point, but not worth
### keeping first iteration of the project offline
Talisman(
    app, 
    content_security_policy=None,
)

import ArtistsForArtists.routes as routes
app.register_blueprint(routes.subdomain)
app.register_blueprint(routes.account)

'''
# Session Cookies

## Set based on session activity
"{{ artistpage }}" - stores viewing credential for that artistpage after user inputs correct credential
"url" - holds a URL for redirect

## Other
"darkmode" - boolean 0 or 1 storing current session preference; default session var set for users based on saved darkmode pref
"work_id" - momentarily holds id of work being modfied or deleted within 'My Subdomain'
'''