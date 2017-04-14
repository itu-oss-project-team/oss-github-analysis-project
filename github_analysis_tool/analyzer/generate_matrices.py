import os.path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from github_analysis_tool.analyzer.commit_based_analyzer import CommitBasedAnalyzer
from github_analysis_tool.analyzer.contributor_matrix_generator import ContributorMatrixGenerator
from github_analysis_tool.analyzer.file_based_analyzer import FileBasedAnalyzer
from github_analysis_tool.services.database_service import DatabaseService


class GenerateMatrices:
    def __init__(self):
        self.__databaseService = DatabaseService()

    def create_matrices(self):
        file_analyzer = FileBasedAnalyzer()
        commit_analyzer = CommitBasedAnalyzer()
        contributor_matrix_generator = ContributorMatrixGenerator()

        directory_path = os.path.dirname(os.path.realpath(__file__))
        repositories_file_path = os.path.join(directory_path, 'repositories.txt')
        finished_repositories_path = os.path.join(directory_path, 'finished_repositories.txt')

        repos = [line.rstrip('\n') for line in open(repositories_file_path)]
        if os.path.exists(finished_repositories_path):
            finished_repos = [line.rstrip('\n') for line in open(finished_repositories_path)]
        else:
            finished_repos = []

        repos_left = []

        for repo in repos:
            if repo not in finished_repos:
                repos_left.append(repo)

        for repo in repos_left:
            repository = self.__databaseService.get_repo_by_full_name(repo)
            repo_id = repository['id']

            file_analyzer.analyze_repo(repo)
            commit_analyzer.analyze_repo(repo)
            contributor_matrix_generator.create_matrix(repo_id)
            print('\n')


GM = GenerateMatrices()
GM.create_matrices()
