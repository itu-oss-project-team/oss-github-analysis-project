#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt
import sys

from github_analysis_tool.github_parser.harvester import GitHubHarvester
from github_analysis_tool import secret_config

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

    github_harvester = GitHubHarvester()
    github_harvester.fetch_repos(star, since, until, force)
    # github_harvester.fetchRepos("10000", "2016-01-01T00:00:00Z", "2017-04-01T00:00:00Z", True)
    # github_harvester.fetchRepo("FreeCodeCamp","FreeCodeCamp", "2016-01-01T00:00:00Z", "2017-04-01T00:00:00Z", True)

if __name__ == "__main__":
    main(sys.argv[1:])
