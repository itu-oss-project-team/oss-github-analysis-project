import os.path

import pandas
import yaml
from sklearn.cluster import KMeans

from github_analysis_tool.services.database_service import DatabaseService


class Clustering:

    def __init__(self, secret_config):
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def __fetch_data(self, data):
        headers = data.columns.values #fetch headers
        repos = data.index.values # fetch repos
        features = data._get_values #fetch features.
        return headers, repos, features

    def k_means_clustering(self, file_name, k=5):
        directory_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(directory_path, file_name)

        data = pandas.read_csv(file_path, sep=';', index_col=0) #read the csv file
        headers, repos, features = self.__fetch_data(data)

        kmeans = KMeans(n_clusters=k, random_state=0, n_init=200).fit(features) #apply kmeans algorithm

        #form clusters
        clusters = []
        for i in range(0, k): # k cluster
            repo_list = []
            for j in range (0, len(kmeans.labels_)): # a label for each repo.
                if i == kmeans.labels_[j]: ## if repo label is equal to Cluster number
                    repo_list.append(repos[j]) # add repo to cluster i's list.
            clusters.append(repo_list)

        self.__exportResults(kmeans, headers, clusters, file_name[:-4]) #avoid ".csv"

    def k_means_clustering_repostats(self, k=5):
        repo_stats = self.__databaseService.getRepoStats()
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

        self.__exportResults(kmeans, headers, clusters, "repo_stats")

    def __exportResults(self, kmeans, headers, clusters, file_name):

        head_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #get the root directory
        clusters_file_path = os.path.join(head_dir, 'outputs', 'clusters_' + file_name + '.txt')
        cluster_centers_file_path = os.path.join(head_dir, 'outputs', 'cluster_centers_' + file_name + '.csv')
        #export clusters and cluster members.
        with open(clusters_file_path, "w") as out_file:
            for i in range(0, kmeans.n_clusters):
                out_file.write("Cluster " + str(i) + " size: " + str(len(clusters[i])) + "\n" )
                for repo in clusters[i]:
                    repo_lang = self.__databaseService.getLanguageByRepoFullName(repo)
                    out_file.write(str(repo) + " - " + str(repo_lang) + "\n")
                out_file.write("\n")

        #export cluster centers matrix.

        indexes = []
        for i in range(0, kmeans.n_clusters):
            indexes.append("Cluster " + str(i))

        cluster_centers_df = pandas.DataFrame(kmeans.cluster_centers_, index=indexes, columns=headers)
        cluster_centers_df.to_csv(cluster_centers_file_path, sep=';')

        return

with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
    secret_config = yaml.load(ymlfile)

clustering = Clustering(secret_config)
clustering.k_means_clustering("file_metrics.csv", k=5)
clustering.k_means_clustering_repostats(k=10)