#!/usr/bin/python
# -*- coding: utf-8 -*-
import getopt
import os.path
import sys
import yaml

from harvester import GitHubHarvester
from contributor_matrix_generator import ContributorMatrixGenerator

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

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
        config = yaml.load(ymlfile)

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

<<<<<<< HEAD
    #github_harvester = GitHubHarvester(config, secret_config)
    #github_harvester.fetchRepos("40000", "2016-01-01T00:00:00Z", None, True)
    
    #github_harvester.fetchRepo("itu-oss-project-team","oss-github-analysis-project", "2016-01-01T00:00:00Z", None, True)
    
    matrix_gen = ContributorMatrixGenerator(secret_config)
    matrix_gen.create_matrix(71659875)
    
=======
    github_harvester = GitHubHarvester(config, secret_config)
    github_harvester.fetchRepos(star, since, until, force)
    #github_harvester.fetchRepos("10000", "2016-01-01T00:00:00Z", "2017-04-01T00:00:00Z", True)

>>>>>>> 81eb423910aa59547e5859e881f2c890d7c31104
if __name__ == "__main__":
    main(sys.argv[1:])
