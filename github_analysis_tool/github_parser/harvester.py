#!/usr/bin/python

import time
from datetime import datetime
import logging
import os.path

from github_analysis_tool.github_parser.requester import GitHubRequester
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool.services.db_column_constants import Columns
from github_analysis_tool import OUTPUT_DIR

class GitHubHarvester:
    """
    End point for harvesting GitHub API
    """
    def __init__(self):
        # Generate a github_requester with imported GitHub tokens
        self.__requester = GitHubRequester()
        self.__databaseService = DatabaseService()
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG,
                            filename=os.path.join(OUTPUT_DIR, "github_parser_log.log"))

    def fetch_repo(self, owner, repo, since_date=None, until_date=None, force_fetch=False):
        repo_url = "https://api.github.com/repos/" + owner + "/" + repo
        time_param = self.__build_time_parameter_string(since_date, until_date)
        res = self.__requester.make_request(repo_url)

        if res.status_code == 200:  # API has responded with OK status
            repo = res.json()
            repo_id = repo['id']
            if repo["language"] is None:
                print("Project language is none, skipped.")
                logging.info("Project language is none, skipped.")
                return
            user_login = repo["owner"]["login"]
            if not self.__databaseService.check_if_github_user_exists(user_login):
                self.__retrieve_user(user_login)
            self.__databaseService.insert_repo(repo)
        else:  # Request gave an error
            print("Error while retrieving: " + repo_url)
            print("Status code: " + str(res.status_code))
            logging.info("Error while rertieving :" + str(repo_url) + "Status code: " + str(res.status_code))
            return

        if not force_fetch and self.__databaseService.check_if_repo_filled(repo_id):
            # Repo filled before so i can skip it now
            print("Repo already fetched: " + repo_url)
            logging.info("Repo already fetched: " + repo_url)
            return

        print("---> Fetching: " + repo_url)
        logging.info("---> Fetching: " + repo_url)
        # Repo can be new as it's first info
        start_time_string = str(datetime.now())
        start_time = time.time()
        self.__retrieve_issues_of_repo(repo_url, repo_id)
        self.__retrieve_commits_of_repo(repo_url, repo_id, time_param)
        #self.__retrieveIssuesofRepo(repo_url, repo_id)
        # Let's mark the repo as filled with time which is beginning of fetching
        self.__databaseService.set_repo_filled_at(repo_id, start_time_string)
        elapsed_time = time.time() - start_time
        print("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")
        logging.info("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")
        return

    def fetch_repos(self, min_stars, since_date=None, until_date=None, force_fetch=False):
        #self.__retrieve_repos(min_stars)

        repos = self.__databaseService.get_repo_urls()
        for repo in repos:
            repo_url = repo[Columns.Repo.url]
            if repo_url == "https://api.github.com/repos/torvalds/linux":
                continue

            repo_id = repo[Columns.Repo.id]

            print("---> Fetching: " + repo_url)
            logging.info("---> Fetching: " + repo_url)
            # Repo can be new as it's first info
            start_time_string = str(datetime.now())
            start_time = time.time()

            if repo[Columns.Repo.filled_at] is not None and force_fetch is False:
                repo_filled_at = repo[Columns.Repo.filled_at]
                print("---> Repo: " + repo_url + " has some data in it, starting from this time: " + str(repo_filled_at))
                logging.info("---> Repo: " + repo_url + " has some data in it, starting from this time: " + str(repo_filled_at))
                repo_filled_at_str = str(repo_filled_at).split()
                repo_filled_at_string = repo_filled_at_str[0] + "T" + repo_filled_at_str[1] + "Z"
                time_param = self.__build_time_parameter_string(repo_filled_at_string, until_date)
            else:
                time_param = self.__build_time_parameter_string(since_date, until_date)
                
            #self.__retrieve_issues_of_repo(repo_url, repo_id)
            self.__retrieve_commits_of_repo(repo_url, repo_id, time_param)

            # Let's mark the repo as filled with time which is beginning of fetching
            self.__databaseService.set_repo_filled_at(repo_id, start_time_string)
            elapsed_time = time.time() - start_time
            print("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")
            logging.info("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")

    def __retrieve_repos(self, stars_count):
        request_url = "https://api.github.com/search/repositories?q=stars:>" + str(stars_count) + "&page=1&per_page=100"
        res = self.__requester.make_request(request_url)
        print("Started retriving projects")
        logging.info("Started retriving projects")
        if res.status_code == 200: # API has responded with OK status
            return_json = res.json()
            if res.links:
                index_start = res.links["last"]["url"].find("page=")
                index_end = res.links["last"]["url"].find("&per_page")
                last = res.links["last"]["url"][index_start+5:index_end]
            else:
                last = 1

            for i in range(1, int(last)+1):
                print("Repositories: " + str(i))
                logging.info("Repositories: " + str(i))
                _requestURL = "https://api.github.com/search/repositories?q=stars:>" + str(stars_count) + "&page=" + str(i) + "&per_page=100"
                res = self.__requester.make_request(_requestURL)
                return_json = res.json()

                for project in return_json["items"]:
                    if project["language"] is None:
                        continue
                    user_login = project["owner"]["login"]
                    if not self.__databaseService.check_if_github_user_exists(user_login):
                        self.__retrieve_user(user_login)
                    self.__databaseService.insert_repo(project)
        else: # Request gave an error
            print("Error while retrieving: " + request_url)
            print("Status code: " + str(res.status_code))
        print("Finished retrieving projects")
        return

    def __retrieve_user(self, user_login):
        user_url = "https://api.github.com/users/" + user_login
        res = self.__requester.make_request(user_url)
        user_data = res.json()
        if res.status_code == 200:  # API has responded with OK status
            self.__databaseService.insert_github_user(user_data)
        else:  # Request gave an error
            print("Error while retrieving: " + user_url)
            print("Status code: " + str(res.status_code))
            logging.info("Error while rertieving :" + str(user_url) + "Status code: " + str(res.status_code))

        return

    def __retrieve_commits_of_repo(self, repo_url, repo_id, since):
        print("Retrieving commits from " + repo_url)
        logging.info("Retrieving commits from " + repo_url)
        request_url = str(repo_url) + "/commits?" + since + "&page=1&per_page=100"
        res = self.__requester.make_request(request_url)
        if res.status_code == 200: # API has responded with OK status
            return_json = res.json()
            if res.links:
                index_start = res.links["last"]["url"].find("page=")
                index_end = res.links["last"]["url"].find("&per_page")
                last = res.links["last"]["url"][index_start+5:index_end]
            else:
                last = 1

            for i in range(1, int(last)+1):
                print("Commits page: ", i)
                logging.info("Commits page: " + str(i))
                _requestURL = str(repo_url) + "/commits?" + since + "&page=" + str(i) + "&per_page=100"
                res = self.__requester.make_request(_requestURL)
                return_json = res.json()

                for commit in return_json:
                    if self.__databaseService.check_if_commit_exists(commit["sha"]):
                        continue
                    __requestURL = str(repo_url) + "/commits/" + str(commit["sha"])
                    res = self.__requester.make_request(__requestURL)
                    commit_detail = res.json()

                    # print( str(repoURL) + " current commit sha: " + commitDetail["sha"])
                    if commit_detail is None:
                        continue

                    try:
                        # insert Author
                        if commit_detail["author"] is not None: # if there's an author field.
                            # if user does not exist in database.
                            if not self.__databaseService.check_if_github_user_exists(commit_detail["author"]["login"]):
                                self.__retrieve_user(commit_detail["author"]["login"]) # retrieve and add user.

                        else: # if there's no author field. --> non-github user.
                            # if non-github user exist in database
                            if commit_detail["commit"]["author"]["email"]: # if non-github user has an email info.
                                if not self.__databaseService.check_if_commit_exists(commit_detail["commit"]["author"]["email"]):
                                    self.__databaseService.insert_non_github_user(commit_detail["commit"]["author"]) # add non-github user.
                            else:
                                raise

                        # insert Committer key

                        if commit_detail["committer"] is not None: # if there's an committer field.
                            # if user does not exist in database.
                            if not self.__databaseService.check_if_github_user_exists(commit_detail["committer"]["login"]):
                                    self.__retrieve_user(commit_detail["committer"]["login"]) # retrieve and add user.

                        else: # if there's no committer field. --> non-github user.
                            # if non-github user exist in database
                            if commit_detail["commit"]["committer"]["email"]:
                                if not self.__databaseService.check_if_user_exists(commit_detail["commit"]["committer"]["email"]):
                                    self.__databaseService.insert_non_github_user(commit_detail["commit"]["committer"]) # add non-github user

                            else:
                                raise

                        self.__databaseService.insert_commit(commit_detail, repo_id)

                    except Exception:
                        with open("commit_problems.txt", "a") as commit_problems_file:
                                if "sha" not in commit_detail:
                                    commit_problems_file.write(str(datetime.now()) + " " + str(repo_url) +
                                                               " page: " + str(i) + "\n")
                                    logging.info(" " + str(repo_url) + " page: " + str(i))
                                else:
                                    commit_problems_file.write(str(datetime.now()) + " " + str(repo_url) +
                                                               "/commits/" + commit_detail["sha"] + "\n")
                                    logging.info(str(datetime.now()) + " " + str(repo_url) +
                                                               "/commits/" + commit_detail["sha"])
                        pass


        else:  # Request gave an error
            print("Error while retrieving: " + request_url)
            print("Status code: " + str(res.status_code))

    def __retrieve_contributors_of_repo(self, repo_url, repo_id):
        index = 1

        while True:
            contributions_url = repo_url + "/contributors?page= " + str(index) + "&per_page=100"
            result = self.__requester.make_request(contributions_url)

            if result.status_code == 200:
                result_json = result.json()
                index = index + 1

                if not result_json:
                    break
                else:
                    for contributor in result_json:
                        login = contributor["login"]
                        contributions = contributor["contributions"]

                        # TODO: Debug log here
                        # print("Adding the user with login: " + login)
                        if self.__databaseService.check_if_github_user_exists(login) is False:
                            # There is no user entry in our DB with this login info so just fetch and insert it
                            self.__retrieve_user(login)

                        user_id = self.__databaseService.get_user_id_from_login(login)
                        self.__databaseService.insert_contribution(user_id, repo_id, contributions)

            else: # Request gave an error
                print("Error while retrieving: " + contributions_url)
                print("Status code: " + str(result.status_code))

    def __retrieve_issues_of_repo(self, repo_url, repo_id):
        index = 1

        while True:
            issues_url = repo_url + "/issues?page=" + str(index) + "&per_page=100"
            result = self.__requester.make_request(issues_url)
            print("Issues page: " + str(index))
            if result.status_code == 200:
                result_json = result.json()
                index = index + 1

                if not result_json:
                    break

                for issues in result_json:
                        issue_id = issues["id"]
                        url = issues["url"]
                        number = issues["number"]
                        title =  issues["title"]
                        repo_id = repo_id
                        reporter_id = issues["user"]["id"]
                        assignee_id = None
                        #assignee_id = issues["assignee"]
                        #if assignee_id:
                          # assignee_id =assignee_id["id"]
                        state = issues["state"]
                        comments = issues["comments"]
                        created_at = str(issues["created_at"])[:10]
                        updated_at = str(issues["updated_at"])[:10]
                        #print(str(issues["closed_at"]))
                        closed_at = "0000-00-00"
                        if str(issues["closed_at"]) == "None":
                            closed_at = "2000-01-01 00:00:00"
                        else:
                             closed_at = str(issues["closed_at"])[:10]

                        #print(issues["number"])
                        #print(title)
                        #print(closed_at)
                        self.__databaseService.insert_issue(issue_id,url,number,title,repo_id,reporter_id, assignee_id, state,comments, created_at, updated_at, closed_at)

                        #print(str(url))

            else:  # Request gave an error
                print("Error while retrieving: " + issues_url)
                print("Status code: " + str(result.status_code))

    def __build_time_parameter_string(self, since_date, until_date):
        # Let's build time parameters string for requests that accept time intervals as parameters
        time_param = ""
        if since_date is not None:
            time_param = time_param + "&since=" + since_date
        if until_date is not None:
            time_param = time_param + "&until=" + until_date
        return time_param

