import os.path
import pandas
from sklearn import neighbors
from sklearn.model_selection import *
from sklearn.feature_selection import *
from sklearn.svm import *
import numpy as np
import sys
import collections
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
        repo_stars_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_by_full_name(repo)
            stars = result["stargazers_count"]
            repo_stars_pair[repo] = stars
            if stars >= 100000:
                label = 0
            elif 50000 <= stars < 100000:
                label = 1
            elif 30000 <= stars < 50000:
                label = 2
            elif 20000 <= stars < 30000:
                label = 3
            elif 15000 <= stars < 20000:
                label = 4
            elif stars < 15000:
                label = 5

            labels.append(label)

        return labels, repo_stars_pair

    def set_no_of_filechanges_labels(self, repos):
        labels = []
        repo_no_of_filechanges_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_filechanges = result["no_of_file_changes"]
            repo_no_of_filechanges_pair[repo] = no_of_filechanges
            if no_of_filechanges >= 250000:
                label = 0
            elif 100000 <= no_of_filechanges < 250000:
                label = 1
            elif 60000 <= no_of_filechanges < 100000:
                label = 2
            elif 40000 <= no_of_filechanges < 60000:
                label = 3
            elif 30000 <= no_of_filechanges < 40000:
                label = 4
            elif 20000 <= no_of_filechanges < 30000:
                label = 5
            elif 10000 <= no_of_filechanges < 20000:
                label = 6
            elif 7000 <= no_of_filechanges < 10000:
                label = 7
            elif 5000 <= no_of_filechanges < 7000:
                label = 8
            elif 2000 <= no_of_filechanges < 5000:
                label = 9
            else:
                label = 10

            labels.append(label)

        return labels, repo_no_of_filechanges_pair

    def set_no_of_files_labels(self, repos):
        labels = []
        repo_no_of_files_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_files = result["no_of_changed_files"]
            repo_no_of_files_pair[repo] = no_of_files
            if no_of_files >= 30000:
                label = 0
            elif 10000 <= no_of_files < 30000:
                label = 1
            elif 5000 <= no_of_files < 10000:
                label = 2
            elif 3000 <= no_of_files < 5000:
                label = 3
            elif 2000 <= no_of_files < 3000:
                label = 4
            elif 1000 <= no_of_files < 2000:
                label = 5
            elif 500 <= no_of_files < 1000:
                label = 6
            elif 200 <= no_of_files < 500:
                label = 7
            else:
                label = 8

            labels.append(label)

        return labels, repo_no_of_files_pair

    def set_language_labels(self, repos):
        labels = []
        repo_language_pair = collections.OrderedDict()
        for repo in repos:
            language = self.__databaseService.get_language_by_repo_full_name(repo)
            repo_language_pair[repo] = language

            if language == "JavaScript" or language == "TypeScript" or language == "CoffeeScript":
                label = 0
            elif language == "Python":
                label = 1
            elif language == "Java":
                label = 2
            elif language == "Ruby":
                label = 3
            elif language == "Go":
                label = 4
            elif language == "C++" or language == "C":
                label = 5
            elif language == "Objective-C" or language == "Swift" or language == "Objective-C++":
                label = 6
            else:
                label = 7

            labels.append(label)

        return labels, repo_language_pair

    def set_no_of_commits_labels(self, repos):
        labels = []
        repo_no_of_commits_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_commits = result["no_of_commits"]
            repo_no_of_commits_pair[repo] = no_of_commits

            if no_of_commits >= 20000:
                label = 0
            elif 10000 <= no_of_commits < 20000:
                label = 1
            elif 5000 <= no_of_commits < 10000:
                label = 2
            elif 2500 <= no_of_commits < 5000:
                label = 3
            elif 1000 <= no_of_commits < 2500:
                label = 4
            elif 500 <= no_of_commits < 1000:
                label = 5
            else:
                label = 6

            labels.append(label)

        return labels, repo_no_of_commits_pair

    def knn(self, data, message, set_labels, k=15):
        headers, repos, features = self.__fetch_data(data)
        labels, repo_class_pair = set_labels(repos)

        no_of_classes = len(np.unique(labels))

        # new_features = self.__feature_selection(features, labels)
        # training_set, test_set, training_labels, test_labels = train_test_split(new_features, labels, test_size=0.3)

        classifier = neighbors.KNeighborsClassifier(k, weights='distance')
        # classifier.fit(training_set, training_labels)
        # scores = cross_val_score(classifier, features, labels, cv=5)
        predicted = cross_val_predict(classifier, features, labels, cv=5)

        success = 0
        fail = 0

        result_classes = [[]*no_of_classes for _ in range(no_of_classes + 1)]
        i = 0
        for repo, label in repo_class_pair.items():
            print(repo, label, " actual: ", labels[i], " predicted: ", predicted[i])
            if labels[i] == predicted[i]:
                success += 1
            else:
                fail += 1

            result_classes[predicted[i]].append((repo, labels[i]))
            i += 1

        print(success, fail, success/(success+fail))
        output_path = os.path.join(OUTPUT_DIR, message + ".txt")

        with open(output_path, "w") as output_file:
            output_file.write("Success: " + str(success) + " Fail: " + str(fail))
            output_file.write( " : " + str(success/(success+fail)) + "\n\n")
            for i in range(0, len(result_classes)):
                output_file.write("Class " + str(i) + "\n" + "\n")
                for element in result_classes[i]:
                    output_file.write(str(element[0]) + " - " + str(element[1]) + "\n")
                output_file.write("\n")

        '''
        success = 0
        fail = 0
        for i in range(0, len(test_set)):
            result = classifier.predict(test_set[i])
            print("actual: ", labels[i], "result: ", result[0])
            if result[0] == labels[i]:
                success += 1
            else:
                fail += 1

        print(success, fail)
        '''

    def svc(self, data, message, set_labels):
        headers, repos, features = self.__fetch_data(data)
        labels, repo_class_pair = set_labels(repos)

        no_of_classes = len(np.unique(labels))

        classifier = SVC(kernel='rbf')
        new_features = self.__feature_selection(features, labels)
        # training_set, test_set, training_labels, test_labels = train_test_split(new_features, labels, test_size=0.3)

        predicted = cross_val_predict(classifier, new_features, labels, cv=5)
        success = 0
        fail = 0

        result_classes = [[] * no_of_classes for _ in range(no_of_classes+1)]
        i = 0
        for repo, label in repo_class_pair.items():
            print(repo, label, " actual: ", labels[i], " predicted: ", predicted[i])
            if labels[i] == predicted[i]:
                success += 1
            else:
                fail += 1

            result_classes[predicted[i]].append((repo, labels[i]))
            i += 1

        print(success, fail, success / (success + fail))
        output_path = os.path.join(OUTPUT_DIR, message + ".txt")

        with open(output_path, "w") as output_file:
            output_file.write("Success: " + str(success) + " Fail: " + str(fail))
            output_file.write(" : " + str(success / (success + fail)) + "\n\n")
            for i in range(0, len(result_classes)):
                output_file.write("Class " + str(i) + "\n" + "\n")
                for element in result_classes[i]:
                    output_file.write(str(element[0]) + " - " + str(element[1]) + "\n")
                output_file.write("\n")

    def __feature_selection(self, features, labels):
        sel = SelectKBest(chi2, k=10)
        new_features = sel.fit_transform(features, labels)
        return new_features
