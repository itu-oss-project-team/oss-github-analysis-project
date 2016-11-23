#!/usr/bin/python

import requests
from requester import GitHubRequester
from pprint import pprint
import pymysql

db = pymysql.connect(host='localhost', port=3306, db='test3', user='root', passwd='')
cursor = db.cursor()

# End point for harvesting GitHub API
class GitHubHarvester:
    def __init__(self, tokens):
        # Generate a github_requester with imported GitHub tokens
        self.__requester = GitHubRequester(tokens)

    def initDB(self):
        cursor.execute("""
        CREATE DATABASE IF NOT EXISTS `test4` DEFAULT CHARACTER SET utf8 COLLATE utf8_turkish_ci;
        USE `test4`;

        -- tables

        -- Table: commits
        CREATE TABLE IF NOT EXISTS commits (
            id int(11) NOT NULL,
            sha varchar(40) NULL DEFAULT NULL,
            author_id int(11) NOT NULL,
            committer_id int(11) NOT NULL,
            project_id int(11) NULL DEFAULT NULL,
            created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            message text NULL,
            url varchar(255) NOT NULL,
            UNIQUE INDEX sha (sha),
            CONSTRAINT commits_pk PRIMARY KEY (id)
        ) ENGINE InnoDB;

        CREATE INDEX IF NOT EXISTS committer_id ON commits (committer_id);

        CREATE INDEX IF NOT EXISTS project_id ON commits (project_id);

        CREATE INDEX IF NOT EXISTS author_id ON commits (author_id);

        -- Table: issues
        CREATE TABLE IF NOT EXISTS issues (
            id int(11) NOT NULL,
            repo_id int(11) NULL DEFAULT NULL,
            reporter_id int(11) NULL DEFAULT NULL,
            assignee_id int(11) NULL DEFAULT NULL,
            pull_request tinyint(1) NOT NULL,
            pull_request_id int(11) NULL DEFAULT NULL,
            created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            issue_id int(11) NOT NULL,
            CONSTRAINT issues_pk PRIMARY KEY (id)
        ) ENGINE InnoDB;

        CREATE INDEX IF NOT EXISTS repo_id ON issues (repo_id);

        CREATE INDEX IF NOT EXISTS reporter_id ON issues (reporter_id);

        CREATE INDEX IF NOT EXISTS assignee_id ON issues (assignee_id);

        CREATE INDEX IF NOT EXISTS issue_id ON issues (issue_id);

        -- Table: repositories
        CREATE TABLE IF NOT EXISTS repositories (
            id int(11) NOT NULL,
            url varchar(255) NULL,
            owner_id int(11) NOT NULL,
            name varchar(255) NOT NULL,
            full_name varchar(255) NOT NULL,
            description varchar(255) NULL DEFAULT NULL,
            language varchar(255) NULL DEFAULT NULL,
            created_at timestamp NULL,
            updated_at timestamp NULL,
            stargazers_count int NOT NULL,
            watchers_count int NOT NULL,
            forks_count int NOT NULL,
            html_url varchar(255) NULL,
            UNIQUE INDEX name (name,owner_id),
            CONSTRAINT projects_pk PRIMARY KEY (id)
        ) ENGINE InnoDB;

        CREATE INDEX IF NOT EXISTS owner_id ON repositories (owner_id);

        -- Table: users
        CREATE TABLE IF NOT EXISTS users (
            id int(11) NOT NULL,
            login varchar(255) NOT NULL,
            name varchar(255) NULL,
            email varchar(255) NULL,
            company varchar(255) NULL,
            bio text NULL,
            url varchar(255) NOT NULL,
            CONSTRAINT id PRIMARY KEY (id)
        );

        -- foreign keys

        -- Reference: fk_repositories_owner_id (table: users)
        ALTER TABLE repositories ADD CONSTRAINT fk_repositories_owner_id FOREIGN KEY fk_repositories_owner_id (owner_id)
            REFERENCES users (id);

        -- Reference: fk_commits_authors (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_authors FOREIGN KEY fk_commits_authors (committer_id)
            REFERENCES users (id);

        -- Reference: fk_commits_committers (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_committers FOREIGN KEY fk_commits_committers (author_id)
            REFERENCES users (id);

        -- Reference: fk_commits_repositories (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_repositories FOREIGN KEY fk_commits_repositories (project_id)
            REFERENCES repositories (id);

        -- Reference: fk_issues_repositories (table: issues)
        ALTER TABLE issues ADD CONSTRAINT fk_issues_repositories FOREIGN KEY fk_issues_repositories (repo_id)
            REFERENCES repositories (id);
        """)

        db.commit()
        return

    def retrieveProjects(self):
        requestURL = "https://api.github.com/search/repositories?q=stars:>5000&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)

        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            indexStart = res.links["last"]["url"].find("page=")
            indexEnd = res.links["last"]["url"].find("&per_page")
            last = res.links["last"]["url"][indexStart+5:indexEnd]

            for i in range(1, int(last)+1):
                print(i)
                requestURL = "https://api.github.com/search/repositories?q=stars:>5000&page=" + str(i) + "&per_page=100"
                res = self.__requester.makeRequest(requestURL)
                returnJson = res.json()

                for item in returnJson["items"]:
                    _id=item["id"]
                    url=item["url"].encode('utf-8', 'ignore')
                    name=item["name"].encode('utf-8', 'ignore')
                    fname=item["full_name"].encode('utf-8', 'ignore')
                    html_url=item["html_url"].encode('utf-8', 'ignore')
                    owner_id=item["owner"]["id"]
                    desc=item["description"]
                    if desc is not None:
                        desc = desc.encode('utf-8', 'ignore')

                    lang=item["language"]
                    if lang is not None:
                        lang = lang.encode('utf-8', 'ignore')
                    else:
                        continue

                    stars=item["stargazers_count"]
                    forks=item["forks"]
                    watchers=item["watchers_count"]
                    created_at=item["created_at"].encode('utf-8', 'ignore')
                    updated_at=item["updated_at"].encode('utf-8', 'ignore')
                    userURL = "https://api.github.com/users/" + item["owner"]["login"]

                    self.retrieveUserInfo(userURL)

                    cursor.execute("""INSERT INTO `repositories` (`id`, `url`, `owner_id`, `name`, `full_name`, `description`,
                    `language`, `created_at`, `updated_at`, `stargazers_count`, `watchers_count`, `forks_count`, `html_url` )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE name = name""",
                    (_id,url,owner_id,name,fname,desc,lang,created_at,updated_at,stars,watchers,forks,html_url))

                    db.commit()
                    print(fname)


        else:
            # TODO Definetly I entercoured with an error from API, what should I do now?
            print('Hatasiz kul olmaz, hatamla sev beni')

        return

    def retrieveUserInfo(self, userURL):
        res = self.__requester.makeRequest(userURL)
        userData = res.json()

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

        cursor.execute("""INSERT INTO users(id, login,name,company,email, bio, url) VALUES (%s,%s,%s,%s,%s,%s, %s)
                    ON DUPLICATE KEY UPDATE login = login""",
                    (userId, userLogin, userName, userCompany, userEmail, userBio, userUrl))

        db.commit()
        return
