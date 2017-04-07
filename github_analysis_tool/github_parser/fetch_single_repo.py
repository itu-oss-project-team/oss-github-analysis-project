#!/usr/bin/python

import getopt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

    github_harvester = GitHubHarvester()

    #github_harvester.fetch_repo(owner, repo, force_fetch = force)
    github_harvester.fetch_repo('itu-oss-project-team', 'oss-github-analysis-project', force_fetch = True)

if __name__ == "__main__":
    main(sys.argv[1:])