import os.path
import sys
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans, AgglomerativeClustering, MiniBatchKMeans
import hdbscan

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool.services.db_column_constants import Columns
from github_analysis_tool import OssConstants


class AnalysisUtilities:
    def __init__(self):
        self.__database_service = DatabaseService()

    def normalize_df(self, df):
        return (df-df.min())/(df.max()-df.min())

    def decompose_df(self, df):
        headers = df.columns.values  # fetch headers
        indexes = df.index.values  # fetch repos
        values = df._get_values  # fetch features.
        return headers, indexes, values

    def __generate_repo_stats_csv(self):
        repos = self.__database_service.get_all_repos()
        repos = [repo[Columns.Repo.full_name] for repo in repos]
        repo_stats = {}

        for repo in repos:
            repo_stat = self.__database_service.get_repo_stats(repo)
            if repo_stat is not None:
                repo_stats[repo] = repo_stat
        repo_stats_df = pd.DataFrame().from_dict(repo_stats, orient='index')
        repo_stats_df.to_csv(OssConstants.REPO_STATS_PATH, sep=";")
        return repo_stats_df

    def get_repo_stats_df(self, refresh=False):
        if not os.path.exists(OssConstants.REPO_STATS_PATH) or refresh:
            return self.__generate_repo_stats_csv() # There is no repo stats CSV or we want newest stats
        else:
            return pd.read_csv(OssConstants.REPO_STATS_PATH, sep=";", index_col=0)

    def merge_dfs_on_indexes(self, left_df, right_df, left_suffix="l", right_suffix="r"):
        """
        This function merges two data frame on indexes by appending columns,
            discards indexes that does not exists on both data frames
        :param left_df: A pandas data frame
        :param right_df: A pandas data frame
        :param left_suffix: Suffix to identify left dfs columns when overlapping
        :param right_suffix: Suffix to identify right dfs columns when overlapping
        :return: A pandas data frame which is merge of left_df and right_df
        """
        return left_df.join(right_df, how='inner', lsuffix=left_suffix, rsuffix=right_suffix)

    def split_data(self, features, labels, row_labels):
        """
        
        :param features: Features matrix to be split
        :param labels: List of labels
        :param row_labels: List of {<key>:<label>} pairs
        :return: training and test set as pandas df and their labels 
                as a list which has same order with these df's rows
        """
        training_set = []
        test_set = []
        training_labels = []
        test_labels = []

        # count number of instances in each class
        class_counts = {}
        for repo in row_labels:
            if row_labels[repo] not in class_counts:
                class_counts[row_labels[repo]] = 1
            else:
                class_counts[row_labels[repo]] += 1

        # compute split sizes logarithmically for each class
        split_sizes = {}
        for class_label in class_counts:
            label_count = class_counts[class_label]
            if 1 < label_count < 10:
                split_size = np.rint(0.50 * label_count)
            elif 10 <= label_count < 20:
                split_size = np.rint(0.60 * label_count)
            elif label_count >= 20:
                split_size = np.rint(0.70 * label_count)
            else:
                split_size = label_count

            split_sizes[class_label] = split_size

        # split data to test-train according to split_sizes.
        class_counters = {}
        i = 0
        for repo in row_labels:
            class_label = row_labels[repo]
            if class_label not in class_counters:
                class_counters[class_label] = 1
            else:
                class_counters[class_label] += 1

            if class_counters[class_label] <= split_sizes[class_label]:
                training_labels.append(labels[i])
                training_set.append(features[i])
            else:
                test_labels.append(labels[i])
                test_set.append(features[i])

            i += 1

        return training_set, test_set, training_labels, test_labels

    def drop_rows(self, pd_data, ignored_indexes):
        # Let's make sure that we will not try to remove non-existing indexes in pd_data
        to_drop_indexes = [index for index in ignored_indexes if index in pd_data.index]
        return pd_data.drop(to_drop_indexes)

