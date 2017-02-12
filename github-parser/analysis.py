from database_service import DatabaseService
from datetime import datetime
import yaml
import os.path
import dateutil.parser

class Analysis:
    def __init__(self, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def setMonthlyProjectStats(self, repo_id):
        start_date = dateutil.parser.parse("2016-01-01 00:00:00")
        end_date = dateutil.parser.parse("2017-02-01 00:00:00")

        self.__databaseService.findNumberOfCommitsAndContributorsOfProjectMonthly(repo_id, start_date, end_date)
        return

    def setFileStats(self, repo_id):

        self.__databaseService.findNumberOfCommitsAndDevelopersOfRepositoryFiles(repo_id)
        return

    def getRepos(self):
        repos = self.__databaseService.getAllRepos(get_only_ids=True)
        return repos

def main():
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    analysis = Analysis(secret_config)
    repos = analysis.getRepos()
    for repo in repos:
        print("Repo " + str(repo) + " is started.")
        analysis.setMonthlyProjectStats(repo)
        analysis.setFileStats(repo)
        print("Repo " + str(repo) + " is done.")
    print("Monthly project stats and file stats analyses are done.")
    return

main()



