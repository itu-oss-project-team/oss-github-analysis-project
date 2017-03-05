import yaml
import os.path
from file_matrix_generator import FileMatrixGenerator
from commit_matrix_generator import CommitMatrixGenerator
from contributor_matrix_generator import ContributorMatrixGenerator
from database_service import DatabaseService


class GenerateMatrices:
    def __init__(self, config, secret_config):
        self.__config = config
        self.__secret_config = secret_config
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def create_matrices(self):
        file_matrix_generator = FileMatrixGenerator(self.__secret_config)
        commit_matrix_generator = CommitMatrixGenerator(self.__secret_config)
        contributor_matrix_generator = ContributorMatrixGenerator(self.__secret_config)

        repos = [line.rstrip('\n') for line in open('repositories.txt')]

        for repo in repos:
            repository = self.__databaseService.getRepoByFullName(repo)
            repo_id = repository['id']
            file_matrix_generator.crate_matrix(repo_id)
            commit_matrix_generator.crate_matrix(repo_id)
            contributor_matrix_generator.create_matrix(repo_id)
            print ('\n')


with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
    config = yaml.load(ymlfile)

with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
    secret_config = yaml.load(ymlfile)

GM = GenerateMatrices(config, secret_config)
GM.create_matrices()