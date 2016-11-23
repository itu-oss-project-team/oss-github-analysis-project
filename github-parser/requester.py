#!/usr/bin/python

import requests

# A class to make API calss to GitHub
# Adding tokens headers etc. will be handled automatically
class GitHubRequester:
    def __init__(self, tokens):
        self.__tokens = tokens

    def makeRequest(self, url):
        # TODO Improve this function to detect request limit exceeds and use token pool when out of requests

        headers = {'Authorization': 'token ' + self.__tokens[0]}
        r = requests.get(url, headers=headers)

        return r
