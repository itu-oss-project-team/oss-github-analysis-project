#!/usr/bin/python


import pymysql
import dateutil.parser
# A service class to make DB queries such as inserting new commits etc.
class DatabaseService:

    def __init__(self, mysql_config):
        # Generate a github_requester with imported GitHub tokens

        self.__db = pymysql.connect(host=mysql_config['host'], port=mysql_config['port'], db=mysql_config['db'],
                             user=mysql_config['user'], passwd=mysql_config['passwd'],
                             charset='utf8mb4', use_unicode=True)

        self.__cursor = self.__db.cursor()

    def insertProject(self, item):
        id = item["id"]
        url = item["url"].encode('utf-8', 'ignore')
        name = item["name"].encode('utf-8', 'ignore')
        full_name = item["full_name"].encode('utf-8', 'ignore')
        html_url = item["html_url"].encode('utf-8', 'ignore')
        owner_id = self.getUserId(0, item["owner"]["login"])
        description = item["description"]

        if description is not None:
            description = description.encode('utf-8', 'ignore')

        lang = item["language"]
        if lang is not None:
            lang = lang.encode('utf-8', 'ignore')

        stars = item["stargazers_count"]
        forks = item["forks"]
        watchers = item["watchers_count"]
        created_at = dateutil.parser.parse(item["created_at"])
        updated_at = dateutil.parser.parse(item["updated_at"])

        self.__cursor.execute(""" SELECT id from repositories where id = %s """, (id))
        self.__db.commit()

        repo = self.__cursor.fetchall()
        if not repo:
            self.__cursor.execute("""INSERT INTO `repositories` (`id`, `url`, `owner_id`, `name`, `full_name`, `description`,
            `language`, `created_at`, `updated_at`, `stargazers_count`, `watchers_count`, `forks_count`)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE name = name""",
                           (id, url, owner_id, name, full_name, description, lang, created_at, updated_at, stars, watchers, forks))

            self.__db.commit()

            print("Inserted project into DB:" + item["full_name"])


    def insertGithubUser(self, githubUserData):

        userId = githubUserData["id"]
        userLogin = githubUserData["login"]
        userName = githubUserData["name"]
        userCompany = githubUserData["company"]
        userEmail = githubUserData["email"]
        userBio = githubUserData["bio"]
        userUrl = githubUserData["url"]

        self.__cursor.execute("""INSERT INTO users(github_user_id, login,name,company,email, bio, url, is_github_user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                 ON DUPLICATE KEY UPDATE login = login""",
                 (userId, userLogin, userName, userCompany, userEmail, userBio, userUrl, 1))

        self.__db.commit()

    def insertUser(self, userData):

        userName = userData["name"]
        userEmail = userData["email"]

        self.__cursor.execute("""INSERT INTO users(name,email, is_github_user) VALUES (%s,%s,%s)
                 ON DUPLICATE KEY UPDATE login = login""",
                 (userName, userEmail, 0))

        self.__db.commit()

    def getRepoUrls(self):
        self.__cursor.execute("""SELECT url, id FROM repositories ORDER BY stargazers_count DESC""")
        self.__db.commit()

        urls = self.__cursor.fetchall()
        return urls

    def insertCommit(self, commit, project_id):
        sha = commit["sha"]
        url = commit["url"]

        if commit["author"] is not None:
            author_id= self.getUserId(0, commit["author"]["login"])
        else:
            author_id = self.getUserId(1, commit["commit"]["author"]["email"])

        if commit["committer"] is not None:
            committer_id = self.getUserId(0, commit["committer"]["login"])
        else:
            committer_id = self.getUserId(1, commit["commit"]["committer"]["email"])

        message = commit["commit"]["message"]
        created_at = dateutil.parser.parse(commit["commit"]["author"]["date"])
        if commit["stats"] is not None:
            additions = commit["stats"]["additions"]
            deletions = commit["stats"]["deletions"]
        else:
            additions = None
            deletions = None

        self.__cursor.execute(
            """INSERT INTO `commits` (`sha`, `url`, `project_id`, `author_id`, `committer_id`, `message`,
            `created_at`, `additions`, `deletions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE url = url """,
            (sha, url, project_id, author_id, committer_id, message, created_at, str(additions), str(deletions))
        )
        print("Commit with sha: " + sha +" added")
        self.__db.commit()
        self.insertFiles(commit["files"], sha, project_id)

        return

    def insertFiles(self, files, commit_sha, project_id):
        for file in files:
            sha = file["sha"]
            if sha is None:
                sha = "null"
            filename = file["filename"]
            status = file["status"]
            additions = file["additions"]
            deletions = file["deletions"]
            changes = file["changes"]
            self.__cursor.execute(
                """ INSERT INTO `filechanges` (`sha`, `project_id`, `commit_sha`, `filename`, `status`, `additions`, `deletions`, `changes`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE filename = filename""",
                (sha,project_id, commit_sha, filename, status, additions, deletions, changes)
            )
            self.__db.commit()

            self.__cursor.execute(
                """ INSERT INTO `filesofproject` (`filename`, `project_id`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE project_id = project_id""", (filename, project_id))
            self.__db.commit()
        return

    def checkIfCommitExist(self, sha):
        self.__cursor.execute(""" SELECT sha from commits where sha = %s """, (sha))
        self.__db.commit()
        _commit = self.__cursor.fetchall()
        if _commit:
            return True
        else:
            return False


    def getAllRepoNames(self):
        self.__cursor.execute(""" SELECT owner_id,name from repositories""")
        self.__db.commit()
        names = self.__cursor.fetchall()
        return names

    def getOwnerLoginbyId(self,id):
        self.__cursor.execute(""" SELECT login from users where github_user_id = %s""",(id))
        self.__db.commit()
        login = self.__cursor.fetchone()
        return login

    def checkIfGithubUserExist(self, login):
        self.__cursor.execute(""" SELECT login from users where login = %s""", (login))
        self.__db.commit()
        _login = self.__cursor.fetchone()
        if _login:
            return True
        else:
            return False

    def checkIfUserExist(self, email):
        self.__cursor.execute(""" SELECT email from users where email = %s""", (email))
        self.__db.commit()
        _email = self.__cursor.fetchone()
        if _email:
            return True
        else:
            return False

    def getUserId(self, type, data):
        if type == 0: #github user
            self.__cursor.execute(""" SELECT user_id from users where login = %s""", (data))
        elif type == 1: #not github user
            self.__cursor.execute(""" SELECT user_id from users where email = %s""", (data))

        self.__db.commit()
        user_id = self.__cursor.fetchone()

        return user_id[0]

    
    def insertContribution(self,userid, repoid,contributions):
       self.__cursor.execute(""" INSERT INTO contributings (repository_id,user_id,contributions)values (%s,%s,%s)""",(repoid,userid,contributions))
       self.__db.commit()