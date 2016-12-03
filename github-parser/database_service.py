#!/usr/bin/python


import pymysql
import dateutil.parser
# A service class to make DB queries such as inserting new commits etc.
class DatabaseService:

    def __init__(self, mysql_config):
        # Generate a github_requester with imported GitHub tokens

        self.__db = pymysql.connect(host=mysql_config['host'], port=mysql_config['port'], db=mysql_config['db'],
                             user=mysql_config['user'], passwd=mysql_config['passwd'],
                             charset='utf8', use_unicode=True)

        self.__cursor = self.__db.cursor()

    def insertProject(self, item):
        id = item["id"]
        url = item["url"].encode('utf-8', 'ignore')
        name = item["name"].encode('utf-8', 'ignore')
        full_name = item["full_name"].encode('utf-8', 'ignore')
        html_url = item["html_url"].encode('utf-8', 'ignore')
        owner_id = item["owner"]["id"]
        description = item["description"]

        if description is not None:
            description = description.encode('utf-8', 'ignore')

        lang = item["language"]
        if lang is not None:
            lang = lang.encode('utf-8', 'ignore')

        stars = item["stargazers_count"]
        forks = item["forks"]
        watchers = item["watchers_count"]
        # TODO: Timeformat does not match, damn why?
        created_at = dateutil.parser.parse(item["created_at"])
        updated_at = dateutil.parser.parse(item["updated_at"])
        #created_at = None
        #updated_at = None
        userURL = "https://api.github.com/users/" + item["owner"]["login"]

        self.__cursor.execute("""INSERT INTO `repositories` (`id`, `url`, `owner_id`, `name`, `full_name`, `description`,
        `language`, `created_at`, `updated_at`, `stargazers_count`, `watchers_count`, `forks_count`)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE name = name""",
                       (id, url, owner_id, name, full_name, description, lang, created_at, updated_at, stars, watchers, forks,))

        self.__db.commit()

        print("Inserted project into DB:" + item["full_name"])


    def insertUser(self, userData):

        userId = userData["id"]
        userLogin = userData["login"].encode('utf-8', 'ignore')
        userName = userData["name"]
        if userName is not None:
         userName = userName.encode('utf-8', 'ignore')

        userCompany = userData["company"]
        if userCompany is not None:
         userCompany = userCompany.encode('utf-8', 'ignore')

        userEmail = userData["email"]
        if userEmail is not None:
         userEmail = userEmail.encode('utf-8', 'ignore')

        userBio = userData["bio"]
        if userBio is not None:
         userBio = userBio.encode('utf-8', 'ignore')

        userUrl = userData["url"]

        self.__cursor.execute("""INSERT INTO users(id, login,name,company,email, bio, url) VALUES (%s,%s,%s,%s,%s,%s, %s)
                 ON DUPLICATE KEY UPDATE login = login""",
                 (userId, userLogin, userName, userCompany, userEmail, userBio, userUrl))

        self.__db.commit()

    def getRepoUrls(self):
        self.__cursor.execute("SELECT url, id FROM repositories")
        self.__db.commit()

        urls = self.__cursor.fetchall()
        return urls

    def insertCommit(self, commit, project_id):
        sha = commit["sha"]
        url = commit["url"]
        author_id= commit["author"]["id"]
        committer_id = commit["committer"]["id"]
        message = commit["commit"]["message"]
        created_at = dateutil.parser.parse(commit["commit"]["author"]["date"])
        additions = commit["stats"]["additions"]
        deletions = commit["stats"]["deletions"]
        self.__cursor.execute(
            """INSERT INTO `commits` (`sha`, `url`, `project_id`, `author_id`, `committer_id`, `message`,
            `created_at`, `additions`, `deletions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE url = url """,
            (sha, url, project_id, author_id, committer_id, message, created_at, str(additions), str(deletions))
        )
        print("Commit with sha: " + sha +" added")
        self.__db.commit()
        self.insertFile(commit["files"], sha, project_id)
        return

    def insertFile(self, files, commit_sha, project_id):
        for file in files:
            sha = file["sha"]
            filename = file["filename"]
            status = file["status"]
            additions = file["additions"]
            deletions = file["deletions"]
            changes = file["changes"]
            contents_url = file["contents_url"]
            if "patch" in file:
                patch = file["patch"]
            else:
                patch = None

            self.__cursor.execute(
                """ INSERT INTO `filechanges` (`sha`, `project_id`, `commit_sha`, `filename`, `status`, `additions`, `deletions`, `changes`, `contents_url`, `patch`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE filename = filename""",
                (sha,project_id, commit_sha, filename, status, additions, deletions, changes, contents_url, patch)
            )
            self.__db.commit()

        return