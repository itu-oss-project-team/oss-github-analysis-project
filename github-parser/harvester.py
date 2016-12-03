#!/usr/bin/python

import requests
from requester import GitHubRequester
from database_service import DatabaseService


# End point for harvesting GitHub API
class GitHubHarvester:
    def __init__(self, config, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__requester = GitHubRequester(secret_config['github-api'])
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def retrieveProjects(self):

        requestURL = "https://api.github.com/search/repositories?q=stars:>50000&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)

        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            if res.links is not None:
                indexStart = res.links["last"]["url"].find("page=")
                indexEnd = res.links["last"]["url"].find("&per_page")
                last = res.links["last"]["url"][indexStart+5:indexEnd]
            else:
                last = 1

            for i in range(1, int(last)+1):
                print(i)
                requestURL = "https://api.github.com/search/repositories?q=stars:>50000&page=" + str(i) + "&per_page=100"
                res = self.__requester.makeRequest(requestURL)
                returnJson = res.json()

                for project in returnJson["items"]:
                    if project["language"] is None:
                        continue
                    userLogin = project["owner"]["login"]
                    self.retrieveSingleUser(userLogin)
                    self.__databaseService.insertProject(project)
                    # TODO: Fetch project contributors with https://api.github.com/repos/d3/d3/contributors
                    #       Then fetch project commits with https://developer.github.com/v3/repos/commits/
                    #       Remember that in order to obtain additions deletions GET /repos/:owner/:repo/commits/:sha
                    #           must be initiated for every single commit (might be headache)

        else: # Request gave an error
            print("Error while retriving: " + requestURL)
            print("Status code: "  + res.status_code)

        return

    def retrieveSingleUser(self, userLogin):
        userURL = "https://api.github.com/users/" + userLogin
        res = self.__requester.makeRequest(userURL)
        userData = res.json()
        if (res.status_code == 200):  # API has responded with OK status
            self.__databaseService.insertUser(userData)
        else:  # Request gave an error
            print("Error while retriving: " + userURL)
            print("Status code: " + res.status_code)

        return

    def retrieveCommits(self):
        urls = self.__databaseService.getRepoUrls()
        for repoURL, project_id in urls:
            print(repoURL)
            print(project_id)
            requestURL = str(repoURL) + "/commits?since=2016-05-01T00:00:00Z&page=1&per_page=100"
            res = self.__requester.makeRequest(requestURL)
            if (res.status_code == 200): #API has responded with OK status
                returnJson = res.json()
                if res.links is not None:
                    indexStart = res.links["last"]["url"].find("page=")
                    indexEnd = res.links["last"]["url"].find("&per_page")
                    last = res.links["last"]["url"][indexStart+5:indexEnd]
                else:
                    last = 1

                for i in range(1, int(last)+1):
                    print(i)
                    requestURL = str(repoURL) + "/commits?since=2016-05-01T00:00:00Z&page=" + str(i) + "&per_page=100"
                    res = self.__requester.makeRequest(requestURL)
                    returnJson = res.json()

                    for commit in returnJson:
                        requestURL = str(repoURL) + "/commits/" + str(commit["sha"])
                        res = self.__requester.makeRequest(requestURL)
                        commitDetail = res.json()
                        if commitDetail["author"]["login"] or commitDetail["committer"]["login"] is not None:
                            self.retrieveSingleUser(commitDetail["author"]["login"])
                            self.retrieveSingleUser(commitDetail["committer"]["login"])
                        self.__databaseService.insertCommit(commitDetail, project_id)
