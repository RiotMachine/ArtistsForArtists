from flask import session
from flask_login import UserMixin
from helpers import dbQuery, userInput
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin):
    def __init__(self, id, username, passhash):
        self.id = str(id)
        self.username = username
        self.passhash = passhash
        self.subdomainID = self.setupUserSubdomain()

    def getUserPrefsDict(self):
        prefsQuery = dbQuery("SELECT userPrefs.prefBool, prefs.prefString FROM userPrefs, prefs "
                        "WHERE userPrefs.userID = ? AND prefs.id = userPrefs.prefID", 
                        [self.id])
        prefsDict = {}
        for prefQuery in prefsQuery:
            prefsDict[prefQuery['prefString']] = prefQuery['prefBool']
        return prefsDict

    def getUserArtistID(self):
        return dbQuery("SELECT artists.id FROM artists, users "
                       "WHERE artists.userID = users.id and users.id = ?",
                       [self.id], jen=True) ['id']

    def modUserSettings(self, changepassBool, prefsDict):
        ### Password change
        if changepassBool:
            dbQuery("UPDATE users SET passwordhash = ? WHERE id = ?", 
                    [generate_password_hash(userInput("newpass")), self.id])

        ### Iterating over dict of prefs:values to update the db and assign values to session vars
        for key, value in prefsDict.items():
            prefID = dbQuery("SELECT id FROM prefs WHERE prefString = ?", [key], jen=True)['id']
            dbQuery("INSERT INTO userPrefs (prefBool, prefID, userID) VALUES (?, ?, ?) "
                    "ON CONFLICT (userID, prefID) DO "
                        "UPDATE SET prefBool = ? WHERE userPrefs.prefID = ? AND userPrefs.userID = ?", 
                    [value, prefID, self.id, 
                     value, prefID, self.id])
            session[key] = value

    def setupUserPrefs(self):
        prefs = self.getUserPrefsDict()
        for key, value in prefs.items():
            session[key] = value

    def setupUserSubdomain(self):
        subdomainRow = dbQuery("SELECT subdomains.id FROM artists, subdomains, users "
                           "WHERE subdomains.artistID = artists.id AND artists.userID = users.id "
                           "AND users.id = ?", 
                           [self.id], jen=True)
        if subdomainRow is None:
            return None
        else:
            return subdomainRow['id']


class Subdomain():
    def __init__(self, id):
        self.id = id
        subdomainRow = self.setupSubdomain()
        self.name = subdomainRow['pagename']
        self.authReq = int(subdomainRow['authreq'])
        self.authPassHash = subdomainRow['authpasshash']

    def setupSubdomain(self):
        return dbQuery("SELECT pagename, authreq, authpasshash FROM subdomains WHERE id = ?", 
                       [self.id], jen=True)

    def getAboutmeRow(self):
        return dbQuery("SELECT aboutme, hasphoto FROM subdomains WHERE subdomains.id = ?", 
                      [self.id], jen=True)

    def getWork(self, title):
        return dbQuery("SELECT content FROM works, subdomains "
                       "WHERE works.title = ? AND subdomains.id = ? "
                            "AND subdomains.artistID = works.artistID", 
                            [title, self.id], jen=True)

    def getWorkList(self):
        return dbQuery("SELECT title, genreString FROM works, genres, subdomains "
                       "WHERE subdomains.id = ? AND subdomains.artistID = works.artistID "
                           "AND genres.id = works.genreID ORDER BY title", [self.id])

    def getWorksTable(self):
        return dbQuery("SELECT works.id, title, genreString, substr(content, 1, 40) AS content "
                       "FROM works, genres, artists, subdomains WHERE works.genreID = genres.id "
                           "AND works.artistID = artists.id AND artists.id = subdomains.artistID "
                           "AND subdomains.id = ? ORDER BY title", 
                       [self.id])

    def verifyAuth(self):
        if self.authReq:
            if session.get(self.name):
                return check_password_hash(self.authPassHash, session[self.name])
            else:
                return False
        else:
            return True


class Work():
    def __init__(self, id):
        self.id = id

    @classmethod
    def newWork(cls, title, artistID, content, genreID):
        newWorkID = dbQuery("INSERT INTO works (title, artistID, content, genreID) VALUES (?, ?, ?, ?) "
                            "RETURNING id", [title, artistID, content, genreID])
        return cls(newWorkID)

    def modifyWork(self, text, title):
        dbQuery("UPDATE works SET content = ?, title = ? WHERE id = ?", 
                [text, title, self.id])

    def deleteWork(self):
        dbQuery("DELETE FROM works WHERE id = ?", [self.id])
        del self

    def getWorkRow(self):
        return dbQuery("SELECT content, title FROM works WHERE works.id = ?",
                       [self.id], jen=True)