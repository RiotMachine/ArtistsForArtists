# Artists for Artists

Artists for Artists (AfA) provides a content management system (CMS).

Its primary focus is to be designed around and to streamline the artist experience.

### Video Demo:  

https://youtu.be/7maRUPDGiE4

### Description:

There will be two kinds of account, Artist and Viewer.

An Artist is allowed one URL path for their work of the type 'domainname.com/artistpage/...' Artists can make their works password protected, and can custom style their URL path.

Viewers will be able to create accounts to store favorite artist pages. They will also be able to comment on works and interact with artists and other users, enabling social networking of artists and fans.

Individuals without accounts will still be able to read artist pages. If an artist page is password protected these guests will need to recredential themselves each time they access the site in a new browser session or if the credential changes.

AfA stores artists' work in a database which is accessed to generate an index of each artist's work and as well as pages containing those works. Future iterations will provide assistance for work creation, submissions tracking, and submissions formatting.

As a writer myself, AfA seeks to address the following qualms of mine with existing CMSes and other artist-assistance apps:

- Single source of truth

    I currently have several Word documents storing writing in submission-formatted and unformatted form. I access two separate sites to track submissions, plus two others to view literary journal rankings - not to mention literary journals themselves. Wouldnt it be nice to have all this information in one place?

- Privacy

    As a writer I am not allowed to share my works publicly if I want to have a chance at acceptance by literary journals. (The publishing world is a strange beast.) Having a CMS where writing can be shared but still be password protected so as not to be publicly searchable is vital. For example, even though Substack allows one to password-protect one's writing, those writings are still search-engine searchable which fails to satisfy the not-publicly-viewable requirement. 

- Community

    The creative life can be a lonely one. The current design of CMSes where interaction is primarily through commenting is unsatisfactory. By sharing and recommending Artist pages among users and interacting with artists themselves, AfA will allow for more-robust community building.

### Design decisions:

1. Each Artist account gets only one URL path

    Allowing an artist multiple URL paths would defeat the single source of truth component of the app.

2. Unlogged-in viewers must reauthenticate for each URL path for each browser session

    We want to make the site accessible for all while creating some friction for individuals who choose not to create user accounts.

3. URL paths are designed around artists, not users

    Not all artists are alive. We want users to be individuals who log into the site, artist or no. We want to allow the option for artists pages for individuals who are no longer with us.

4. Custom CSS settings for artist pages

    Artists can be finicky. They should have the option to customize their artist page within reason.

### v1:

The first iteration of AfA was designed using my limited perspective. If I went live tomorrow, what core functionalities do I need the site to have before I display my Artist page to friends and family?

Thus this first iteration of AfA is designed to implement core functionalities that an artist might want when displaying their work. Future iterations will create more robust guest functionalities and front-end artist interfaces for uploading work and choosing settings.

#### User experience

##### Landing page

The default landing page contains an index of all Artist pages on the platform. This landing page can be returned to using a button at the bottom of every page on the site.

##### Artist-specific URLs

Each artist-specific URL contains an About Me page and Works index.

- About Me

    The About Me page text is customizable using Markdown formatting. The basic design is to have a segment of text and an artist portrait.

- Works

    This index lists all of an artist's works in our database. Each work is accessible through a hyperlink on this page.

#### Architecture

The site is a Flask app using jinja2 templates running on top of a SQLITE database.

##### SQL database

The database has 3 central tables: 

- Users
- Subdomains
- Works

     Works are linked to a single subdomain. The subdomain table is used to store the artist's settings for his/her URL path. The works table is used to store the works the artist uploads. The users table links to the subdomains table in the case that a user has an artist page.

##### Python/Flask backend

The site runs on app.py and helpers.py.

- app.py

    The <artistpage> variable pulled from URLs is key to the dynamic functioning of the site in its current iteration. 

    Of particular note, displaywork(artistpage, worktitle) makes use of pandoc and pypandoc to dynamically format works. Works are stored in the dB as markdown and are converted using this software and wrapper into HTML upon user-access.

- helpers.py

    helpers.py contains .authReq for testing for valid URL paths, .dbOpen and .dbOpenDict for DB access, and .subdomainFails to operate the jinja2 filter for escaping characters in dynamically-created hyperlinks that may pose issues for browsers.

##### jinja2 html templating

- template.html

    This template provides basic site-wide formatting. The order of precedence for CSS formatting is AfA > Bootstrap > Artist. Therefore Artists will only be able to adjust CSS elements that do not affect core design of the site, such as text color.

- sitetemplate.html and sitedomaintemplate.html

    sitetemplate.html provides AfA homepages formatting. sitedomaintemplate.html provides formatting for artist pages.

- index.html

    index is the AfA homepage.

- apology.html

    This template is used when an invalid URL is passed to the browser.

- authenticate.html

    This template is used when an Artist page requires authentication.

- Other html templates

    The remainder of templates are accessed to dynamically generate sites within each Artist page.

##### /static

Static contains global CSS, AfA-specific CSS, global JS, and Artist page-specific CSS using the format '<artistpage>.css'

### Upcoming improvements:

#### For v2:

- Front-end Artist account creation, settings adjustments, and works upload

- Submissions formatting algorithm

- Site redesign: account options in header dropdown and urlpath options in sidebar

#### Future improvements

- Expand rendered html special char escaping

- Expanded functionalities for visual and auditory artists

- Social networking capabilities

    - User-to-user Artist page sharing/recommendation

    - User-to-Artist interaction

    - Artist page statistics

    ### Dependencies

    #### External Dependencies
    - 