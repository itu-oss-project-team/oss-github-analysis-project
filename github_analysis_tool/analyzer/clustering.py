import os.path
import sys
import pandas
from sklearn.cluster import KMeans, AgglomerativeClustering, MiniBatchKMeans
import hdbscan

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.services.database_service import DatabaseService


class Clustering:

    def __init__(self):
        self.__databaseService = DatabaseService()

    def __fetch_data(self, data):
        headers = data.columns.values  # fetch headers
        repos = data.index.values  # fetch repos
        features = data._get_values  # fetch features.
        return headers, repos, features

    def k_means_clustering(self, out_path, pd_data, number_of_clusters):
        headers, repos, features = self.__fetch_data(pd_data)

        kmeans = KMeans(n_clusters=number_of_clusters, random_state=0, n_init=200).fit(features)  # apply kmeans algorithm

        # form clusters
        clusters = []
        for i in range(0, number_of_clusters): # k cluster
            repo_list = []
            for j in range (0, len(kmeans.labels_)):  # a label for each repo.
                if i == kmeans.labels_[j]:  # if repo label is equal to Cluster number
                    repo_list.append(repos[j])  # add repo to cluster i's list.
            clusters.append(repo_list)

        out_file_path = os.path.join(out_path, "kmeans_noOfClusters" + str(number_of_clusters))
        self.__export_k_means_results(kmeans, headers, clusters, out_file_path)  # avoid ".csv"

    def agglomerative_clustering(self, out_path, pd_data, number_of_clusters):
        headers, repos, features = self.__fetch_data(pd_data)

        agglomerative_clustering = AgglomerativeClustering(n_clusters=number_of_clusters, linkage="complete")
        agglomerative_clustering.fit(features)

        # form clusters
        clusters = []
        for i in range(0, number_of_clusters):  # k cluster
            repo_list = []
            for j in range(0, len(agglomerative_clustering.labels_)):  # a label for each repo.
                if i == agglomerative_clustering.labels_[j]:  # if repo label is equal to Cluster number
                    repo_list.append(repos[j])  # add repo to cluster i's list.
            clusters.append(repo_list)

        out_file_path = os.path.join(out_path, "agglomerative_noOfClusters" + str(number_of_clusters))
        self.__export_agglomerative_results(agglomerative_clustering, clusters, out_file_path)

    def hdbscan_clustering(self, out_path, pd_data, min_cluster_size, min_samples):
        headers, repos, features = self.__fetch_data(pd_data)

        hdbscan_clustering = hdbscan.HDBSCAN(min_cluster_size, min_samples)
        hdbscan_clustering.fit(features)

        # form clusters
        clusters = []
        for i in range(0, hdbscan_clustering.labels_.max()):  # k cluster
            repo_list = []
            for j in range(0, len(hdbscan_clustering.labels_)):  # a label for each repo.
                if i == hdbscan_clustering.labels_[j]:  # if repo label is equal to Cluster number
                    repo_list.append(repos[j])  # add repo to cluster i's list.
            clusters.append(repo_list)

        out_file_path = os.path.join(out_path, "hdbscan_minSize" + str(min_cluster_size) + "_minSamples" + str(min_samples))
        self.__export_hdbscan_results(hdbscan_clustering, clusters, out_file_path)

    def minibatchs_k_means_clustering(self, out_path, pd_data, number_of_clusters):
        headers, repos, features = self.__fetch_data(pd_data)

        mb_kmeans = MiniBatchKMeans(n_clusters=number_of_clusters)
        mb_kmeans.fit(features)

        clusters = []
        for i in range(0, number_of_clusters): # k cluster
            repo_list = []
            for j in range (0, len(mb_kmeans.labels_)):  # a label for each repo.
                if i == mb_kmeans.labels_[j]:  # if repo label is equal to Cluster number
                    repo_list.append(repos[j])  # add repo to cluster i's list.
            clusters.append(repo_list)
        out_file_path = os.path.join(out_path, "mb_kmeans_noOfClusters" + str(number_of_clusters))
        self.__export_k_means_results(mb_kmeans, headers, clusters, out_file_path)  # avoid ".csv"


    def __export_k_means_results(self, clusterer, headers, clusters, file_path):

        clusters_file_path = file_path + "_clusters.txt"
        cluster_centers_file_path = file_path + "_cluster_centers.csv"
        # export clusters and cluster members.
        with open(clusters_file_path, "w") as out_file:
            for i in range(0, clusterer.n_clusters):
                out_file.write("Cluster " + str(i) + " size: " + str(len(clusters[i])) + "\n")
                for repo in clusters[i]:
                    repo_lang = self.__databaseService.get_language_by_repo_full_name(repo)
                    out_file.write(str(repo) + " - " + str(repo_lang) + "\n")
                out_file.write("\n")

        # export cluster centers matrix.
        indexes = []
        for i in range(0, clusterer.n_clusters):
            indexes.append("Cluster " + str(i))

        cluster_centers_df = pandas.DataFrame(clusterer.cluster_centers_, index=indexes, columns=headers)
        cluster_centers_df.to_csv(cluster_centers_file_path, sep=';')

        return

    def __export_agglomerative_results(self, clusterer, clusters, file_path):
        clusters_file_path = file_path + ".txt"
        with open(clusters_file_path, "w") as out_file:
            for i in range(0, clusterer.n_clusters):
                out_file.write("Cluster " + str(i) + " size: " + str(len(clusters[i])) + "\n" )
                for repo in clusters[i]:
                    repo_lang = self.__databaseService.get_language_by_repo_full_name(repo)
                    out_file.write(str(repo) + " - " + str(repo_lang) + "\n")
                out_file.write("\n")

    def __export_hdbscan_results(self, clusterer, clusters, file_path):
        clusters_file_path = file_path + ".txt"
        with open(clusters_file_path, "w") as out_file:
            for i in range(-1, clusterer.labels_.max()):
                out_file.write("Cluster " + str(i) + " size: " + str(len(clusters[i])) + "\n" )
                for repo in clusters[i]:
                    repo_lang = self.__databaseService.get_language_by_repo_full_name(repo)
                    out_file.write(str(repo) + " - " + str(repo_lang) + "\n")
                out_file.write("\n")