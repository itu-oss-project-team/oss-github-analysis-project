import os.path
import pandas
import numpy as np
import sys
from scipy.stats import linregress

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.analyzer.clustering import Clustering
from github_analysis_tool.analyzer.classification import Classification
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool import OUTPUT_DIR


class NetworkAnalysis:

    def __init__(self):
        repo_languages_data = pandas.read_csv(os.path.join(OUTPUT_DIR, "repo_languages.csv"), sep=';', index_col=0, header=None)
        self.repo_languages = repo_languages_data.to_dict()[1]
        self.classification = Classification()
        self.clustering = Clustering()

    def __fetch_data(self, data):
        headers = data.columns.values  # fetch headers
        repos = data.index.values  # fetch repos
        features = data._get_values  # fetch features.
        return headers, repos, features

    def compute_repo_correlations(self, file_name):
        data = pandas.read_csv(file_name, sep=';', index_col=0)  # read the csv file
        headers, repos, features = self.__fetch_data(data)

        for i in range(0, len(features)):
            corrs = []
            for j in range(i, len(features)):
                lin = linregress(features[i], features[j])
                print(repos[i], repos[j], str(lin.rvalue))

    def compute_cross_correlations(self, file_name):
        data = pandas.read_csv(file_name, sep=';', index_col=0)  # read the csv file
        headers, repos, features = self.__fetch_data(data)

        feature_pair_list = []
        correlations_list = []
        avg_correlations = {}
        for metric1 in data._series.keys():
            corrs = []
            for metric2 in data._series.keys():
                if metric1 == metric2:
                    continue

                #tuple of two vectors
                feature_vector_pair = (data._series[metric1]._values, data._series[metric2]._values)
                feature_pair = (str(metric1), str(metric2))
                feature_pair_list.append(feature_pair)

                # http://stackoverflow.com/questions/3949226/calculating-pearson-correlation-and-significance-in-python
                # corr = np.corrcoef(feature_vector_pair[0], feature_vector_pair[1])[0][1]
                # linear regression of two feature vectors.
                lin = linregress(data._series[metric1]._values, data._series[metric2]._values)
                correlations_list.append(lin.rvalue)
                corrs.append(lin.rvalue)

            avg_correlations[metric1] = np.mean(corrs)


        for i in range(0, len(correlations_list)):
            print(feature_pair_list[i][0] + " - " + feature_pair_list[i][1] + " : "
                  + str(correlations_list[i]))

        '''
        with open(file_name[:-4] + "_avg_correlations.txt", "w") as output_file:
            for metric in sorted(avg_correlations, key=avg_correlations.get, reverse=True):
                output_file.write(metric + " : " + str(avg_correlations[metric]) + "\n")
                print(metric, ":", avg_correlations[metric])
        '''
        # todo return the values
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

# networkAnalysis.compute_cross_correlations(file_metrics_path)
# networkAnalysis.compute_cross_correlations(commit_metrics_path)

networkAnalysis.do_classification(file_metrics_path)
networkAnalysis.do_classification(commit_metrics_path)
