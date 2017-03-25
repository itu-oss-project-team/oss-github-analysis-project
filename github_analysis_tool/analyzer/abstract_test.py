import os

import yaml

from github_analysis_tool.analyzer.file_based_analyzer import FileBasedAnalyzer

with open(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'config.yaml'), 'r') as ymlfile:
    config = yaml.load(ymlfile)

with open(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
    secret_config = yaml.load(ymlfile)

fba = FileBasedAnalyzer("file", secret_config)
fba.analyze_repo("itu-oss-project-team/oss-github-analysis-project")