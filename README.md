# Artists for Artists

Artists for Artists (AfA) provides a content management system (CMS). 
Unlike other content management systems like Blogspot and Substack, it orients its design decisions around authors, not readers. 
CMSes have to this point failed to provide for authors' unique needs such as submission tracking, version management, and industry-mandated privacy.
AfA seeks to change that.


## Current State:

### URL:

artistsforartists.art

### Video Demo:  

https://youtu.be/FWWigC2IOIg

### Summary:
This first iteration of AfA implements core functionalities that an artist might want when displaying their work.
It answers the question, What core functionalities do I need the site to have before I display my Artist page to friends and family?

There are two kinds of account, Artist and Viewer.

An Artist is allowed one URL path for their work of the type 'domainname.com/artistpage/...' 
Artists have the ability to upload a bio and works.
They can make their works password protected. 
On the backend, they are able to add, modify, and delete works. 
They are also able to turn on/off password protection or change the needed credential.
If an artist page is password protected guests need to recredential themselves each time they access the site in a new browser session.

Viewers are able to save darkmode preferences and change their account password. 

Individuals without accounts are and will be able to read artist pages. 

AfA stores artists' bios and work in a database which is accessed to generate an index of each artist's work as well as pages containing those works.

### Design decisions:

1. Each Artist gets only one URL path

    Allowing an artist multiple URL paths would defeat the single source of truth component of the app.

2. URL paths are designed around artists, not users

    Not all artists are alive. We want users to be individuals who log into the site, artist or no. We want to allow the option for artists pages for individuals who are no longer with us.


### User experience

#### Landing and Search page

The default landing page allows access to a sidebar link to an index of all Artist pages on the platform. The landing page can be returned to using a button at the bottom of every page on the site.

#### Artist-specific URLs

Each artist-specific URL contains

- About Me
- Works

The About Me page text is customizable using Markdown formatting. The basic design is a segment of text and an artist portrait.
The Works index lists all of an artist's works in our database. Each work is accessible through a hyperlink on this page.
	
#### Settings pages

There are three settings pages. 

- My Account
- Settings
- My Subdomain

My Account displays a summary of the user's account.
In Settings users can see and change prefs, and also their password.
In My Subdomain artists can change subdomain settings as well as add, edit, or delete work.

### Architecture

The site is a Flask app using jinja2 templates running on top of a SQLITE database.

#### SQL database

The database has 3 central tables: 

- Users
- Subdomains
- Works

The subdomain table is used to store the artist's details and settings for his/her URL path. 
The works table is used to store works the artist uploads.
Works are linked to a subdomain in a M:1 relationship. Users and subdomains exist in a 1:1 relationship. 
However, not every user has a subdomain, and not every subdomain has a user.

#### Python/Flask backend

The site runs on Python Flask. The app is initialized in __init__.py. 
Web navigation logic is handled in routes.py. User, Subdomain, and Work classes handle methods unique to instances of those objects.

#### Dependencies

The site would not be possible without several web resources and libraries. 
Pypandoc allows the site to dynamically generate html and save text using Pandoc. Text is stored in markdown.
Flask-Login handles user session management. EasyMDE provides the authors' text editor.

#### jinja2 html templating

A note on the templating structure is in order. There is a primary template.html. 
Each 'section' of the site then builds off this template with one of its own.
Unique pages within each section are variations on that section's template.

#### /static

Static contains favicon files as well as custom JavaScript. The site uses Bootstrap (through a CDN) to deliver a responsive CSS framework.
Darkmode is made possible through JavaScript that toggles Bootstrap's built in darkmode setting.

## Upcoming improvements:

The current state of the site, while sufficient as an MVP, has some way to go before it lives up to its intended mission.
We do not want to become another Substack, with addictive endless feeds and bloated design. 
Still, there is room for growth while maintaining a clean and simple home for art.

### For v1.2:

- Searchbar in header to allow users to search for and access an artist's page from anywhere on the site

- User 'like' and 'follow' functionality so users can see on their homepages when favorite authors have uploaded new work and have easy access to those they enjoy

- Artist submission tracking and formatting

- Option to embed media in works pages (such as videos or audio of a reading)

### Future improvements

- Subdomain-level display customization

- Locally served and tailored Bootstrap (via Sass)

- Expanded functionalities for visual and auditory artists

- Social networking capabilities

    - User-to-user Artist page sharing/recommendation

    - User-to-Artist interaction

    - Artist page statistics
