#!/usr/bin/python

import pymysql
import dateutil.parser
import dateutil.rrule
from db_coloumn_constants import Coloumns


# A service class to make DB queries such as inserting new commits etc.
class DatabaseService:

    def __init__(self, mysql_config):
        # Generate a github_requester with imported GitHub tokens

        self.__db = pymysql.connect(host=mysql_config['host'], port=mysql_config['port'], db=mysql_config['db'],
                             user=mysql_config['user'], passwd=mysql_config['passwd'],
                             charset='utf8mb4', use_unicode=True)

        self.__cursor = self.__db.cursor()
        self.__dictCursor = self.__db.cursor(pymysql.cursors.DictCursor)

        self.__file_sha_null_counter = 0
        self.__commit_sha_null_counter = 0

    def insertProject(self, item):
        id = item["id"]
        url = item["url"].encode('utf-8', 'ignore')
        name = item["name"].encode('utf-8', 'ignore')
        full_name = item["full_name"].encode('utf-8', 'ignore')
        html_url = item["html_url"].encode('utf-8', 'ignore')
        owner_id = self.getUserIdFromLogin(item["owner"]["login"])
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

        self.__dictCursor.execute(""" SELECT id from repositories where id = %s """, (id))
        self.__db.commit()

        repo = self.__dictCursor.fetchall()
        if not repo:
            self.__dictCursor.execute("""INSERT INTO `repositories` (`id`, `url`, `owner_id`, `name`, `full_name`, `description`,
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

        self.__dictCursor.execute("""INSERT INTO users(github_user_id, login,name,company,email, bio, url, is_github_user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                 ON DUPLICATE KEY UPDATE login = login""",
                                  (userId, userLogin, userName, userCompany, userEmail, userBio, userUrl, 1))

        self.__db.commit()

    def insertUser(self, userData):

        userName = userData["name"]
        userEmail = userData["email"]

        self.__dictCursor.execute("""INSERT INTO users(name,email, is_github_user) VALUES (%s,%s,%s)
                 ON DUPLICATE KEY UPDATE login = login""",
                                  (userName, userEmail, 0))

        self.__db.commit()

    def insertCommit(self, commit, project_id):
        sha = commit["sha"]
        if sha is None:
            sha = "null" + str(self.__commit_sha_null_counter);
            print("Project: " + str(project_id) + " commit: " + str(commit_sha) + " has null commit sha. counter: " + str(self.__commit_sha_null_counter))
            self.__commit_sha_null_counter += 1;

        url = commit["url"]

        if commit["author"] is not None:
            author_id = self.getUserIdFromLogin(commit["author"]["login"])
        else:
            author_id = self.getUserIdFromEmail(commit["commit"]["author"]["email"])

        if commit["committer"] is not None:
            committer_id = self.getUserIdFromLogin(commit["committer"]["login"])
        else:
            committer_id = self.getUserIdFromEmail(commit["commit"]["committer"]["email"])

        message = commit["commit"]["message"]
        created_at = dateutil.parser.parse(commit["commit"]["author"]["date"])
        if commit["stats"] is not None:
            additions = commit["stats"]["additions"]
            deletions = commit["stats"]["deletions"]
        else:
            additions = None
            deletions = None

        self.__dictCursor.execute(
            """INSERT INTO `commits` (`sha`, `url`, `project_id`, `author_id`, `committer_id`, `message`,
            `created_at`, `additions`, `deletions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE url = url """,
            (sha, url, project_id, author_id, committer_id, message, created_at, str(additions), str(deletions))
        )
        #print("Commit with sha: " + sha +" added")
        self.__db.commit()
        self.insertFiles(commit["files"], sha, project_id)

        return

    def insertFiles(self, files, commit_sha, project_id):
        for file in files:
            sha = file["sha"]
            if sha is None:
                sha = "null" + str(self.__file_sha_null_counter);
                print("Project: " + str(project_id) + " commit: " + str(commit_sha) + " has null file sha. counter: " + str(self.__file_sha_null_counter))
                self.__file_sha_null_counter += 1;
            filename = file["filename"]
            status = file["status"]
            additions = file["additions"]
            deletions = file["deletions"]
            changes = file["changes"]
            self.__dictCursor.execute(
                """ INSERT INTO `filechanges` (`sha`, `project_id`, `commit_sha`, `filename`, `status`, `additions`, `deletions`, `changes`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE filename = filename""",
                (sha,project_id, commit_sha, filename, status, additions, deletions, changes)
            )
            self.__db.commit()

            self.__dictCursor.execute(
                """ INSERT INTO `filesofproject` (`filename`, `project_id`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE project_id = project_id""", (filename, project_id))
            self.__db.commit()
        return

    def insertContribution(self,userid, repoid,contributions):
       self.__dictCursor.execute(""" INSERT INTO contributings (repository_id,user_id,contributions)values (%s,%s,%s)""", (repoid, userid, contributions))
       self.__db.commit()

    def checkIfCommitExist(self, sha):
        self.__dictCursor.execute(""" SELECT sha from commits where sha = %s """, (sha))
        self.__db.commit()
        _commit = self.__dictCursor.fetchall()
        if _commit:
            return True
        else:
            return False

    def checkIfRepoFilled(self, repo_id, time_since = None):
        if time_since is None:
            # No time value has been specified just check whether repo is filled before or nor
            self.__dictCursor.execute(""" SELECT `id` FROM `repositories` WHERE `id` = %s AND `filled_at` IS NOT NULL""", (repo_id))
        else:
            # A time value has been specified, check wheter repo's content is newer than given time
            date = str(dateutil.parser.parse(time_since))
            self.__dictCursor.execute(""" SELECT `id` FROM `repositories` WHERE `id` = %s AND `filled_at` > %s """, (repo_id, date))

        self.__db.commit()
        repos = self.__dictCursor.fetchone()

        if (repos is not None):
            # Repo exists or newer
            return True
        else:
            # Repo does not new enough
            return False

    '''
        Get all repos in DB
        if get_only_ids is true it will return a list of repo ids
        else it will return repos as a dict
    '''
    def getAllRepos(self, get_only_ids=False):
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM repositories""")
            self.__db.commit()
            repos = self.__cursor.fetchall()
            repos = [repo[0] for repo in repos]
        else:
            self.__dictCursor.execute(""" SELECT * FROM repositories""")
            self.__db.commit()
            repos = self.__dictCursor.fetchall()
        return repos

    def getRepoUrls(self):
        self.__dictCursor.execute("""SELECT url, id FROM repositories ORDER BY stargazers_count DESC""")
        self.__db.commit()

        urls = self.__dictCursor.fetchall()
        return urls

    '''
        Get all commits of a specified repo in DB
        if get_only_shas is true it will return a list of commits shas
        else it will return commits as a dict
    '''
    def getCommitsOfRepo(self, repo_id, get_only_shas=False):
        if get_only_shas:
            self.__cursor.execute(""" SELECT sha FROM commits WHERE project_id = %s""", repo_id)
            self.__db.commit()
            commits = self.__cursor.fetchall()
            commits = [commit[0] for commit in commits]
        else:
            self.__dictCursor.execute(""" SELECT * FROM commits WHERE project_id = %s""", repo_id)
            self.__db.commit()
            commits = self.__dict_cursor.fetchall()
        return commits

    '''
        Get all files of a specified commit in DB
        if get_only_shas is true it will return a list of file change shas
        else it will return file changes as a dict
    '''
    def getFilesChangesOfCommit(self, commit_sha, get_only_shas=False):
        if get_only_shas:
            self.__cursor.execute(""" SELECT sha FROM filechanges WHERE commit_sha = %s""", commit_sha)
            self.__db.commit()
            files = self.__cursor.fetchall()
            files = [file[0] for file in files]
        else:
            self.__dictCursor.execute(""" SELECT * FROM filechanges WHERE commit_sha = %s""", commit_sha)
            self.__db.commit()
            files = self.__dictCursor.fetchall()
        return files

    def getOwnerLoginbyId(self, id):
        self.__dictCursor.execute(""" SELECT login from users where github_user_id = %s""", (id))
        self.__db.commit()
        login = self.__dictCursor.fetchone()
        return login

    # Returns user id associated with given e-mail, for non-GitHub users
    def getUserIdFromEmail(self, email):
        self.__dictCursor.execute(""" SELECT user_id from users where email = %s""", (email))

        self.__db.commit()
        user_id = self.__dictCursor.fetchone()

        return user_id[Coloumns.User.id]

    # Returns user id associated with given GitHub login name, for GitHub users
    def getUserIdFromLogin(self, login):
        self.__dictCursor.execute(""" SELECT user_id from users where login = %s""", (login))

        self.__db.commit()
        user_id = self.__dictCursor.fetchone()

        return user_id[Coloumns.User.id]

    def checkIfGithubUserExist(self, login):
        self.__dictCursor.execute(""" SELECT login from users where login = %s""", (login))
        self.__db.commit()
        _login = self.__dictCursor.fetchone()
        if _login:
            return True
        else:
            return False

    def checkIfUserExist(self, email):
        self.__dictCursor.execute(""" SELECT email from users where email = %s""", (email))
        self.__db.commit()
        _email = self.__dictCursor.fetchone()
        if _email:
            return True
        else:
            return False

    def setRepoFilledAt(self, repo_id, filled_time):
        self.__dictCursor.execute(""" UPDATE repositories SET filled_at = %s WHERE id = %s""", (filled_time, repo_id))
        self.__db.commit()

    def findNumberOfCommitsAndContributorsOfProjectMonthly(self, project_id, start_date, end_date):
        date_list = list(dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart=start_date, until=end_date))
        for i in range(0, len(date_list)-1, 1):
            s_date = date_list[i]
            e_date = date_list[i+1]
            self.__cursor.execute(""" select count(*) from commits where project_id = %s and (created_at BETWEEN %s and %s) """,
                                  (project_id, s_date, e_date))
            self.__db.commit()
            no_of_commits = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" select count(*) from (
                select count(*), author_id from commits where project_id = %s and (created_at BETWEEN %s and %s) group by author_id
                ) contributorsCount """, (project_id, s_date, e_date))
            self.__db.commit()
            no_of_contributors = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" select count(*) from (
                select count(*), filename, changes from filechanges join commits on commit_sha = commits.sha
                where filechanges.project_id = %s and (created_at BETWEEN %s and %s) group by filename) filesCount """,
                (project_id, s_date, e_date))
            self.__db.commit()
            no_of_changed_files = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" select id from projectstats
                where project_id = %s and
                start_date = %s and
                end_date = %s """, (project_id, s_date, e_date))
            self.__db.commit()
            id = self.__cursor.fetchone()

            if id is not None:
                id = id[0]
                self.__cursor.execute(""" INSERT INTO projectstats
                    (id, project_id, start_date, end_date, no_of_commits, no_of_contributors, no_of_changed_files)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    no_of_commits = VALUES(no_of_commits), no_of_contributors = VALUES(no_of_contributors),
                    no_of_changed_files = VALUES(no_of_changed_files) """,
                    (id, project_id, s_date, e_date, no_of_commits, no_of_contributors, no_of_changed_files))
                self.__db.commit()
            else:
                self.__cursor.execute(""" INSERT INTO projectstats(project_id, start_date, end_date, no_of_commits,
                    no_of_contributors, no_of_changed_files) VALUES (%s, %s, %s, %s, %s, %s) """,
                    (project_id, s_date, e_date, no_of_commits, no_of_contributors, no_of_changed_files))
                self.__db.commit()

        return
