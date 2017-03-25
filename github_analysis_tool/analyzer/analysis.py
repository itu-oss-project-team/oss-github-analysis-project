import os.path

import dateutil.parser
import yaml

from github_analysis_tool.services.database_service import DatabaseService


class Analysis:
    def __init__(self, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def setMonthlyRepoStats(self, repo):
        start_date = dateutil.parser.parse("2016-01-01 00:00:00")
        end_date = dateutil.parser.parse("2017-03-01 00:00:00")

        repo_id = self.__databaseService.getRepoByFullName(repo)["id"]
        self.__databaseService.findNumberOfCommitsAndContributorsOfProjectMonthly(repo_id, start_date, end_date)
        return

    def setFileStats(self, repo):
        repo_id = self.__databaseService.getRepoByFullName(repo)["id"]
        self.__databaseService.findNumberOfCommitsAndDevelopersOfRepositoryFiles(repo_id)
        return

    def setRepoStats(self, repo):
        repo_id = self.__databaseService.getRepoByFullName(repo)["id"]
        self.__databaseService.findNumberOfCommitsAndContributorsOfProject(repo_id)
        return

    def getRepos(self):
        repos = self.__databaseService.getAllRepos(get_only_ids=True)
        return repos

    def getRepo(self, full_name):
        repo = self.__databaseService.getRepoByFullName(full_name, get_only_ids=True)
        return repo

def main():
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    analysis = Analysis(secret_config)

    directory_path = os.path.dirname(os.path.realpath(__file__))
    repositories_file_path = os.path.join(directory_path, 'repositories.txt')
    repos = [line.rstrip('\n') for line in open(repositories_file_path)]
    for repo in repos:
        print("Repo " + str(repo) + " is started.")
        analysis.setRepoStats(repo)
        #analysis.setMonthlyRepoStats(repo)
        #analysis.setFileStats(repo)
        print("Repo " + str(repo) + " is done.")
    print("Monthly repo stats and file stats analyses are done.")

    return

main()



