import os.path
import pandas
from sklearn.cluster import KMeans
import numpy as np
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scipy.stats import linregress

from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool import OUTPUT_DIR


class Clustering:

    def __init__(self):
        self.__databaseService = DatabaseService()

    def __fetch_data(self, data):
        headers = data.columns.values  # fetch headers
        repos = data.index.values  # fetch repos
        features = data._get_values  # fetch features.
        return headers, repos, features

    def k_means_clustering(self, file_name, k=5):

        data = pandas.read_csv(file_name, sep=';', index_col=0)  # read the csv file
        headers, repos, features = self.__fetch_data(data)

        kmeans = KMeans(n_clusters=k, random_state=0, n_init=200).fit(features)  # apply kmeans algorithm

        # form clusters
        clusters = []
        for i in range(0, k): # k cluster
            repo_list = []
            for j in range (0, len(kmeans.labels_)):  # a label for each repo.
                if i == kmeans.labels_[j]:  ## if repo label is equal to Cluster number
                    repo_list.append(repos[j])  # add repo to cluster i's list.
            clusters.append(repo_list)

        self.__export_results(kmeans, headers, clusters, file_name[:-4])  # avoid ".csv"

    def k_means_clustering_repostats(self, k=5):
        repo_stats = self.__databaseService.get_repo_stats()
        '''
        indexes = [repo["full_name"] for repo in repo_stats] #get repo full_names to be indexes in pandas df
        columns = []

        repo_stats_df = pandas.DataFrame(data=repo_stats, index=indexes, columns=columns)
        '''
        repo_stats_df = pandas.DataFrame.from_dict(repo_stats)
        repo_stats_df.set_index(keys="full_name", inplace=True)
        headers, repos, features = self.__fetch_data(repo_stats_df)

        kmeans = KMeans(n_clusters=k, random_state=0, n_init=200).fit(features)  # apply kmeans algorithm
        # form clusters
        clusters = []
        for i in range(0, k):  # k cluster
            repo_list = []
            for j in range(0, len(kmeans.labels_)):  # a label for each repo.
                if i == kmeans.labels_[j]:  ## if repo label is equal to Cluster number
                    repo_list.append(repos[j])  # add repo to cluster i's list.
            clusters.append(repo_list)

        self.__export_results(kmeans, headers, clusters, os.path.join(OUTPUT_DIR,"repo_stats"))

    def __export_results(self, kmeans, headers, clusters, file_name):

        clusters_file_path = file_name + "_clusters.txt"
        cluster_centers_file_path = file_name + "_cluster_centers.csv"
        # export clusters and cluster members.
        with open(clusters_file_path, "w") as out_file:
            for i in range(0, kmeans.n_clusters):
                out_file.write("Cluster " + str(i) + " size: " + str(len(clusters[i])) + "\n" )
                for repo in clusters[i]:
                    repo_lang = self.__databaseService.get_language_by_repo_full_name(repo)
                    out_file.write(str(repo) + " - " + str(repo_lang) + "\n")
                out_file.write("\n")

        # export cluster centers matrix.

        indexes = []
        for i in range(0, kmeans.n_clusters):
            indexes.append("Cluster " + str(i))

        cluster_centers_df = pandas.DataFrame(kmeans.cluster_centers_, index=indexes, columns=headers)
        cluster_centers_df.to_csv(cluster_centers_file_path, sep=';')

        return
