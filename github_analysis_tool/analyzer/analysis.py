import os.path
import dateutil.parser

from github_analysis_tool.services.database_service import DatabaseService


class Analysis:
    def __init__(self):
        # Generate a github_requester with imported GitHub tokens
        self.__databaseService = DatabaseService()

    def set_monthly_repo_stats(self, repo):
        start_date = dateutil.parser.parse("2016-01-01 00:00:00")
        end_date = dateutil.parser.parse("2017-03-01 00:00:00")

        repo_id = self.__databaseService.get_repo_by_full_name(repo)["id"]
        self.__databaseService.find_number_of_commits_and_contributors_of_repo_monthly(repo_id, start_date, end_date)

    def set_file_stats(self, repo):
        repo_id = self.__databaseService.get_repo_by_full_name(repo)["id"]
        self.__databaseService.find_number_of_commits_and_developers_of_repository_files(repo_id)

    def set_repo_stats(self, repo):
        repo_id = self.__databaseService.get_repo_by_full_name(repo)["id"]
        self.__databaseService.find_number_of_commits_and_contributors_of_repo(repo_id)

    def get_repos(self):
        repos = self.__databaseService.get_all_repos(get_only_ids=True)
        return repos

    def get_repo(self, full_name):
        repo = self.__databaseService.get_repo_by_full_name(full_name, get_only_ids=True)
        return repo


def main():
    print("-->Monthly repo stats and file stats analyses started.")
    analysis = Analysis()

    directory_path = os.path.dirname(os.path.realpath(__file__))
    repositories_file_path = os.path.join(directory_path, 'repositories.txt')
    repos = [line.rstrip('\n') for line in open(repositories_file_path)]
    for repo in repos:
        print("---->Repo " + str(repo) + " is started.")
        analysis.set_repo_stats(repo)
        #analysis.setMonthlyRepoStats(repo)
        #analysis.setFileStats(repo)
        print("---->Repo " + str(repo) + " is done.")
    print("-->Monthly repo stats and file stats analyses are done.")

    return

main()



