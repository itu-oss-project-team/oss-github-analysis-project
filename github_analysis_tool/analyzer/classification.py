import os.path
import pandas
from sklearn import neighbors
from sklearn.model_selection import *
from sklearn.feature_selection import *
from sklearn.svm import *
from sklearn.metrics import confusion_matrix
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

    def set_star_labels(self, data):
        headers, repos, features = self.__fetch_data(data)
        labels = []
        repo_stars_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_by_full_name(repo)
            stars = result["stargazers_count"]
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

            repo_stars_pair[repo] = label

            labels.append(label)

        return labels, repo_stars_pair

    def set_no_of_filechanges_labels(self, data):
        headers, repos, features = self.__fetch_data(data)
        labels = []
        repo_no_of_filechanges_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_filechanges = result["no_of_file_changes"]
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

            repo_no_of_filechanges_pair[repo] = label
            labels.append(label)

        return labels, repo_no_of_filechanges_pair

    def set_no_of_files_labels(self, data):
        headers, repos, features = self.__fetch_data(data)
        labels = []
        repo_no_of_files_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_files = result["no_of_changed_files"]
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

            repo_no_of_files_pair[repo] = label
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

    def set_no_of_commits_labels(self, data):
        headers, repos, features = self.__fetch_data(data)
        labels = []
        repo_no_of_commits_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_commits = result["no_of_commits"]

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

            repo_no_of_commits_pair[repo] = label
            labels.append(label)

        return labels, repo_no_of_commits_pair

    def trim_data_with_language(self, data, threshold = 3):
        headers, repos, features = self.__fetch_data(data)
        language_counts = {}
        repo_languages = {}

        # Which languages should be treated as one
        language_groups = [["JavaScript", "TypeScript", "CoffeeScript"]]

        # {"language_a" : "language_a,language_b,language_c"}
        language_mapping = {}

        # Fill language mapping
        for language_group in language_groups:
            group_label = '-'.join(language_group)
            for language in language_group:
                language_mapping[language] = group_label

        # Let's find out languages of all repos and repo counts of languages with taking care of lang groups
        for repo in repos:
            repo_lang = self.__databaseService.get_language_by_repo_full_name(repo)
            if repo_lang in language_mapping:
                # Take language group label
                repo_languages[repo] = language_mapping[repo_lang]
            else:
                repo_languages[repo] = repo_lang

            if repo_languages[repo] not in language_counts:
                language_counts[repo_languages[repo]] = 1
            else:
                language_counts[repo_languages[repo]] += 1

        # Find languages with repo counts lower than our thereshold
        ignored_languages = [language for language in language_counts if language_counts[language] < threshold]
        # Find repos with ignored languages
        ignored_repos = [repo for repo in repos if repo_languages[repo] in ignored_languages]

        # We should no longer keep language information of ignored repos
        for repo in ignored_repos:
            repo_languages.pop(repo, None)

        # We should no longer keep metrics of ignored repos
        new_data = data = data.drop(ignored_repos)

        labels = []
        for repo in repo_languages:
            labels.append(repo_languages[repo])
        return new_data, labels, repo_languages

    def knn(self, data, message, set_labels, k=5):
        data, labels, repo_class_pair = set_labels(data)
        headers, repos, features = self.__fetch_data(data)

        new_features = self.__feature_selection(features, labels, 8)
        training_set, test_set, training_labels, test_labels = self.__split_data(features, repos, labels, repo_class_pair)
        knn_classifier = neighbors.KNeighborsClassifier(k, weights='distance')
        knn_classifier.fit(training_set, training_labels)
        predicted = knn_classifier.predict(test_set)
        # scores = cross_val_score(classifier, features, labels, cv=5)
        # predicted = cross_val_predict(classifier, features, labels, cv=5)

        '''
        success = 0
        fail = 0
        for i in range(0, len(test_labels)):
            print("actual: ", test_labels[i], "result: ", predicted[i])
            if predicted[i] == test_labels[i]:
                success += 1
            else:
                fail += 1

        print(success, fail, success/(success+fail))
        '''

        output_path = os.path.join(OUTPUT_DIR, message + ".csv")

        self.__export_confusion_matrix(test_labels, predicted, output_path)


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

    def __feature_selection(self, features, labels, k=10):
        sel = SelectKBest(chi2, k=k)
        new_features = sel.fit_transform(features, labels)
        return new_features

    def __split_data(self, features, repos, labels, repo_class_pairs):
        training_set = []
        test_set = []
        training_labels = []
        test_labels = []

        # count number of instances in each class
        class_counts = {}
        for repo in repo_class_pairs:
            if repo_class_pairs[repo] not in class_counts:
                class_counts[repo_class_pairs[repo]] = 1
            else:
                class_counts[repo_class_pairs[repo]] += 1

        # compute split sizes logarithmically for each class
        split_sizes = {}
        for class_label in class_counts:
            label_count = class_counts[class_label]
            if 1 < label_count <= 10:
                split_size = np.math.floor(1.4 * label_count / np.log2(label_count))
            elif label_count > 10:
                split_size = np.math.ceil(0.50*label_count / (np.log10(label_count)))
            else:
                split_size = label_count

            print(class_label, split_size, class_counts[class_label])
            split_sizes[class_label] = split_size

        #split data to test-train according to split_sizes.
        class_counters = {}
        i = 0
        for repo in repo_class_pairs:
            class_label = repo_class_pairs[repo]
            if class_label not in class_counters:
                class_counters[class_label] = 1
            else:
                class_counters[class_label] += 1

            if class_counters[class_label] <= split_sizes[class_label]:
                training_labels.append(labels[i])
                training_set.append(features[i])
            else:
                test_labels.append(labels[i])
                test_set.append(features[i])

            i += 1

        return training_set, test_set, training_labels, test_labels

    def __export_confusion_matrix(self, labels, predicted, output_path):
        success = 0
        fail = 0
        for i in range(0,len(labels)):
            if labels[i] == predicted[i]:
                success += 1
            else:
                fail += 1

        print(success, fail, success/(success+fail))

        label_names = np.unique(labels)
        prediction_names = np.unique(predicted)

        conf_matrix = confusion_matrix(labels, predicted, label_names)
        print(conf_matrix)
        with open(output_path, "w") as output_file:
            output_file.write(";")
            for i in range(0, len(label_names)):
                output_file.write(str(label_names[i]) + ";")
            output_file.write("\n")
            for row in range(0, len(conf_matrix)):
                output_file.write(str(label_names[row]) + ";")
                for col in range(0, len(conf_matrix[row])):
                    output_file.write(str(conf_matrix[row][col]) + ";")
                output_file.write("\n")



