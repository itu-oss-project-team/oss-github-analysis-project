#!/usr/bin/python

import requests

# A class to make API calss to GitHub
# Adding tokens headers etc. will be handled automatically
class GitHubRequester:
    def __init__(self, github_api_config):
        self.__tokens = github_api_config['tokens']
        self.__RateLimit_Remaining = 5000
        self.__tokenOrder = 0
    def makeRequest(self, url):
        # TODO Improve this function to detect request limit exceeds and use token pool when out of requests

        if int(self.__RateLimit_Remaining) <= 1 and self.__tokenOrder == 0:
            self.__tokenOrder = self.__tokenOrder + 1
            print("X-Rate limit remaining: " + str(self.__RateLimit_Remaining))
            print("Token order is incremented to " + str(self.__tokenOrder))

        elif int(self.__RateLimit_Remaining) <= 1 and self.__tokenOrder == 1:
            self.__tokenOrder = self.__tokenOrder - 1
            print("X-Rate limit remaining: " + str(self.__RateLimit_Remaining))
            print("Token order is decremented to " + str(self.__tokenOrder))

        token = self.__tokens[int(self.__tokenOrder)]
        headers = {'Authorization': 'token ' + token}
        r = requests.get(url, headers=headers)
        self.__RateLimit_Remaining = r.headers["X-RateLimit-Remaining"]
        return r