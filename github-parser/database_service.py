#!/usr/bin/python


import pymysql


# A service class to make DB queries such as inserting new commits etc.
class DatabaseService:

    def __init__(self, mysql_config):
        # Generate a github_requester with imported GitHub tokens

        self.__db = pymysql.connect(host=mysql_config['host'], port=mysql_config['port'], db=mysql_config['db'],
                             user=mysql_config['user'],
                             passwd=mysql_config['passwd'])

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
        #created_at = item["created_at"].encode('utf-8', 'ignore')
        #updated_at = item["updated_at"].encode('utf-8', 'ignore')
        created_at = None
        updated_at = None
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

