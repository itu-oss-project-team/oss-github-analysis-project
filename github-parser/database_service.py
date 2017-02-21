#!/usr/bin/python

import pymysql
import dateutil.parser
import dateutil.rrule
from db_coloumn_constants import Coloumns
from _datetime import datetime


# A service class to make DB queries such as inserting new commits etc.
class DatabaseService:

    def __init__(self, mysql_config):
        # Generate a github_requester with imported GitHub tokens

        self.__db = pymysql.connect(host=mysql_config['host'], port=mysql_config['port'], db=mysql_config['db'],
                             user=mysql_config['user'], passwd=mysql_config['passwd'],
                             charset='utf8mb4', use_unicode=True)

        self.__cursor = self.__db.cursor()
        self.__dictCursor = self.__db.cursor(pymysql.cursors.DictCursor)

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

    #method used for inserting Non GitHub users.
    def insertUser(self, userData):

        userName = userData["name"]
        userEmail = userData["email"]

        self.__dictCursor.execute("""INSERT INTO users(name,email, is_github_user) VALUES (%s,%s,%s)
                 ON DUPLICATE KEY UPDATE login = login""",
                                  (userName, userEmail, 0))

        self.__db.commit()

    def insertCommit(self, commit, repo_id):
        sha = commit["sha"]
        if sha is None:
            return

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

        # id=LAST_INSERT_ID(id) assures that cursor.lastrowid always returns the ID of related row
        self.__dictCursor.execute(
            """INSERT INTO `commits` (`sha`, `url`, `repo_id`, `author_id`, `committer_id`, `message`,
            `created_at`, `additions`, `deletions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id), url = url """,
            (sha, url, repo_id, author_id, committer_id, message, created_at, str(additions), str(deletions))
        )

        #print("Commit with sha: " + sha +" added")
        self.__db.commit()

        # Gather the id of last inserted row, this is my commit id
        commit_id = self.__dictCursor.lastrowid
        self.insertFiles(commit["files"], commit_id, sha, repo_id)

        return

    def insertFiles(self, files, commit_id, commit_sha, repo_id):
        for file in files:
            sha = file["sha"]

            if sha is None:
                continue

            file_path = file["filename"]
            status = file["status"]
            additions = file["additions"]
            deletions = file["deletions"]
            changes = file["changes"]

            self.__dictCursor.execute(
                """ INSERT INTO `filesofproject` (`file_path`, `repo_id`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id), repo_id = repo_id""", (file_path, repo_id))
            self.__db.commit()

            # Gather the id of last inserted row, this is my file id
            file_id = self.__dictCursor.lastrowid

            # id=LAST_INSERT_ID(id) assures that cursor.lastrowid always returns the ID of related row
            self.__dictCursor.execute(
                """ INSERT INTO `filechanges` (`sha`, `repo_id`, `commit_id`, `commit_sha`, `file_id`, `file_path`, `status`, `additions`, `deletions`, `changes`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE file_path = file_path""",
                (sha, repo_id, commit_id, commit_sha, file_id, file_path, status, additions, deletions, changes)
            )
            self.__db.commit()


        return

    def insertContribution(self,userid, repoid,contributions):
       self.__dictCursor.execute(""" INSERT INTO contributings (repo_id,user_id,contributions)values (%s,%s,%s)""", (repoid, userid, contributions))
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
            self.__cursor.execute(""" SELECT id FROM repositories ORDER BY stargazers_count DESC""")
            self.__db.commit()
            repos = self.__cursor.fetchall()
            repos = [repo[0] for repo in repos]
        else:
            self.__dictCursor.execute(""" SELECT * FROM repositories ORDER BY stargazers_count DESC""")
            self.__db.commit()
            repos = self.__dictCursor.fetchall()
        return repos

    def getRepoByFullName(self, full_name, get_only_ids=False):
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM repositories where full_name = %s""", full_name)
            self.__db.commit()
            repos = self.__cursor.fetchall()
            repos = [repo[0] for repo in repos]
        else:
            self.__dictCursor.execute(""" SELECT * FROM repositories where full_name = %s""", full_name)
            self.__db.commit()
            repos = self.__dictCursor.fetchall()
        return repos

    def getRepoUrls(self):
        self.__dictCursor.execute("""SELECT url, id, filled_at FROM repositories ORDER BY stargazers_count DESC""")
        self.__db.commit()

        urls = self.__dictCursor.fetchall()
        return urls

    '''
        Get all commits of a specified repo in DB
        if get_only_ids is true it will return a list of commits ids
        else it will return commits as a dict
    '''
    def getCommitsOfRepo(self, repo_id, get_only_ids=False):
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM commits WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            commits = self.__cursor.fetchall()
            commits = [commit[0] for commit in commits]
        else:
            self.__dictCursor.execute(""" SELECT * FROM commits WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            commits = self.__dictCursor.fetchall()
        return commits

    def getCommitIdsOfRepo(self, repo_id):
        self.__cursor.execute(""" SELECT commit_id FROM commits WHERE repo_id = %s""", repo_id)
        self.__db.commit()
        commits = self.__cursor.fetchall()
        commits = [commit[0] for commit in commits]
        return commits

    '''
        Get all files of a specified repo in DB
        if get_only_file_names is true it will return a list of full file paths
        else it will return repo files as a dict
    '''
    def getFilesOfRepo(self, repo_id, get_only_file_names=False):
        if get_only_file_names:
            self.__cursor.execute(""" SELECT file_path FROM filesofproject WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            files = self.__cursor.fetchall()
            # Take only file names from result
            files = [file[0] for file in files]
        else:
            self.__dictCursor.execute(""" SELECT * FROM filesofproject WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            files = self.__cursor.fetchall()
        return files

    '''
        Get all files of a specified commit in DB
        if get_only_ids is true it will return a list of file change ids
        else it will return file changes as a dict
    '''
    def getFilesChangesOfCommit(self, commit_id, get_only_ids=False):
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM filechanges WHERE commit_id = %s""", commit_id)
            self.__db.commit()
            files = self.__cursor.fetchall()
            files = [file[0] for file in files]
        else:
            self.__dictCursor.execute(""" SELECT * FROM filechanges WHERE commit_id = %s""", commit_id)
            self.__db.commit()
            files = self.__dictCursor.fetchall()
        return files

    def getCommitsOfFile(self, repo_id, file_name, get_only_ids=False):
        if get_only_ids:
            self.__cursor.execute("""SELECT DISTINCT commit_id FROM filechanges WHERE repo_id = %s AND file_path = %s""", (repo_id, file_name))
            self.__db.commit()
            commits = self.__cursor.fetchall()
            commits = [commit[0] for commit in commits]
        else:
            self.__dictCursor.execute("""SELECT * FROM commits WHERE commit_id IN (SELECT DISTINCT commit_id FROM filechanges WHERE repo_id = %s AND file_path = %s)""", (repo_id, file_name))
            commits = self.__dictCursor.fetchall()
        return commits


    ####Commiter_id or author_id???
    def getContributorOfCommit (self, commit_id):
            self.__dictCursor.execute(""" SELECT author_id FROM commits WHERE id = %s""", commit_id)
            self.__db.commit()
            committer_id = self.__dictCursor.fetchone()
            return committer_id

    def checkContributorStatus(self,author_id):
            self.__dictCursor.execute(""" SELECT is_github_user FROM users WHERE user_id = %s""", author_id)
            self.__db.commit()
            is_github_user = self.__dictCursor.fetchone()
            return is_github_user

    def getCommitDate (self, commit_id):
            self.__dictCursor.execute(""" SELECT created_at FROM commits WHERE id = %s""", commit_id)
            self.__db.commit()
            commit_date = self.__dictCursor.fetchone()
            return commit_date

    def getCommitAdditions (self, commit_id):
            self.__dictCursor.execute(""" SELECT additions FROM commits WHERE id = %s""", commit_id)
            self.__db.commit()
            commit_additions = self.__dictCursor.fetchone()
            return commit_additions

    def getCommitDeletions (self, commit_id):
            self.__dictCursor.execute(""" SELECT deletions FROM commits WHERE id = %s""", commit_id)
            self.__db.commit()
            commit_deletions = self.__dictCursor.fetchone()
            return commit_deletions

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

    #this method iterates monthly and finds number of commits, contributors, file changes and unique files of a repository.
    def findNumberOfCommitsAndContributorsOfProjectMonthly(self, repo_id, start_date, end_date):
        date_list = list(dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart=start_date, until=end_date))
        for i in range(0, len(date_list)-1, 1):
            s_date = date_list[i]
            e_date = date_list[i+1]
            self.__cursor.execute(""" select count(*) from commits where repo_id = %s and (created_at BETWEEN %s and %s) """,
                                  (repo_id, s_date, e_date))
            self.__db.commit()
            no_of_commits = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" select count(*) from (
                select count(*), author_id from commits where repo_id = %s and (created_at BETWEEN %s and %s) group by author_id
                ) contributorsCount """, (repo_id, s_date, e_date))
            self.__db.commit()
            no_of_contributors = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" select count(*) from (
                select count(*) from filechanges join commits on commits.id = filechanges.commit_id
                where filechanges.repo_id = %s and (created_at BETWEEN %s and %s) group by filechanges.file_path) filesCount """,
                (repo_id, s_date, e_date))
            self.__db.commit()
            no_of_changed_files = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" SELECT count(*) FROM filechanges JOIN commits ON commit_sha = commits.sha
            WHERE filechanges.repo_id = %s AND (created_at BETWEEN %s AND %s) """, (repo_id, s_date, e_date))
            no_of_file_changes = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" select id from monthly_repositorystats
                where repo_id = %s and
                start_date = %s and
                end_date = %s """, (repo_id, s_date, e_date))
            self.__db.commit()
            id = self.__cursor.fetchone()

            if id is not None:
                id = id[0]
                self.__cursor.execute(""" INSERT INTO monthly_repositorystats
                    (id, repo_id, start_date, end_date, no_of_commits, no_of_contributors, no_of_changed_files, no_of_file_changes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    no_of_commits = VALUES(no_of_commits), no_of_contributors = VALUES(no_of_contributors),
                    no_of_changed_files = VALUES(no_of_changed_files), no_of_file_changes = VALUES(no_of_file_changes) """,
                    (id, repo_id, s_date, e_date, no_of_commits, no_of_contributors, no_of_changed_files, no_of_file_changes))
                self.__db.commit()
            else:
                self.__cursor.execute(""" INSERT INTO monthly_repositorystats(repo_id, start_date, end_date, no_of_commits,
                    no_of_contributors, no_of_changed_files, no_of_file_changes) VALUES (%s, %s, %s, %s, %s, %s, %s) """,
                    (repo_id, s_date, e_date, no_of_commits, no_of_contributors, no_of_changed_files, no_of_file_changes))
                self.__db.commit()

        return

    #this method finds number of commits, developers, file changes and unique changed files of a repository.
    def findNumberOfCommitsAndContributorsOfProject(self, repo_id):
        self.__dictCursor.execute(""" select count(*) from commits where repo_id = %s""",
                                  (repo_id))
        self.__db.commit()
        no_of_commits = self.__dictCursor.fetchone()["count(*)"]

        self.__dictCursor.execute(""" select count(*) from (
                select author_id from commits where repo_id = %s group by author_id
                ) contributorsCount """, (repo_id))
        self.__db.commit()
        no_of_contributors = self.__dictCursor.fetchone()["count(*)"]

        self.__dictCursor.execute(""" SELECT count(*) FROM filesofproject WHERE  repo_id = %s """, (repo_id))
        self.__db.commit()
        no_of_changed_files = self.__dictCursor.fetchone()["count(*)"]

        self.__dictCursor.execute("""SELECT count(*) FROM filechanges WHERE repo_id = %s """, (repo_id))
        self.__db.commit()
        no_of_file_changes = self.__dictCursor.fetchone()["count(*)"]

        self.__dictCursor.execute(""" select id from repositorystats
                where repo_id = %s """, (repo_id))
        self.__db.commit()
        id = self.__dictCursor.fetchone()

        if id:
            self.__dictCursor.execute(""" INSERT INTO `repositorystats`(`id`, `repo_id`, `no_of_commits`, `no_of_contributors`,
                `no_of_changed_files`, `no_of_file_changes`) VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                no_of_commits = VALUES(no_of_commits), no_of_contributors = VALUES(no_of_contributors),
                no_of_changed_files = VALUES(no_of_changed_files), no_of_file_changes = VALUES(no_of_file_changes) """,
                (id["id"], repo_id, no_of_commits, no_of_contributors, no_of_changed_files, no_of_file_changes))
            self.__db.commit()
        else:
            self.__dictCursor.execute(""" INSERT INTO `repositorystats`(`repo_id`, `no_of_commits`, `no_of_contributors`,
                `no_of_changed_files`, `no_of_file_changes`) VALUES (%s,%s,%s,%s,%s) """,
                (repo_id, no_of_commits, no_of_contributors, no_of_changed_files, no_of_file_changes))
            self.__db.commit()

        return

    #this method finds number of commits, first-last commit dates, number of developers and top developer id in a file.
    def findNumberOfCommitsAndDevelopersOfRepositoryFiles(self, repo_id):
        self.__dictCursor.execute(""" SELECT full_name, file_path, filesofproject.id as file_id FROM filesofproject
            left join repositories on filesofproject.repo_id = repositories.id where repo_id = %s""", repo_id)

        fileList = self.__dictCursor.fetchall()

        for fileDetails in fileList:
            file_id = fileDetails["file_id"]
            self.__dictCursor.execute(""" SELECT created_at FROM filechanges
                join commits on commits.sha = filechanges.commit_sha
                where filechanges.repo_id = %s and file_id = %s
                order by created_at ASC """, (repo_id, file_id))
            self.__db.commit()

            commit_based_result = self.__dictCursor.fetchall()
            if not commit_based_result:
                continue

            no_of_commits = len(commit_based_result)
            first_commit_date = commit_based_result[0]["created_at"]
            last_commit_date = commit_based_result[no_of_commits-1]["created_at"]

            total_time_between_two_commits = 0
            #calculate commit frequency: total time difference between two commits / total number of commits
            for i in range(1, no_of_commits):
                time_difference = commit_based_result[i]["created_at"] - commit_based_result[i-1]["created_at"]
                #print("Time diff: " ,time_difference, time_difference.days + time_difference.seconds /86400)
                total_time_between_two_commits += time_difference.days + time_difference.seconds / 86400 #86400 seconds=1 day

            commit_freq = total_time_between_two_commits / no_of_commits

            self.__dictCursor.execute(""" SELECT count(*), author_id FROM filechanges
                join commits on commits.sha = filechanges.commit_sha
                where filechanges.repo_id = %s and file_id = %s
                group by author_id order by count(*) DESC""", (repo_id, file_id))
            self.__db.commit()

            developer_based_result = self.__dictCursor.fetchall()
            top_developer_id = developer_based_result[0]["author_id"]
            no_of_developers = len(developer_based_result)

            self.__dictCursor.execute(""" SELECT id from filestats
                WHERE project_full_name = %s and file_id = %s """, (fileDetails["full_name"], file_id))
            self.__db.commit()
            id = self.__dictCursor.fetchone()

            if id:
                self.__dictCursor.execute(""" INSERT INTO
                    filestats(id, repo_id, project_full_name, file_path, no_of_commits, first_commit_date, last_commit_date,
                    commit_frequency, no_of_developers, top_developer_id, file_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    no_of_commits = VALUES(no_of_commits), first_commit_date = VALUES(first_commit_date),
                    last_commit_date = VALUES(last_commit_date), commit_frequency = VALUES(commit_frequency),
                    no_of_developers = VALUES(no_of_developers), top_developer_id = VALUES(top_developer_id) """,
                    (id["id"], repo_id, fileDetails["full_name"], fileDetails["file_path"], no_of_commits, first_commit_date, last_commit_date,
                     commit_freq, no_of_developers, top_developer_id, file_id))
                self.__db.commit()
            else:
                self.__dictCursor.execute(""" INSERT INTO
                    filestats(repo_id, project_full_name, file_path, no_of_commits, first_commit_date, last_commit_date,
                    commit_frequency, no_of_developers, top_developer_id, file_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """,
                    (repo_id, fileDetails["full_name"], fileDetails["file_path"], no_of_commits, first_commit_date, last_commit_date,
                     commit_freq, no_of_developers, top_developer_id, file_id))
                self.__db.commit()
        return
