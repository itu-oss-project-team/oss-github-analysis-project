import os.path
import pandas
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

class Clustering:

    def __read_file(self, file_name):
        data = pandas.read_csv(file_name, sep=';') #read the csv file
        headers = [data._info_axis._data[1:]][0] #fetch headers
        repos = [row[0] for row in data._values] #fetch repo names
        features = [row[1:len(row)] for row in data._values] #fetch features.
        return headers, repos, features

    def k_means_clustering(self, file_name, k=5):
        headers, repos, features = self.__read_file(file_name)
        kmeans = KMeans(n_clusters=k, random_state=0, n_init=200).fit(features) #apply kmeans algorithm

        #form clusters
        clusters = []
        for i in range(0, k): # k cluster
            repo_list = []
            for j in range (0, len(kmeans.labels_)): # a label for each repo.
                if i == kmeans.labels_[j]: ## if repo label is equal to Cluster number
                    repo_list.append(repos[j]) # add repo to cluster i's list.
            clusters.append(repo_list)

        self.__exportResults(kmeans, headers, clusters, file_name)

    def __exportResults(self, kmeans, headers, clusters, file_name):

        #export clusters and cluster members.
        with open("clusters_" + file_name[:-4] + ".txt", "w") as out_file:
            for i in range(0, kmeans.n_clusters):
                out_file.write("Cluster " + str(i) + "\n")
                for repo in clusters[i]:
                    out_file.write(str(repo) + "\n")
                out_file.write("\n")

        #export cluster centers matrix.
        with open("cluster_centers_" + file_name, "w") as out_file:
            out_file.write(";")
            for header in headers:
                out_file.write(str(header) +";")
            out_file.write("\n")
            for i in range(0, kmeans.n_clusters):
                out_file.write("Cluster " + str(i) + ";")
                for center in kmeans.cluster_centers_[i]:
                    out_file.write(str(center) + ";")
                out_file.write("\n")
        return


clustering = Clustering()
clustering.k_means_clustering("file_metrics.csv", k=10)