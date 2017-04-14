#!/usr/bin/python

import dateutil.parser
import dateutil.rrule
import pymysql

from .db_column_constants import Columns
from github_analysis_tool import secret_config

class DatabaseService:
    """
    A service class to make DB queries such as inserting new commits etc.
    """

    def __init__(self):
        mysql_config = secret_config['mysql']

        self.__db = pymysql.connect(host=mysql_config['host'], port=mysql_config['port'], db=mysql_config['db'],
                                    user=mysql_config['user'], passwd=mysql_config['passwd'], charset='utf8mb4',
                                    use_unicode=True)

        self.__cursor = self.__db.cursor()
        self.__dict_cursor = self.__db.cursor(pymysql.cursors.DictCursor)

    # Insertion functions

    def insert_repo(self, item):
        repo_id = item["id"]
        url = item["url"].encode('utf-8', 'ignore')
        name = item["name"].encode('utf-8', 'ignore')
        full_name = item["full_name"].encode('utf-8', 'ignore')
        html_url = item["html_url"].encode('utf-8', 'ignore')
        owner_id = self.get_user_id_from_login(item["owner"]["login"])
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

        self.__dict_cursor.execute(""" SELECT id FROM repositories WHERE id = %s """, repo_id)
        self.__db.commit()

        repo = self.__dict_cursor.fetchall()
        if not repo:
            self.__dict_cursor.execute("""INSERT INTO `repositories` (`id`, `url`, `owner_id`, `name`, `full_name`, `description`,
            `language`, `created_at`, `updated_at`, `stargazers_count`, `watchers_count`, `forks_count`)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE name = name""",
                                       (repo_id, url, owner_id, name, full_name, description, lang, created_at,
                                        updated_at,
                                        stars, watchers, forks))

            self.__db.commit()

            print("Inserted project into DB:" + item["full_name"])

    def insert_github_user(self, github_user_data):

        user_id = github_user_data["id"]
        user_login = github_user_data["login"]
        user_name = github_user_data["name"]
        user_company = github_user_data["company"]
        user_email = github_user_data["email"]
        user_bio = github_user_data["bio"]
        user_url = github_user_data["url"]

        self.__dict_cursor.execute("""INSERT INTO users(github_user_id, login,name,company,email, bio, url, is_github_user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                 ON DUPLICATE KEY UPDATE login = login""",
                                   (user_id, user_login, user_name, user_company, user_email, user_bio, user_url, 1))

        self.__db.commit()

    def insert_non_github_user(self, user_data):
        """
        This method used to insert non-GitHub users
        :param user_data: User data retrieved from GitHub API
        :return:  None
        """

        user_name = user_data["name"]
        user_email = user_data["email"]

        self.__dict_cursor.execute("""INSERT INTO users(name,email, is_github_user) VALUES (%s,%s,%s)
                 ON DUPLICATE KEY UPDATE login = login""",
                                   (user_name, user_email, False))

        self.__db.commit()

    def insert_commit(self, commit, repo_id):
        sha = commit["sha"]
        if sha is None:
            return

        url = commit["url"]

        if commit["author"] is not None:
            author_id = self.get_user_id_from_login(commit["author"]["login"])
        else:
            author_id = self.get_user_id_from_email(commit["commit"]["author"]["email"])

        if commit["committer"] is not None:
            committer_id = self.get_user_id_from_login(commit["committer"]["login"])
        else:
            committer_id = self.get_user_id_from_email(commit["commit"]["committer"]["email"])

        message = commit["commit"]["message"]
        created_at = dateutil.parser.parse(commit["commit"]["author"]["date"])

        additions = None
        deletions = None

        if "stats" in commit:
            if commit["stats"] is not None:
                additions = commit["stats"]["additions"]
                deletions = commit["stats"]["deletions"]

        # id=LAST_INSERT_ID(id) assures that cursor.lastrowid always returns the ID of related row
        self.__dict_cursor.execute(
            """INSERT INTO `commits` (`sha`, `url`, `repo_id`, `author_id`, `committer_id`, `message`,
            `created_at`, `additions`, `deletions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id), url = url """,
            (sha, url, repo_id, author_id, committer_id, message, created_at, str(additions), str(deletions))
        )

        # print("Commit with sha: " + sha +" added")
        self.__db.commit()

        # Gather the id of last inserted row, this is my commit id
        commit_id = self.__dict_cursor.lastrowid
        self.insert_files(commit["files"], commit_id, sha, repo_id)

        return

    def insert_files(self, files, commit_id, commit_sha, repo_id):
        for file in files:
            sha = file["sha"]

            if sha is None:
                continue

            file_path = file["filename"]
            status = file["status"]
            additions = file["additions"]
            deletions = file["deletions"]
            changes = file["changes"]

            self.__dict_cursor.execute(
                """ INSERT INTO `filesofproject` (`file_path`, `repo_id`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id), repo_id = repo_id""",
                (file_path, repo_id))
            self.__db.commit()

            # Gather the id of last inserted row, this is my file id
            file_id = self.__dict_cursor.lastrowid

            # id=LAST_INSERT_ID(id) assures that cursor.lastrowid always returns the ID of related row
            self.__dict_cursor.execute(
                """ INSERT INTO `filechanges` (`sha`, `repo_id`, `commit_id`, `commit_sha`, `file_id`, `file_path`, `status`, `additions`, `deletions`, `changes`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE file_path = file_path""",
                (sha, repo_id, commit_id, commit_sha, file_id, file_path, status, additions, deletions, changes)
            )
            self.__db.commit()

        return

    def insert_contribution(self, userid, repoid, contributions):
        self.__dict_cursor.execute(""" INSERT INTO contributings (repo_id,user_id,contributions)VALUES (%s,%s,%s)""",
                                   (repoid, userid, contributions))
        self.__db.commit()

    def insert_issue(self, id, url, number, title, repo_id, reporter_id, assignee_id, state, comments, created_at,
                     updated_at, closed_at,closedbyid):
        self.__dict_cursor.execute("""INSERT INTO issues (id,url,number,title,repo_id,reporter_id, assignee_id, state, comments, created_at, updated_at, closed_at,closedbyid)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """, (id, url, number, title, repo_id, reporter_id,
                                                                   assignee_id, state, comments, created_at, updated_at,
                                                                   closed_at,closedbyid))
        self.__db.commit()

    # Check functions
    
    def check_if_commit_exists(self, sha):
        self.__dict_cursor.execute(""" SELECT sha FROM commits WHERE sha = %s """, sha)
        self.__db.commit()
        _commit = self.__dict_cursor.fetchall()
        if _commit:
            return True
        else:
            return False

    def check_if_repo_filled(self, repo_id, time_since=None):
        if time_since is None:
            # No time value has been specified just check whether repo is filled before or nor
            self.__dict_cursor.execute(
                """ SELECT `id` FROM `repositories` WHERE `id` = %s AND `filled_at` IS NOT NULL""", repo_id)
        else:
            # A time value has been specified, check wheter repo's content is newer than given time
            date = str(dateutil.parser.parse(time_since))
            self.__dict_cursor.execute(""" SELECT `id` FROM `repositories` WHERE `id` = %s AND `filled_at` > %s """,
                                       (repo_id, date))

        self.__db.commit()
        repos = self.__dict_cursor.fetchone()

        if repos is not None:
            # Repo exists or newer
            return True
        else:
            # Repo does not new enough
            return False

    def check_if_github_user_exists(self, login):
        self.__dict_cursor.execute(""" SELECT login FROM users WHERE login = %s""", login)
        self.__db.commit()
        _login = self.__dict_cursor.fetchone()
        if _login:
            return True
        else:
            return False

    def check_if_user_exists(self, email):
        self.__dict_cursor.execute(""" SELECT email FROM users WHERE email = %s""", email)
        self.__db.commit()
        _email = self.__dict_cursor.fetchone()
        if _email:
            return True
        else:
            return False

    # Get functions
    
    def get_all_repos(self, get_only_ids=False):
        """
        Get all repos in DB
        :param get_only_ids: If true list of IDs will be returned, otherwise list of dicts
        :return: List of repos / IDs 
        """
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM repositories ORDER BY stargazers_count DESC""")
            self.__db.commit()
            repos = self.__cursor.fetchall()
            repos = [repo[0] for repo in repos]
        else:
            self.__dict_cursor.execute(""" SELECT * FROM repositories ORDER BY stargazers_count DESC""")
            self.__db.commit()
            repos = self.__dict_cursor.fetchall()
        return repos

    def get_repo_by_full_name(self, full_name, get_only_ids=False):
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM repositories WHERE full_name = %s""", full_name)
            self.__db.commit()
            repo = self.__cursor.fetchone()
        else:
            self.__dict_cursor.execute(""" SELECT * FROM repositories WHERE full_name = %s""", full_name)
            self.__db.commit()
            repo = self.__dict_cursor.fetchone()
        return repo

    def get_repo_urls(self):
        self.__dict_cursor.execute("""SELECT url, id, filled_at FROM repositories ORDER BY stargazers_count DESC""")
        self.__db.commit()

        urls = self.__dict_cursor.fetchall()
        return urls

    def get_commits_of_repo(self, repo_id, get_only_ids=False):
        """
        Get all commits of a repo in DB
        :param repo_id: ID of repo
        :param get_only_ids: If true list of IDs will be returned, otherwise list of dicts
        :return: List of commits / IDs
        """
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM commits WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            commits = self.__cursor.fetchall()
            commits = [commit[0] for commit in commits]
        else:
            self.__dict_cursor.execute(""" SELECT * FROM commits WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            commits = self.__dict_cursor.fetchall()
        return commits

    def get_files_of_repo(self, repo_id, get_only_file_paths=False):
        """
        Get all files of a repo in DB
        :param repo_id: ID of repo
        :param get_only_file_paths: If true list of file paths will be returned, otherwise list of dicts
        :return: List of files / file paths
        """
        if get_only_file_paths:
            self.__cursor.execute(""" SELECT file_path FROM filesofproject WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            files = self.__cursor.fetchall()
            # Take only file names from result
            files = [file[0] for file in files]
        else:
            self.__dict_cursor.execute(""" SELECT * FROM filesofproject WHERE repo_id = %s""", repo_id)
            self.__db.commit()
            files = self.__cursor.fetchall()
        return files

    def get_files_changes_of_commit(self, commit_id, get_only_ids=False):
        """
        Get all file changes associated with given commit in DB
        :param commit_id: ID of commit
        :param get_only_ids: If true list of file change IDs will be returned, otherwise list of dicts
        :return: List of file changes / IDs
        """
        if get_only_ids:
            self.__cursor.execute(""" SELECT id FROM filechanges WHERE commit_id = %s""", commit_id)
            self.__db.commit()
            files = self.__cursor.fetchall()
            files = [file[0] for file in files]
        else:
            self.__dict_cursor.execute(""" SELECT * FROM filechanges WHERE commit_id = %s""", commit_id)
            self.__db.commit()
            files = self.__dict_cursor.fetchall()
        return files
    
    def get_files_of_files_changes_of_commit(self, commit_id, get_only_ids=False):
        self.__dict_cursor.execute(""" SELECT file_id FROM filechanges WHERE commit_id = %s""", commit_id)
        self.__db.commit()
        fileids = self.__dict_cursor.fetchall()
        return fileids

    def get_commits_of_file(self, repo_id, file_name, get_only_ids=False):
        if get_only_ids:
            self.__cursor.execute("""SELECT DISTINCT commit_id FROM filechanges
                                    WHERE repo_id = %s AND file_path = %s""", (repo_id, file_name))
            self.__db.commit()
            commits = self.__cursor.fetchall()
            commits = [commit[0] for commit in commits]
        else:
            self.__dict_cursor.execute("""SELECT * FROM commits
                                    WHERE commit_id IN
                                    (SELECT DISTINCT commit_id FROM filechanges WHERE repo_id = %s AND file_path = %s)""",
                                       (repo_id, file_name))
            commits = self.__dict_cursor.fetchall()
        return commits

    # Commiter_id or author_id???
    def get_contributor_of_commit(self, commit_id):
        self.__dict_cursor.execute(""" SELECT author_id FROM commits WHERE id = %s""", commit_id)
        self.__db.commit()
        committer_id = self.__dict_cursor.fetchone()
        return committer_id

    def check_contributor_status(self, author_id):
        self.__dict_cursor.execute(""" SELECT is_github_user FROM users WHERE user_id = %s""", author_id)
        self.__db.commit()
        is_github_user = self.__dict_cursor.fetchone()
        return is_github_user

    def get_commit_date(self, commit_id):
        self.__dict_cursor.execute(""" SELECT created_at FROM commits WHERE id = %s""", commit_id)
        self.__db.commit()
        commit_date = self.__dict_cursor.fetchone()
        return commit_date

    def get_commit_additions(self, commit_id):
        self.__dict_cursor.execute(""" SELECT additions FROM commits WHERE id = %s""", commit_id)
        self.__db.commit()
        commit_additions = self.__dict_cursor.fetchone()
        return commit_additions

    def get_commit_deletions(self, commit_id):
        self.__dict_cursor.execute(""" SELECT deletions FROM commits WHERE id = %s""", commit_id)
        self.__db.commit()
        commit_deletions = self.__dict_cursor.fetchone()
        return commit_deletions

    def get_owner_loginby_id(self, id):
        self.__dict_cursor.execute(""" SELECT login FROM users WHERE github_user_id = %s""", id)
        self.__db.commit()
        login = self.__dict_cursor.fetchone()
        return login

    # Returns user id associated with given e-mail, for non-GitHub users
    def get_user_id_from_email(self, email):
        self.__dict_cursor.execute(""" SELECT user_id FROM users WHERE email = %s""", email)

        self.__db.commit()
        user_id = self.__dict_cursor.fetchone()

        return user_id[Columns.User.id]

    # Returns user id associated with given GitHub login name, for GitHub users
    def get_user_id_from_login(self, login):
        self.__dict_cursor.execute(""" SELECT user_id FROM users WHERE login = %s""", login)

        self.__db.commit()
        user_id = self.__dict_cursor.fetchone()

        return user_id[Columns.User.id]

    # this method returns programming language of the repo
    def get_language_by_repo_full_name(self, full_name):
        self.__dict_cursor.execute("""SELECT language FROM repositories WHERE full_name = %s""", full_name)
        self.__db.commit()

        result = self.__dict_cursor.fetchone()
        return result["language"]
    
    def check_if_issue_exists(self, issueid):
        self.__dict_cursor.execute("""SELECT * FROM issues WHERE id = %s """,issueid)
        self.__db.commit()
        return self.__dict_cursor.fetchone()
    # Set functions

    def set_repo_filled_at(self, repo_id, filled_time):
        self.__dict_cursor.execute(""" UPDATE repositories SET filled_at = %s WHERE id = %s""",
                                   (filled_time, repo_id))
        self.__db.commit()

    # Statistic functions

    # Iterates monthly and finds number of commits, contributors, file changes and unique files of a repository
    def find_number_of_commits_and_contributors_of_repo_monthly(self, repo_id, start_date, end_date):
        date_list = list(dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart=start_date, until=end_date))
        for i in range(0, len(date_list) - 1, 1):
            s_date = date_list[i]
            e_date = date_list[i + 1]
            self.__cursor.execute(""" SELECT count(*) FROM commits WHERE repo_id = %s AND
                                (created_at BETWEEN %s AND %s) """,
                                  (repo_id, s_date, e_date))
            self.__db.commit()
            no_of_commits = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" SELECT count(*) FROM (
                SELECT count(*), author_id FROM commits WHERE repo_id = %s AND
                (created_at BETWEEN %s AND %s) GROUP BY author_id
                ) contributors_count """, (repo_id, s_date, e_date))
            self.__db.commit()
            no_of_contributors = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" SELECT count(*) FROM (
                SELECT count(*) FROM filechanges JOIN commits ON commits.id = filechanges.commit_id
                WHERE filechanges.repo_id = %s AND
                (created_at BETWEEN %s AND %s) GROUP BY filechanges.file_path) files_count """,
                                  (repo_id, s_date, e_date))
            self.__db.commit()
            no_of_changed_files = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" SELECT count(*) FROM filechanges JOIN commits ON commit_sha = commits.sha
            WHERE filechanges.repo_id = %s AND (created_at BETWEEN %s AND %s) """, (repo_id, s_date, e_date))
            no_of_file_changes = self.__cursor.fetchone()[0]

            self.__cursor.execute(""" SELECT id FROM monthly_repositorystats
                WHERE repo_id = %s AND
                start_date = %s AND
                end_date = %s """, (repo_id, s_date, e_date))
            self.__db.commit()
            id = self.__cursor.fetchone()

            if id is not None:
                id = id[0]
                self.__cursor.execute(""" INSERT INTO monthly_repositorystats
                    (id, repo_id, start_date, end_date, no_of_commits, no_of_contributors,
                    no_of_changed_files, no_of_file_changes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    no_of_commits = VALUES(no_of_commits), no_of_contributors = VALUES(no_of_contributors),
                    no_of_changed_files = VALUES(no_of_changed_files), no_of_file_changes = VALUES(no_of_file_changes) """,
                                      (id, repo_id, s_date, e_date, no_of_commits, no_of_contributors,
                                       no_of_changed_files, no_of_file_changes))
                self.__db.commit()
            else:
                self.__cursor.execute(""" INSERT INTO monthly_repositorystats(repo_id, start_date, end_date, no_of_commits,
                    no_of_contributors, no_of_changed_files, no_of_file_changes) VALUES (%s, %s, %s, %s, %s, %s, %s) """,
                                      (repo_id, s_date, e_date, no_of_commits, no_of_contributors,
                                       no_of_changed_files, no_of_file_changes))
                self.__db.commit()

        return

    # this method finds number of commits, developers, file changes and unique changed files of a repository.
    def find_number_of_commits_and_contributors_of_repo(self, repo_id):
        self.__dict_cursor.execute(""" SELECT count(*) FROM commits WHERE repo_id = %s""",
                                   repo_id)
        self.__db.commit()
        no_of_commits = self.__dict_cursor.fetchone()["count(*)"]

        self.__dict_cursor.execute(""" SELECT count(*) FROM (
                SELECT author_id FROM commits WHERE repo_id = %s GROUP BY author_id
                ) contributors_count """, repo_id)
        self.__db.commit()
        no_of_contributors = self.__dict_cursor.fetchone()["count(*)"]

        self.__dict_cursor.execute(""" SELECT count(*) FROM filesofproject WHERE  repo_id = %s """, repo_id)
        self.__db.commit()
        no_of_changed_files = self.__dict_cursor.fetchone()["count(*)"]

        self.__dict_cursor.execute("""SELECT count(*) FROM filechanges WHERE repo_id = %s """, repo_id)
        self.__db.commit()
        no_of_file_changes = self.__dict_cursor.fetchone()["count(*)"]

        self.__dict_cursor.execute(""" SELECT id FROM repositorystats
                WHERE repo_id = %s """, repo_id)
        self.__db.commit()
        id = self.__dict_cursor.fetchone()

        if id:
            self.__dict_cursor.execute(""" INSERT INTO `repositorystats`(`id`, `repo_id`, `no_of_commits`, `no_of_contributors`,
                `no_of_changed_files`, `no_of_file_changes`) VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                no_of_commits = VALUES(no_of_commits), no_of_contributors = VALUES(no_of_contributors),
                no_of_changed_files = VALUES(no_of_changed_files), no_of_file_changes = VALUES(no_of_file_changes) """,
                                       (id["id"], repo_id, no_of_commits, no_of_contributors, no_of_changed_files,
                                        no_of_file_changes))
            self.__db.commit()
        else:
            self.__dict_cursor.execute(""" INSERT INTO `repositorystats`(`repo_id`, `no_of_commits`, `no_of_contributors`,
                `no_of_changed_files`, `no_of_file_changes`) VALUES (%s,%s,%s,%s,%s) """,
                                       (repo_id, no_of_commits, no_of_contributors, no_of_changed_files,
                                        no_of_file_changes))
            self.__db.commit()

        return

    # this method finds number of commits, first-last commit dates, number of developers and top developer id in a file.
    def find_number_of_commits_and_developers_of_repository_files(self, repo_id):
        self.__dict_cursor.execute(""" SELECT full_name, file_path, filesofproject.id AS file_id FROM filesofproject
            LEFT JOIN repositories ON filesofproject.repo_id = repositories.id WHERE repo_id = %s""", repo_id)

        file_list = self.__dict_cursor.fetchall()

        for file_details in file_list:
            file_id = file_details["file_id"]
            self.__dict_cursor.execute(""" SELECT created_at FROM filechanges
                JOIN commits ON commits.sha = filechanges.commit_sha
                WHERE filechanges.repo_id = %s AND file_id = %s
                ORDER BY created_at ASC """, (repo_id, file_id))
            self.__db.commit()

            commit_based_result = self.__dict_cursor.fetchall()
            if not commit_based_result:
                continue

            no_of_commits = len(commit_based_result)
            first_commit_date = commit_based_result[0]["created_at"]
            last_commit_date = commit_based_result[no_of_commits - 1]["created_at"]

            total_time_between_two_commits = 0
            # calculate commit frequency: total time difference between two commits / total number of commits
            for i in range(1, no_of_commits):
                time_difference = commit_based_result[i]["created_at"] - commit_based_result[i - 1]["created_at"]
                # print("Time diff: " ,time_difference, time_difference.days + time_difference.seconds /86400)
                total_time_between_two_commits += time_difference.days + time_difference.seconds / 86400  # 86400 seconds=1 day

            commit_freq = total_time_between_two_commits / no_of_commits

            self.__dict_cursor.execute(""" SELECT count(*), author_id FROM filechanges
                JOIN commits ON commits.sha = filechanges.commit_sha
                WHERE filechanges.repo_id = %s AND file_id = %s
                GROUP BY author_id ORDER BY count(*) DESC""", (repo_id, file_id))
            self.__db.commit()

            developer_based_result = self.__dict_cursor.fetchall()
            top_developer_id = developer_based_result[0]["author_id"]
            no_of_developers = len(developer_based_result)

            self.__dict_cursor.execute(""" SELECT id FROM filestats
                WHERE project_full_name = %s AND file_id = %s """, (file_details["full_name"], file_id))
            self.__db.commit()
            id = self.__dict_cursor.fetchone()

            if id:
                self.__dict_cursor.execute(""" INSERT INTO
                    filestats(id, repo_id, project_full_name, file_path, no_of_commits, first_commit_date,
                    last_commit_date, commit_frequency, no_of_developers, top_developer_id, file_id)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    no_of_commits = VALUES(no_of_commits), first_commit_date = VALUES(first_commit_date),
                    last_commit_date = VALUES(last_commit_date), commit_frequency = VALUES(commit_frequency),
                    no_of_developers = VALUES(no_of_developers), top_developer_id = VALUES(top_developer_id) """,
                                           (id["id"], repo_id, file_details["full_name"], file_details["file_path"],
                                            no_of_commits,
                                            first_commit_date, last_commit_date, commit_freq, no_of_developers,
                                            top_developer_id, file_id))
                self.__db.commit()
            else:
                self.__dict_cursor.execute(""" INSERT INTO
                    filestats(repo_id, project_full_name, file_path, no_of_commits, first_commit_date,
                    last_commit_date, commit_frequency, no_of_developers, top_developer_id, file_id)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """,
                                           (
                                           repo_id, file_details["full_name"], file_details["file_path"], no_of_commits,
                                           first_commit_date, last_commit_date, commit_freq, no_of_developers,
                                           top_developer_id, file_id))
                self.__db.commit()
        return

    def get_repo_stats(self, repo_full_name=None):
        # result of all repos
        if not repo_full_name:
            self.__dict_cursor.execute("""SELECT full_name, no_of_commits, no_of_contributors,
                              no_of_changed_files, no_of_file_changes
                              FROM `repositorystats` JOIN repositories ON repo_id = repositories.id""")
            self.__db.commit()
            return self.__dict_cursor.fetchall()
        # result of a single repo
        else:
            self.__dict_cursor.execute("""SELECT no_of_commits, no_of_contributors,
                              no_of_changed_files, no_of_file_changes
                              FROM `repositorystats` JOIN repositories ON repo_id = repositories.id
                              WHERE full_name = %s""", repo_full_name)
            self.__db.commit()
            return self.__dict_cursor.fetchone()
