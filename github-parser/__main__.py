#!/usr/bin/python
# -*- coding: utf-8 -*-

#import pymysql.cursors
#db=pymysql.connect(passwd="moonpie",db="thangs")

import json
import requests
import time
import yaml
import os.path

from harvester import GitHubHarvester

def main():

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
        config = yaml.load(ymlfile)


    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    github_harvester = GitHubHarvester(config, secret_config)
    insertProject(github_harvester, secret_config)

def insertProject(github_harvester, secret_config):
    github_harvester.retrieveProjects(40000) #stargazers_count is given as argument.
    github_harvester.retrieveCommits("since=2016-05-01T00:00:00Z") #since is given as argument.
    github_harvester.retrieveContributors()
    return

if __name__ == "__main__":
    main()