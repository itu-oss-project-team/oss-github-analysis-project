#!/usr/bin/python
# -*- coding: utf-8 -*-

#import pymysql.cursors
#db=pymysql.connect(passwd="moonpie",db="thangs")


import csv
import json
import requests
import time
import yaml
import os.path

from classes.harvester import GitHubHarvester

def main():

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
        config = yaml.load(ymlfile)


    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    # Let's read projects from projects file
    # TODO:
    with open(os.path.join(os.path.dirname(__file__), os.pardir, config['projects-file']), 'r') as f:
        reader = csv.reader(f)
        projects = []
        #For each row of my .csv file
        for row in reader:
            project = {
                'owner': row[0].strip(),
                'repo': row[1].strip()
            }
            projects.append(project)

    github_harvester = GitHubHarvester(secret_config['github-api']['tokens'], projects)

    github_harvester.retriveCommits();



def insertProject(projectJson):
    return

def insertCommits(commitsJson):
    return

if __name__ == "__main__":
    main()