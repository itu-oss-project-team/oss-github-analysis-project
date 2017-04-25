import os.path
import sys
import numpy as np
import pandas as pd
import random
import collections

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

    def __count_classes(self, labels):
        # count number of instances in each class
        class_counts = {}
        for label in labels:
            if label not in class_counts:
                class_counts[label] = 1
            else:
                class_counts[label] += 1

        return class_counts

    def split_data(self, observations, labels, row_labels):
        """
        
        :param observations: Features matrix to be split
        :param labels: List of labels
        :param row_labels: List of {<key>:<label>} pairs
        :return: training and test set as pandas df and their labels 
                as a list which has same order with these df's rows
        """
        training_set = []
        test_set = []
        training_labels = []
        test_labels = []

        class_counts = self.__count_classes(labels)
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
                training_set.append(observations[i])
            else:
                test_labels.append(labels[i])
                test_set.append(observations[i])

            i += 1

        return training_set, test_set, training_labels, test_labels

    def drop_rows(self, pd_data, ignored_indexes):
        # Let's make sure that we will not try to remove non-existing indexes in pd_data
        to_drop_indexes = [index for index in ignored_indexes if index in pd_data.index]
        return pd_data.drop(to_drop_indexes)

    def get_biasing_labels(self, labels):
        biasing_labels = []
        class_counts = self.__count_classes(labels)
        total_labels = len(labels)

        for class_label in class_counts:
            if class_counts[class_label] > 0.50*total_labels:
                biasing_labels.append(class_label)

        return biasing_labels

    def undersampling(self, dataset, labels, biasing_labels, size, seed):
        random.seed(seed) # seed the random
        observation_label_pair_list = list(zip(dataset, labels)) # associate dataset rows with labels.

        sampling_list = dict.fromkeys(biasing_labels, []) #create a dictionary for each biasing_label.
        non_sampling_list = []

        for observation_label_pair in observation_label_pair_list:
            if observation_label_pair[1] in biasing_labels: # if this label is in biasing_labels
                sampling_list[observation_label_pair[1]].append(observation_label_pair) #add to sampling list
            else:
                non_sampling_list.append(observation_label_pair) #add to nonsampling list

        dataset, labels = zip(*non_sampling_list) #unzip back the values which will not be eliminated.

        for biasing_label in sampling_list:
            random.shuffle(sampling_list[biasing_label]) # shuffle the list
            sampling_list_dataset, sampling_list_labels = zip(*sampling_list[biasing_label])
            # take first size element.
            dataset = sampling_list_dataset[:size] + dataset
            labels = sampling_list_labels[:size] + labels

        return dataset, labels

    def export_confusion_matrix(self, out_file_pre_path, conf_matrix, label_names, success, fail):
        out_file_path = out_file_pre_path + "_confusionMatrix.csv"
        with open(out_file_path, "w") as output_file:
            output_file.write(";")
            for i in range(0, len(label_names)):
                output_file.write(str(label_names[i]) + ";")
            output_file.write("\n")
            for row in range(0, len(conf_matrix)):
                output_file.write(str(label_names[row]) + ";")
                for col in range(0, len(conf_matrix[row])):
                    output_file.write(str(conf_matrix[row][col]) + ";")
                output_file.write("\n")

            output_file.write(";")
            for col in range(0, len(conf_matrix[0])):
                output_file.write(";")
            output_file.write(str(success) + ";" + str(fail) + ";")
            output_file.write(str(success/(success+fail)) + ";\n")

    def compute_sampling_confusion_matrix(self, conf_matrices, out_file_pre_path, label_names, sampled_scores):
        print("------> Total")
        total_labels = len(label_names)
        total_conf_matrix = np.zeros((total_labels, total_labels), dtype=np.int32)
        total_success = 0
        total_fail = 0

        for sampled_score in sampled_scores:
            total_success += sampled_score[0]
            total_fail += sampled_score[1]

        for conf_matrix in conf_matrices:
            total_conf_matrix = np.add(total_conf_matrix, conf_matrix)

        print(total_success, total_fail, (total_success/(total_success+total_fail)))
        print(total_conf_matrix)
        self.export_confusion_matrix(out_file_pre_path, total_conf_matrix,
                                     label_names, total_success, total_fail)
