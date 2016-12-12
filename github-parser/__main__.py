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
    github_harvester.fetchProjects("40000", "2016-05-01T00:00:00Z", None)

if __name__ == "__main__":
    main()