from flask import abort, flash, g, redirect, request, url_for
from flask_login import current_user
from functools import wraps
from urllib.parse import urlparse
import sqlite3

# Functions

## Query functions
### Following Flask documentation for built-in SQLite3 support
### https://flask.palletsprojects.com/en/stable/patterns/sqlite3/
def dbOpenDict():
    con = getattr(g, '_database', None)
    if con is None:
        con = g._database = sqlite3.connect("artforart.db", autocommit=True)
        con.row_factory = sqlite3.Row
    return con

def dbQuery(query, args=(), jen=False):
    cur = dbOpenDict().execute(query, args)
    query = cur.fetchall()
    cur.close()
    return (query[0] if query else None) if jen else query

## Nav functions
def getPrevURL():
    referURL = request.referrer
    referHostname = urlparse(referURL).hostname
    destHostname = urlparse(request.url).hostname
    if referHostname == destHostname:
        return referURL
    else:
        return None

def getSubdomainID(artistpage):
    subdomain = dbQuery("SELECT id FROM subdomains WHERE pagename = ?", [artistpage], jen=True)
    if subdomain is None:
        abort(404)
    else:
        return subdomain['id']

def noCache(response):
	response.headers['Cache-Control'] = 'no-store'
	return response

## Other
### see: subdomainTextupload()
ALLOWED_EXTENSIONS = {'docx', 'md'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def userInput(inputName):
    return request.form.get(inputName)

# Wrappers
def loggedin_notallowed(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if current_user.is_authenticated:
			flash('You are already logged in', 'errorMessage')
			return redirect(url_for('homepage'))
		return f(*args, **kwargs)
	return decorated_function

def subdomain_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.subdomainID is None:
            flash('Please register an Artist Site to access that page', 'errorMessage')
            return redirect(url_for('account'))
        return f(*args, **kwargs)
    return decorated_function

# Filters
## Filter for titles with chars needing escaped when referenced in links
def urlEscape(string):
    return string.replace("?", "%3F")