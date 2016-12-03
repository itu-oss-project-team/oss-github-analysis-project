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

    def retrieveProjects(self, stars_count):

        requestURL = "https://api.github.com/search/repositories?q=stars:>" + str(stars_count) + "&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)

        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            if res.links == "{}":
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
                    self.retrieveSingleUser(userLogin)
                    self.__databaseService.insertProject(project)
        else: # Request gave an error
            print("Error while retrieving: " + requestURL)
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

    def retrieveCommits(self, since):
        urls = self.__databaseService.getRepoUrls()
        for repoURL, project_id in urls:
            print("Retriving commits from repoURL")
            requestURL = str(repoURL) + "/commits?since=" + since + "&page=1&per_page=100"
            res = self.__requester.makeRequest(requestURL)
            if (res.status_code == 200): #API has responded with OK status
                returnJson = res.json()
                if res.links == "{}":
                    indexStart = res.links["last"]["url"].find("page=")
                    indexEnd = res.links["last"]["url"].find("&per_page")
                    last = res.links["last"]["url"][indexStart+5:indexEnd]
                else:
                    last = 1

                for i in range(1, int(last)+1):
                    print(i)
                    _requestURL = str(repoURL) + "/commits?since=" + since + "&page=" + str(i) + "&per_page=100"
                    res = self.__requester.makeRequest(_requestURL)
                    returnJson = res.json()

                    for commit in returnJson:
                        __requestURL = str(repoURL) + "/commits/" + str(commit["sha"])
                        res = self.__requester.makeRequest(__requestURL)
                        commitDetail = res.json()
                        if commitDetail["author"]["login"] or commitDetail["committer"]["login"] is not None:
                            self.retrieveSingleUser(commitDetail["author"]["login"])
                            self.retrieveSingleUser(commitDetail["committer"]["login"])
                        self.__databaseService.insertCommit(commitDetail, project_id)

            else: # Request gave an error
                print("Error while retrieving: " + requestURL)
                print("Status code: "  + res.status_code)

