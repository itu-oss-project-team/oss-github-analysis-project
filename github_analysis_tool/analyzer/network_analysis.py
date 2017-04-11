import os.path
import pandas
import numpy as np
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scipy.stats import linregress

from github_analysis_tool.analyzer.clustering import Clustering
from github_analysis_tool.analyzer.classification import Classification
from github_analysis_tool import OUTPUT_DIR


class NetworkAnalysis:

    def __init__(self):
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

        '''
        for i in range(0, len(correlations_list)):
            print(feature_pair_list[i][0] + " - " + feature_pair_list[i][1] + " : "
                  + str(correlations_list[i]))
        '''
        for metric in sorted(avg_correlations, key=avg_correlations.get, reverse=True):
            print(metric, ":", avg_correlations[metric])

        # todo return the values
        return

    def do_classification(self, file_path):
        self.classification.knn(file_metrics_path, networkAnalysis.classification.set_star_labels)

    def do_clustering(self, file_path):
        k = 10
        self.clustering.k_means_clustering(file_metrics_path, k=k)
        self.clustering.k_means_clustering_repostats(k=k)

networkAnalysis = NetworkAnalysis()
file_metrics_path = os.path.join(OUTPUT_DIR, "file_metrics.csv")

# networkAnalysis.compute_cross_correlations(file_metrics_path)
# networkAnalysis.compute_repo_correlations(file_metrics_path)

networkAnalysis.do_classification(file_metrics_path)