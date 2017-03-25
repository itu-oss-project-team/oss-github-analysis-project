#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt
import os.path
import sys
import yaml

from github_analysis_tool.github_parser.harvester import GitHubHarvester

def main(argv):
    owner = ""
    repo = ""
    force = False

    try:
        opts, args = getopt.getopt(argv, "o:r:f", ["owner=", "repo=", "force"])
    except getopt.GetoptError:
        print('ERROR in input arguments!')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':  # Help case
            print('fetch_repo.py -o <owner> -r <repo> -f Ex: fetch_repo.py --owner itu-oss-project-team  --repo oss-github-analysis-project --force')
            sys.exit()
        elif opt in ("-o", "--owner"):
            owner = arg
        elif opt in ("-r", "--repo"):
            repo = arg
        elif opt in ("-f", "--force"):
            force = True

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
        config = yaml.load(ymlfile)

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    github_harvester = GitHubHarvester(config, secret_config)

    github_harvester.fetchRepo(owner, repo, force_fetch = force)
    #github_harvester.fetchRepo('itu-oss-project-team', 'oss-github-analysis-project', force_fetch = true)

if __name__ == "__main__":
    main(sys.argv[1:])