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
       # created_at = item["created_at"].encode('utf-8', 'ignore')
        #updated_at = item["updated_at"].encode('utf-8', 'ignore')
        created_at = None
        updated_at = None
        userURL = "https://api.github.com/users/" + item["owner"]["login"]


        self.__cursor.execute("""INSERT INTO `repositories` (`id`, `url`, `owner_id`, `name`, `full_name`, `description`,
        `language`, `created_at`, `updated_at`, `stargazers_count`, `watchers_count`, `forks_count`, `html_url` )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE name = name""",
                       (id, url, owner_id, name, full_name, description, lang, created_at, updated_at, stars, watchers, forks,
                        html_url))

        self.__db.commit()

        print("Inserted project into DB:" + full_name)


