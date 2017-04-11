#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt
import sys
<<<<<<< HEAD:github_analysis_tool/github_parser/__main__.py
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.github_parser.harvester import GitHubHarvester
from github_analysis_tool import secret_config
=======
import yaml
#reload(sys)
#sys.setdefaultencoding('UTF-8')

from harvester import GitHubHarvester
from Szz import IssueLinker
>>>>>>> master:github-parser/__main__.py

def main(argv):
    since = None
    until = None
    star = 10000
    force = False
    try:
        opts, args = getopt.getopt(argv, "hu:s:f", ["since=", "until=", "star=", "force"])
    except getopt.GetoptError:
        print('ERROR in input arguments!')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':  # Help case
            print('__main.py__ -s <since_date> -u <until_date> --star <min_star_number> -f')
            sys.exit()
        elif opt in ("-s", "--since"):
            since = arg
        elif opt in ("-u", "--until"):
            until = arg
        elif opt in ("--star"):
            star = arg
        elif opt in ("-f", "--force"):
            force = True

<<<<<<< HEAD:github_analysis_tool/github_parser/__main__.py
    github_harvester = GitHubHarvester()
    github_harvester.fetch_repos(star, since, until, force)
    # github_harvester.fetchRepos("10000", "2016-01-01T00:00:00Z", "2017-04-01T00:00:00Z", True)
    # github_harvester.fetchRepo("FreeCodeCamp","FreeCodeCamp", "2016-01-01T00:00:00Z", "2017-04-01T00:00:00Z", True)
=======
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
        config = yaml.load(ymlfile)

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)
    
    
    github_harvester = GitHubHarvester(config, secret_config)
    #IssueLinker("13446",1,secret_config)
    github_harvester.fetchRepos(star, since, until, force)
    #github_harvester.fetchRepos("10000", "2016-01-01T00:00:00Z", "2017-04-01T00:00:00Z", True)
    #github_harvester.fetchRepo("FreeCodeCamp","FreeCodeCamp", "2016-01-01T00:00:00Z", "2017-04-01T00:00:00Z", True)
>>>>>>> master:github-parser/__main__.py

if __name__ == "__main__":
    main(sys.argv[1:])
