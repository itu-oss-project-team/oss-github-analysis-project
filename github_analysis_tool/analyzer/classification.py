import os.path
import pandas
from sklearn import neighbors
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool import OUTPUT_DIR


class Classification:

    def __init__(self):
        self.__databaseService = DatabaseService()

    def __fetch_data(self, data):
        headers = data.columns.values  # fetch headers
        repos = data.index.values  # fetch repos
        features = data._get_values  # fetch features.
        return headers, repos, features

    def set_star_labels(self, repos):
        labels = []
        repo_stars_pair = {}
        for repo in repos:
            result = self.__databaseService.get_repo_by_full_name(repo)
            stars = result["stargazers_count"]
            repo_stars_pair[repo] = stars
            if stars >= 100000:
                label = 1
            elif 50000 <= stars < 100000:
                label = 2
            elif 40000 <= stars < 50000:
                label = 3
            elif 30000 <= stars < 40000:
                label = 4
            elif 20000 <= stars < 30000:
                label = 5
            elif 15000 <= stars < 20000:
                label = 6
            elif stars < 15000:
                label = 7

            labels.append(label)

        return labels, repo_stars_pair

    def set_no_of_files_labels(self, repos):
        labels = []
        repo_no_of_files_pair = {}
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_files = result["no_of_changed_files"]
            repo_no_of_files_pair[repo] = no_of_files
            if no_of_files >= 30000:
                label = 1
            elif 10000 <= no_of_files < 30000:
                label = 2
            elif 5000 <= no_of_files < 10000:
                label = 3
            elif 3000 <= no_of_files < 5000:
                label = 4
            elif 2000 <= no_of_files < 3000:
                label = 5
            elif 1000 <= no_of_files < 2000:
                label = 6
            elif 500 <= no_of_files < 1000:
                label = 7
            elif 300 <= no_of_files < 500:
                label = 8
            elif 100 <= no_of_files < 300:
                label = 9
            elif 50 <= no_of_files < 100:
                label = 10
            else:
                label = 11

            labels.append(label)

        return labels, repo_no_of_files_pair

    def knn(self, file_name, set_labels, k=3):
        data = pandas.read_csv(file_name, sep=';', index_col=0)  # read the csv file
        headers, repos, features = self.__fetch_data(data)
        labels, repo_stars_pair = set_labels(repos)

        training_set = []
        training_labels = []
        test_set = []
        test_labels = []
        for i in range(0, len(features)):
            if i % 2 == 0:
                test_set.append(features[i])
                test_labels.append(labels[i])
            else:
                training_set.append(features[i])
                training_labels.append(labels[i])

        classifier = neighbors.KNeighborsClassifier(3, weights='distance')
        classifier.fit(training_set, training_labels)
        success = 0
        fail = 0
        for i in range(0, len(test_set)):
            result = classifier.predict(test_set[i])
            print("actual: ", labels[i], "result: ", result)
            if result[0] == labels[i]:
                success += 1
            else:
                fail += 1

        print(success, fail)
