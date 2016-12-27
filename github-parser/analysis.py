from database_service import DatabaseService
from datetime import datetime
import yaml
import os.path
import dateutil.parser

class Analysis:
    def __init__(self, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def setMonthlyProjectStats(self):
        start_date = dateutil.parser.parse("2013-01-01 00:00:00")
        end_date = dateutil.parser.parse("2017-01-01 00:00:00")
        repos = self.__databaseService.getAllRepos()
        print(repos)
        for repo in repos:
            print(repo)
            self.__databaseService.findNumberOfCommitsAndContributorsOfProjectMonthly(repo[0], start_date, end_date)

        return


def main():
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    analysis = Analysis(secret_config)
    analysis.setMonthlyProjectStats()

main()



