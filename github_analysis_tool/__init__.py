import os
import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(ROOT_DIR , "outputs")


class OssConstants:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")
    FILE_METRICS_PATH = os.path.join(OUTPUT_DIR, "file_metrics.csv")
    COMMIT_METRICS_PATH = os.path.join(OUTPUT_DIR, "commit_metrics.csv")
    REPO_STATS_PATH = os.path.join(OUTPUT_DIR, "repo_stats.csv")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

with open(os.path.join(ROOT_DIR, os.pardir, 'config.yaml'), 'r') as ymlfile:
    config = yaml.load(ymlfile)

with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
    secret_config = yaml.load(ymlfile)
