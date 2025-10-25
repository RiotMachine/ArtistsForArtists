from flask          import Flask
from flask_login    import LoginManager

app = Flask(__name__)

## SECRET_KEY is req for Flask cookies
app.config['SECRET_KEY'] = 'ChangingThisOnceWeGoLive'

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
login_manager.login_message_category = "errorMessage"

### set SQLite3 dB location
DB_LOCATION = "file:/home/jacob/Projects/ArtistsForArtists/artforart.db"

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