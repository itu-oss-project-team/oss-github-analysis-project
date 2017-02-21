import yaml
import os.path
from file_matrix_generator import FileMatrixGenerator
from commit_matrix_generator import CommitMatrixGenerator

with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
    config = yaml.load(ymlfile)

with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
    secret_config = yaml.load(ymlfile)


file_matrix_generator = FileMatrixGenerator(secret_config)
commit_matrix_generator = CommitMatrixGenerator(secret_config)

file_matrix_generator.crate_matrix(71659875)    #  oss-github-analysis-project
commit_matrix_generator.crate_matrix(71659875)  #  oss-github-analysis-project