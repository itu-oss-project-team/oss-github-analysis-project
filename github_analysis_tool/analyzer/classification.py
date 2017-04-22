import os.path
import pandas
from sklearn import neighbors
from sklearn.model_selection import *
from sklearn.feature_selection import *
from sklearn.svm import *
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import *
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
        observations = data._get_values  # fetch observations.
        return headers, repos, observations

    def set_star_labels(self, data):
        headers, repos, observations = self.__fetch_data(data)
        labels = []
        repo_stars_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_by_full_name(repo)
            stars = result["stargazers_count"]
            if stars > 50000:
                label = "50k+"
            elif 30000 <= stars < 50000:
                label = "30k-50k"
            elif 20000 <= stars < 30000:
                label = "20k-30k"
            elif 15000 <= stars < 20000:
                label = "15k-20k"
            elif stars < 15000:
                label = "15k-"

            repo_stars_pair[repo] = label

            labels.append(label)

        return data, labels, repo_stars_pair

    def set_no_of_filechanges_labels(self, data):
        headers, repos, observations = self.__fetch_data(data)
        labels = []
        repo_no_of_filechanges_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_filechanges = result["no_of_file_changes"]
            if no_of_filechanges >= 250000:
                label = "250k+"
            elif 100000 <= no_of_filechanges < 250000:
                label = "100k-250k"
            elif 60000 <= no_of_filechanges < 100000:
                label = "60k-100k"
            elif 40000 <= no_of_filechanges < 60000:
                label = "40k-60k"
            elif 30000 <= no_of_filechanges < 40000:
                label = "30k-40k"
            elif 20000 <= no_of_filechanges < 30000:
                label = "20k-30k"
            elif 10000 <= no_of_filechanges < 20000:
                label = "10k-20k"
            elif 7000 <= no_of_filechanges < 10000:
                label = "7k-10k"
            elif 5000 <= no_of_filechanges < 7000:
                label = "5k-7k"
            elif 2000 <= no_of_filechanges < 5000:
                label = "2k-5k"
            else:
                label = "2k-"

            repo_no_of_filechanges_pair[repo] = label
            labels.append(label)

        return data, labels, repo_no_of_filechanges_pair

    def set_no_of_files_labels(self, data):
        headers, repos, observations = self.__fetch_data(data)
        labels = []
        repo_no_of_files_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_files = result["no_of_changed_files"]
            if no_of_files >= 30000:
                label = "30k+"
            elif 10000 <= no_of_files < 30000:
                label = "10k-30k"
            elif 5000 <= no_of_files < 10000:
                label = "5k-10k"
            elif 3000 <= no_of_files < 5000:
                label = "3k-5k"
            elif 2000 <= no_of_files < 3000:
                label = "2k-3k"
            elif 1000 <= no_of_files < 2000:
                label = "1k-2k"
            elif 500 <= no_of_files < 1000:
                label = "500-1k"
            elif 200 <= no_of_files < 500:
                label = "200-500"
            else:
                label = "200-"

            repo_no_of_files_pair[repo] = label
            labels.append(label)

        return data, labels, repo_no_of_files_pair

    def set_two_class_language_labels(self, data):
        headers, repos, observations = self.__fetch_data(data)
        labels = []
        repo_language_pair = collections.OrderedDict()

        for repo in repos:
            language = self.__databaseService.get_language_by_repo_full_name(repo)

            if language == "JavaScript" or language == "TypeScript" or language == "CoffeeScript" \
                    or language == "HTML" or language == "CSS" or language == "PHP" \
                    or language == "Jupyter Notebook":
                label = "Web"
            else:
                label = "Non-Web"

            repo_language_pair[repo] = language
            labels.append(label)

        return data, labels, repo_language_pair

    def set_no_of_commits_labels(self, data):
        headers, repos, observations = self.__fetch_data(data)
        labels = []
        repo_no_of_commits_pair = collections.OrderedDict()
        for repo in repos:
            result = self.__databaseService.get_repo_stats(repo_full_name=repo)
            no_of_commits = result["no_of_commits"]

            if no_of_commits >= 20000:
                label = "20k+"
            elif 10000 <= no_of_commits < 20000:
                label = "10k-20k"
            elif 5000 <= no_of_commits < 10000:
                label = "5k-10k"
            elif 2500 <= no_of_commits < 5000:
                label = "2.5k-5k"
            elif 1000 <= no_of_commits < 2500:
                label = "1k-2.5k"
            elif 500 <= no_of_commits < 1000:
                label = "500-1k"
            else:
                label = "500-"

            repo_no_of_commits_pair[repo] = label
            labels.append(label)

        return data, labels, repo_no_of_commits_pair

    def trim_data_with_language(self, data, threshold = 3):
        headers, repos, observations = self.__fetch_data(data)
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
        new_data = data.drop(ignored_repos)

        labels = []
        for repo in repo_languages:
            labels.append(repo_languages[repo])
        return new_data, labels, repo_languages

    def knn(self, data, message, set_labels, k=5):
        data, labels, repo_class_pair = set_labels(data)
        headers, repos, observations = self.__fetch_data(data)

        new_observations = self.__feature_selection(observations, labels, 20)

        training_set, test_set, training_labels, test_labels = self.__split_data(new_observations, repos, labels, repo_class_pair)
        knn_classifier = neighbors.KNeighborsClassifier(k, weights='distance')
        knn_classifier.fit(training_set, training_labels)
        predicted = knn_classifier.predict(test_set)
        # scores = cross_val_score(classifier, observations, labels, cv=5)
        # predicted = cross_val_predict(classifier, observations, labels, cv=5)

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
        data, labels, repo_class_pair = set_labels(data)
        headers, repos, observations = self.__fetch_data(data)

        new_observations = self.__feature_selection(observations, labels, 8)
        training_set, test_set, training_labels, test_labels = self.__split_data(observations, repos, labels, repo_class_pair)
        svc_classifier = SVC(kernel='rbf')
        svc_classifier.fit(training_set, training_labels)
        predicted = svc_classifier.predict(test_set)
        # scores = cross_val_score(classifier, observations, labels, cv=5)
        # predicted = cross_val_predict(classifier, observations, labels, cv=5)

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

    def __feature_selection(self, observations, labels, k=10):
        sel = SelectKBest(chi2, k=k)
        new_observations = sel.fit_transform(observations, labels)
        return new_observations

    def __split_data(self, observations, repos, labels, repo_class_pairs):
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
            if 1 < label_count < 10:
                split_size = np.rint(0.50 * label_count)
            elif 10 <= label_count < 20:
                split_size = np.rint(0.60 * label_count)
            elif label_count >= 20:
                split_size = np.rint(0.70 * label_count)
            else:
                split_size = label_count

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
                training_set.append(observations[i])
            else:
                test_labels.append(labels[i])
                test_set.append(observations[i])

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

            output_file.write(";")
            for col in range(0, len(conf_matrix[0])):
                output_file.write(";")
            output_file.write(str(success) + ";" + str(fail) + ";")
            output_file.write(str(success/(success+fail)) + ";\n")



