import os.path
import pandas
import numpy as np
import sys
from scipy.stats import linregress
import collections

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.analyzer.clustering import Clustering
from github_analysis_tool.analyzer.classification import Classification
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool import OUTPUT_DIR


class NetworkAnalysis:

    def __init__(self):
        #repo_languages_data = pandas.read_csv(os.path.join(OUTPUT_DIR, "repo_languages.csv"), sep=';', index_col=0, header=None)
        #self.repo_languages = repo_languages_data.to_dict()[1]
        self.classification = Classification()
        self.clustering = Clustering()

    def __fetch_data(self, data):
        headers = data.columns.values  # fetch headers
        repos = data.index.values  # fetch repos
        features = data._get_values  # fetch features.
        return headers, repos, features

    def compute_cross_correlations(self, file_name):
        data = pandas.read_csv(file_name, sep=';', index_col=0)  # read the csv file

        correlations = collections.OrderedDict()
        avg_correlations = collections.OrderedDict()

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

        output_file_path = file_name[:-4] + "_correlation_matrix.csv"
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
        return

    def do_classification(self, file_path):
        data = pandas.read_csv(file_path, sep=';', index_col=0)  # read the csv file
        self.classification.knn(data, file_path, "knn_star_classification", self.classification.set_star_labels)
        self.classification.knn(data, file_path, "knn_language_classification", self.classification.set_language_labels)
        self.classification.knn(data, file_path, "knn_no_of_files_classification", self.classification.set_no_of_files_labels)
        self.classification.knn(data, file_path, "knn_no_of_file_changes_classification", self.classification.set_no_of_filechanges_labels)
        self.classification.knn(data, file_path, "knn_no_of_commits_classification", self.classification.set_no_of_commits_labels)
        return

    def do_clustering(self, data_frame, data_set_name):
        # Try different clustering algorithms with different parameters
        print("----> Analyzing data set: " + data_set_name)
        out_path = os.path.join(OUTPUT_DIR, "clustering", data_set_name)
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        for i in range(3, 9):
            print("------> K-Means clustering with # of clusters: " + str(i))
            self.clustering.k_means_clustering(out_path, data_frame, number_of_clusters=i)
        for i in range(9, 15):
            print("------> Agglomerative clustering with # of clusters: " + str(i))
            self.clustering.agglomerative_clustering(out_path, data_frame, number_of_clusters=i)
        for i in range(2, 8, 2):
            for j in range(2, 5):
                print("------> HDBSCAN clustering with min clusters: " + str(i) + ", min samples: " + str(j))
                self.clustering.hdbscan_clustering(out_path, data_frame, min_cluster_size=i, min_samples=j)

networkAnalysis = NetworkAnalysis()

file_metrics_path = os.path.join(OUTPUT_DIR, "file_metrics.csv")
commit_metrics_path = os.path.join(OUTPUT_DIR, "commit_metrics.csv")

networkAnalysis.compute_cross_correlations(file_metrics_path)
networkAnalysis.compute_cross_correlations(commit_metrics_path)

networkAnalysis.do_classification(file_metrics_path)
networkAnalysis.do_classification(commit_metrics_path)
