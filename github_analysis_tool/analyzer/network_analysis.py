import collections
import numpy as np
import os.path
import pandas
from sklearn.feature_selection import *
from scipy.stats import linregress
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.analyzer.clustering import Clustering
from github_analysis_tool.analyzer.classification2 import Classification
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool.analyzer.analysis_utilities import AnalysisUtilities
from github_analysis_tool import OssConstants


class NetworkAnalysis:

    def __init__(self):
        self.classification = Classification()
        self.clustering = Clustering()
        self.database_service = DatabaseService()
        self.__analysis_utilities = AnalysisUtilities()

    def compute_cross_correlations(self, data, message=""):
        correlations = collections.OrderedDict()
        avg_correlations = collections.OrderedDict()
        metrics_to_be_removed = set()

        print(data.shape)
        for metric1 in data._series.keys():
            correlations[metric1] = collections.OrderedDict()
            corrs = []
            for metric2 in data._series.keys():
            # http://stackoverflow.com/questions/3949226/calculating-pearson-correlation-and-significance-in-python
                # corr = np.corrcoef(feature_vector_pair[0], feature_vector_pair[1])[0][1]
                # linear regression of two feature vectors.
                lin = linregress(data._series[metric1]._values, data._series[metric2]._values)
                correlations[metric1][metric2] = lin.rvalue
                corrs.append(lin.rvalue)

            avg_correlations[metric1] = np.mean(corrs)

        considered_metrics = set()
        metric_votes = {}
        for metric1 in correlations:
            considered_metrics.add(metric1)
            for metric2 in list(set(correlations.keys())-considered_metrics):
                if metric1 == metric2:
                    continue

                if abs(correlations[metric1][metric2]) > 0.50:
                    #print(metric1, metric2, str(correlations[metric1][metric2]))
                    if metric1 not in metric_votes:
                        metric_votes[metric1] = -1
                    else:
                        metric_votes[metric1] -= 1

                    if metric2 not in metric_votes:
                        metric_votes[metric2] = -1
                    else:
                        metric_votes[metric2] -= 1

                else:
                    if metric1 not in metric_votes:
                        metric_votes[metric1] = 1
                    else:
                        metric_votes[metric1] += 1

                    if metric2 not in metric_votes:
                        metric_votes[metric2] = 1
                    else:
                        metric_votes[metric2] += 1

        for metric in metric_votes:
            if(metric_votes[metric] < 0):
                metrics_to_be_removed.add(metric)

        new_data = data.drop(metrics_to_be_removed, axis=1)
        print(new_data.shape)

        output_file_path = os.path.join(OssConstants.OUTPUT_DIR, message + "correlation_matrix.csv")
        with open(output_file_path, "w") as output:
            output.write(";")
            for metric1 in correlations:
                output.write(metric1 + ";")
            output.write("\n")
            for metric1 in correlations:
                output.write(metric1 + ";")
                for metric2 in correlations[metric1]:
                    output.write(str(correlations[metric1][metric2]) + ";")
                output.write("\n")

        return new_data

    def generate_data_frame(self, file_path, file_path_2=None):
        data = pandas.read_csv(file_path, sep=';', index_col=0)  # read the csv file
        if file_path_2 is not None:
            data2 = pandas.read_csv(file_path_2, sep=';', index_col=0)
            new_headers_2 = data2.columns.values
            for i in range(0,len(new_headers_2)):
                new_headers_2[i] += "_2"

            data2.rename(columns=dict(zip(data2.columns, new_headers_2)), inplace=True)
            new_data_frame = pandas.concat([data, data2], axis=1)
            new_data_frame.dropna(inplace=True)
            return new_data_frame
        else:
            return data

    def do_classification(self, df, df_name, labelling_func, labelling_name):
        print("----> Classifying data set \"" + df_name + "\" with  \"" + labelling_name + " \" labels.")

        reduced_df = df[~df.index.duplicated()]  # Remove duplicate rows
        labels, row_labels, ignored_indexes = labelling_func(df=reduced_df)

        reduced_df = self.__analysis_utilities.drop_rows(reduced_df, ignored_indexes)  # Remove non-labeled rows/repos
        columns, _, feature_values = self.__analysis_utilities.decompose_df(reduced_df)

        k = 10
        k = k if (k <= len(columns)) else len(columns)  # Make sure that k is not larger than actual features
        # TODO: Obtain selected features and report them, maybe using column names
        # Reduce feature set by selecting best k features
        reduced_features = SelectKBest(chi2, k=k).fit_transform(feature_values, labels)

        training_set, test_set, training_labels, test_labels = \
            self.__analysis_utilities.split_data(reduced_features, labels, row_labels)

        out_folder_path = os.path.join(OssConstants.OUTPUT_DIR, "classification", labelling_name, df_name)
        if not os.path.exists(out_folder_path):
            os.makedirs(out_folder_path)

        self.classification.classify_with_knn(out_folder_path, training_set, test_set, training_labels, test_labels)

    def do_clustering(self, data_frame, df_name):
        # Try different clustering algorithms with different parameters
        print("----> Clustering data set: " + df_name)
        out_folder_path = os.path.join(OssConstants.OUTPUT_DIR, "clustering", df_name)
        if not os.path.exists(out_folder_path):
            os.makedirs(out_folder_path)

        for i in range(3, 9):
            print("------> MB K-Means clustering with # of clusters: " + str(i))
            self.clustering.minibatchs_k_means_clustering(out_folder_path, data_frame, number_of_clusters=i)

        for i in range(3, 9):
            print("------> K-Means clustering with # of clusters: " + str(i))
            self.clustering.k_means_clustering(out_folder_path, data_frame, number_of_clusters=i)
        for i in range(9, 15):
            print("------> Agglomerative clustering with # of clusters: " + str(i))
            self.clustering.agglomerative_clustering(out_folder_path, data_frame, number_of_clusters=i)
        for i in range(2, 8, 2):
            for j in range(2, 5):
                print("------> HDBSCAN clustering with min clusters: " + str(i) + ", min samples: " + str(j))
                self.clustering.hdbscan_clustering(out_folder_path, data_frame, min_cluster_size=i, min_samples=j)
