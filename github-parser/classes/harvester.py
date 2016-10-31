#!/usr/bin/python

import requests
from .requester import GitHubRequester

# End point for harvesting GitHub API
class GitHubHarvester:
    def __init__(self, tokens, projects):
        # Generate a github_requester with imported GitHub tokens
        self.__requester = GitHubRequester(tokens)
        self.__projects = projects


    def retriveCommits(self):
    # TODO This function should traverse all projects and then call __retriveCommitsFromRepo
        for project in self.__projects:
            print(project['owner'], '/', project['repo'])
            self.__retriveCommitsFromRepo(project['owner'], project['repo'])


    def __retriveCommitsFromRepo(self, owner, repo):
        # TODO This is of course will only return last 100 commits, make it traverse all pages
        requestURL = "https://api.github.com/repos/" + owner.strip() + "/" + repo.strip() + "/commits"
        r = self.__requester.makeRequest(requestURL)

        if (r.status_code == 200): #API has responded with OK status
            returnJson = r.json();

            for commit in returnJson:
                print(commit['commit']['message'])
            # TODO I have commits as a JSON, now I should insert them to DB. somehow...
        else:
            # TODO Definetly I entercoured with an error from API, what should I do now?
            print('Hatasiz kul olmaz, hatamla sev beni')

        return