from flask                      import session
from flask_login                import UserMixin
from werkzeug.security          import check_password_hash, generate_password_hash
from ArtistsForArtists.helpers  import dbQuery, userInput

class User(UserMixin):
    def __init__(self, id, username, passhash):
        self.id = str(id)
        self.username = username
        self.passhash = passhash
        subdomainRow = dbQuery("SELECT subdomains.id FROM subdomains, users "
                                "WHERE subdomains.userID = users.id AND users.id = ?",
                                [self.id], jen=True)
        if subdomainRow is None:
            self.subdomainID = None
        else:
            self.subdomainID = subdomainRow['id']

    def setupPrefs(self):
        prefs = self.getPrefsDict()
        for key, value in prefs.items():
            session[key] = value            

    def getPrefsDict(self):
        prefsQuery = dbQuery("SELECT userPrefs.prefBool, prefs.prefString FROM userPrefs, prefs "
                                "WHERE userPrefs.userID = ? AND prefs.id = userPrefs.prefID", 
                                [self.id])
        prefsDict = {}
        for prefQuery in prefsQuery:
            prefsDict[prefQuery['prefString']] = prefQuery['prefBool']
        return prefsDict

    def updatePrefs(self, prefsDict):
        ## Iterating over dict of prefs:values to update the db and assign values to session vars
        for key, value in prefsDict.items():
            prefID = dbQuery("SELECT id FROM prefs WHERE prefString = ?", [key], jen=True)['id']
            dbQuery("INSERT INTO userPrefs (prefBool, prefID, userID) VALUES (?, ?, ?) "
                        "ON CONFLICT (userID, prefID) DO "
                        "UPDATE SET prefBool = ? WHERE userPrefs.prefID = ? AND userPrefs.userID = ?", 
                    [value, prefID, self.id, 
                     value, prefID, self.id])
            session[key] = value

    def changePass(self, newpass):
        dbQuery("UPDATE users SET passwordhash = ? WHERE id = ?", 
                    [generate_password_hash(newpass), self.id])


class Subdomain():
    def __init__(self, id):
        self.id = id
        subdomainRow = dbQuery("SELECT pagename, authreq, authpasshash FROM subdomains WHERE id = ?", 
                                [self.id], jen=True)
        self.name = subdomainRow['pagename']
        self.authReq = int(subdomainRow['authreq'])
        self.authPassHash = subdomainRow['authpasshash']

    def getAboutmeRow(self):
        return dbQuery("SELECT aboutme, hasphoto FROM subdomains WHERE id = ?", 
                        [self.id], jen=True)

    def getArtistName(self):
        return dbQuery("SELECT artistname FROM subdomains WHERE subdomains.id = ?", 
                        [self.id], jen=True)['artistname']

    def getWork(self, title):
        return dbQuery("SELECT content FROM works, subdomains "
                       "WHERE works.title = ? AND subdomains.id = ? "
                        "AND subdomains.id = works.subdomainID", 
                        [title, self.id], jen=True)

    def getWorksList(self):
        return dbQuery("SELECT title, genreString FROM works, genres, subdomains "
                       "WHERE subdomains.id = ? AND subdomains.id = works.subdomainID "
                        "AND genres.id = works.genreID ORDER BY title", [self.id])

    def getWorksTable(self):
        return dbQuery("SELECT works.id, title, genreString, substr(content, 1, 40) AS content "
                       "FROM works, genres, subdomains WHERE works.genreID = genres.id "
                        "AND works.subdomainID = subdomains.id AND subdomains.id = ? ORDER BY title", 
                        [self.id])

    def verifyAuth(self):
        if self.authReq:
            if session.get(self.name):
                return check_password_hash(self.authPassHash, session[self.name])
            else:
                return False
        else:
            return True

    def changePass(self, newpass):
        dbQuery("UPDATE subdomains SET authpasshash = ? WHERE id = ?", 
                    [generate_password_hash(newpass), self.id])


class Work():
    def __init__(self, id):
        self.id = id

    @classmethod
    def newWork(cls, title, subdomainID, content, genreID):
        newWorkID = dbQuery("INSERT INTO works (title, subdomainID, content, genreID) VALUES (?, ?, ?, ?) "
                            "RETURNING id", [title, subdomainID, content, genreID])
        return cls(newWorkID)

    def modifyWork(self, text, title, genreID):
        dbQuery("UPDATE works SET content = ?, title = ?, genreID = ? WHERE id = ?", 
                [text, title, genreID, self.id])

    def deleteWork(self):
        dbQuery("DELETE FROM works WHERE id = ?", [self.id])
        del self

    def getWorkRow(self):
        return dbQuery("SELECT content, title FROM works WHERE works.id = ?",
                       [self.id], jen=True)