#!/usr/bin/python

from requester import GitHubRequester
from database_service import DatabaseService
from datetime import datetime
import time

# End point for harvesting GitHub API
class GitHubHarvester:
    def __init__(self, config, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__requester = GitHubRequester(secret_config['github-api'])
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def fetchRepo(self, owner, repo, since_date=None, until_date=None, force_fetch=False):
        repo_url = "https://api.github.com/repos/" + owner + "/" + repo
        time_param = self.__buildTimeParameterString(since_date, until_date)
        res = self.__requester.makeRequest(repo_url)

        if res.status_code == 200:  # API has responded with OK status
            repo = res.json()
            repo_id = repo['id']
            if repo["language"] is None:
                print("Project language is none, skipped.")
                return
            user_login = repo["owner"]["login"]
            if not self.__databaseService.checkIfGithubUserExist(user_login):
                self.__retrieveSingleUser(user_login)
            self.__databaseService.insertProject(repo)
        else:  # Request gave an error
            print("Error while retrieving: " + repo_url)
            print("Status code: " + str(res.status_code))

        if not force_fetch and self.__databaseService.checkIfRepoFilled(repo_id):
            # Repo filled before so i can skip it now
            print("Repo already fetched: " + repo_url)
            return

        print("---> Fetching: " + repo_url)
        # Repo can be new as it's first info
        start_time_string = str(datetime.now())
        start_time = time.time()
        self.__retrieveCommitsOfRepo(repo_url, repo_id, time_param)
        self.__retrieveContributorsOfRepo(repo_url, repo_id)
        # Let's mark the repo as filled with time which is beginning of fetching
        self.__databaseService.setRepoFilledAt(repo_id, start_time_string)
        elapsed_time = time.time() - start_time
        print("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")
        return

    def fetchRepos(self, min_stars, since_date=None, until_date=None, force_fetch=False):
        self.__retrieveProjects(min_stars)

        time_param = self.__buildTimeParameterString(since_date, until_date)

        repos = self.__databaseService.getRepoUrls()
        for repo_url, repo_id in repos:
            if not force_fetch and self.__databaseService.checkIfRepoFilled(repo_id):
                # Repo filled before so i can skip it now
                print("Repo already fetched: " + repo_url)
                continue

            print("---> Fetching: " + repo_url)
            # Repo can be new as it's first info
            start_time_string = str(datetime.now())
            start_time = time.time()
            self.__retrieveCommitsOfRepo(repo_url, repo_id, time_param)
            self.__retrieveContributorsOfRepo(repo_url, repo_id)
            # Let's mark the repo as filled with time which is beginning of fetching
            self.__databaseService.setRepoFilledAt(repo_id, start_time_string)
            elapsed_time = time.time() - start_time
            print("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")

    def __retrieveProjects(self, stars_count):

        requestURL = "https://api.github.com/search/repositories?q=stars:>" + str(stars_count) + "&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)
        print("Started retriving projects")
        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            if res.links:
                print(res.links)
                indexStart = res.links["last"]["url"].find("page=")
                indexEnd = res.links["last"]["url"].find("&per_page")
                last = res.links["last"]["url"][indexStart+5:indexEnd]
            else:
                last = 1

            for i in range(1, int(last)+1):
                print(i)
                _requestURL = "https://api.github.com/search/repositories?q=stars:>" + str(stars_count) + "&page=" + str(i) + "&per_page=100"
                res = self.__requester.makeRequest(_requestURL)
                returnJson = res.json()

                for project in returnJson["items"]:
                    if project["language"] is None:
                        continue
                    userLogin = project["owner"]["login"]
                    if self.__databaseService.checkIfGithubUserExist(userLogin) == False:
                        self.__retrieveSingleUser(userLogin)
                    self.__databaseService.insertProject(project)
        else: # Request gave an error
            print("Error while retrieving: " + requestURL)
            print("Status code: "  + str(res.status_code))
        print("Finished retriving projects")
        return

    def __retrieveSingleUser(self, userLogin):
        userURL = "https://api.github.com/users/" + userLogin
        res = self.__requester.makeRequest(userURL)
        userData = res.json()
        if (res.status_code == 200):  # API has responded with OK status
            self.__databaseService.insertGithubUser(userData)
        else:  # Request gave an error
            print("Error while retriving: " + userURL)
            print("Status code: " + str(res.status_code))

        return

    def __retrieveCommitsOfRepo(self, repoURL, project_id, since):
        print("Retriving commits from " + repoURL)
        requestURL = str(repoURL) + "/commits?" + since + "&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)
        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            if res.links:
                indexStart = res.links["last"]["url"].find("page=")
                indexEnd = res.links["last"]["url"].find("&per_page")
                last = res.links["last"]["url"][indexStart+5:indexEnd]
            else:
                last = 1

            for i in range(1, int(last)+1):
                print("Commits page: " , i)
                _requestURL = str(repoURL) + "/commits?" + since + "&page=" + str(i) + "&per_page=100"
                res = self.__requester.makeRequest(_requestURL)
                returnJson = res.json()

                for commit in returnJson:
                    if self.__databaseService.checkIfCommitExist(commit["sha"]) == False:
                        __requestURL = str(repoURL) + "/commits/" + str(commit["sha"])
                        res = self.__requester.makeRequest(__requestURL)
                        commitDetail = res.json()

                        print( str(repoURL) + " current commit sha: " + commitDetail["sha"])
                        if commitDetail is not None:

                            if commitDetail["author"] is not None:
                                if self.__databaseService.checkIfGithubUserExist(commitDetail["author"]["login"]) == False:
                                    self.__retrieveSingleUser(commitDetail["author"]["login"])
                            else:
                                if self.__databaseService.checkIfUserExist(commitDetail["commit"]["author"]["email"]) == False:
                                    self.__databaseService.insertUser(commitDetail["commit"]["author"])

                            if commitDetail["committer"] is not None:
                                if self.__databaseService.checkIfGithubUserExist(commitDetail["committer"]["login"]) == False:
                                    self.__retrieveSingleUser(commitDetail["committer"]["login"])
                            else:
                                if self.__databaseService.checkIfUserExist(commitDetail["commit"]["committer"]["email"]) == False:
                                    self.__databaseService.insertUser(commitDetail["commit"]["committer"])

                            self.__databaseService.insertCommit(commitDetail, project_id)

        else: # Request gave an error
            print("Error while retrieving: " + requestURL)
            print("Status code: "  + str(res.status_code))

    def __retrieveContributorsOfRepo(self, repoUrl, project_id):
        index = 1

        while(1):
            contributionsURL = repoUrl + "/contributors?page= " +  str(index) + "&per_page=100"
            result = self.__requester.makeRequest(contributionsURL)

            if(result.status_code == 200):
                resultJson = result.json()
                index = index + 1

                if not resultJson:
                    break
                else:
                    for contributor in resultJson:
                        login = contributor["login"]
                        contributions = contributor["contributions"]

                        #print("Adding the user with login: " + login)
                        if(self.__databaseService.checkIfGithubUserExist(login) is False):
                            # There is no user entry in our DB with this login info so just fetch and insert it
                            self.__retrieveSingleUser(login)

                        userid = self.__databaseService.getUserIdFromLogin(login)
                        self.__databaseService.insertContribution(userid,project_id,contributions)

            else: # Request gave an error
                print("Error while retrieving: " + contributionsURL)
                print("Status code: "  + str(result.status_code))

    def __buildTimeParameterString(self, since_date, until_date):
        # Let's build time parameters string for requests that accept time intervals as parameters
        time_param = ""
        if since_date is not None:
            time_param = time_param + "&since=" + since_date
        if until_date is not None:
            time_param = time_param + "&until=" + until_date
        return time_param
