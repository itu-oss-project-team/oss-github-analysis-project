import collections
import numpy as np
import os.path
from sklearn import neighbors
from sklearn.metrics import confusion_matrix
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool.analyzer.analysis_utilities import AnalysisUtilities


class Classification:

    def __init__(self):
        self.__analysis_utilities = AnalysisUtilities()
        self.__database_service = DatabaseService()

    def set_language_labels(self, df):
        threshold = 3
        headers, repos, features = self.__analysis_utilities.decompose_df(df)
        language_counts = {}
        repo_labels = {}

        # Which languages should be treated as one
        language_groups = [["JavaScript", "TypeScript", "CoffeeScript"]]

        # {"language_a" : "language_a,language_b,language_c"}
        group_language_mapping = {}

        # Fill language -> group mapping
        for language_group in language_groups:
            group_label = '-'.join(language_group)
            for language in language_group:
                group_language_mapping[language] = group_label

        # Let's find out languages of all repos and repo counts of languages with taking care of lang groups
        for repo in repos:
            repo_lang = self.__database_service.get_language_by_repo_full_name(repo)
            if repo_lang in group_language_mapping:
                # This language is a part of group use group label
                repo_labels[repo] = group_language_mapping[repo_lang]
            else:
                repo_labels[repo] = repo_lang

            if repo_labels[repo] not in language_counts:
                language_counts[repo_labels[repo]] = 1
            else:
                language_counts[repo_labels[repo]] += 1

        # Find languages with repo counts lower than our threshold
        ignored_languages = [language for language in language_counts if language_counts[language] < threshold]
        # Find repos with ignored languages
        ignored_repos = [repo for repo in repos if repo_labels[repo] in ignored_languages]

        # We should no longer keep language information of ignored repos
        for repo in ignored_repos:
            repo_labels.pop(repo, None)

        labels = []
        for repo in repo_labels:
            labels.append(repo_labels[repo])
        return labels, repo_labels, ignored_repos

    def set_no_of_commits_labels(self, df):
        headers, repos, features = self.__analysis_utilities.decompose_df(df)
        labels = []
        repo_labels = collections.OrderedDict()
        for repo in repos:
            result = self.__database_service.get_repo_stats(repo_full_name=repo)
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

            repo_labels[repo] = label
            labels.append(label)

        return labels, repo_labels, []  # No ignored repos

    def __export_confusion_matrix(self, labels, predicted, out_file_pre_path):
        success = 0
        fail = 0
        for i in range(0, len(labels)):
            if labels[i] == predicted[i]:
                success += 1
            else:
                fail += 1

        print(success, fail, success/(success+fail))

        label_names = np.unique(labels)

        conf_matrix = confusion_matrix(labels, predicted, label_names)
        print(conf_matrix)
        out_file_path = out_file_pre_path + "_confusionMatrix.csv"
        with open(out_file_path, "w") as output_file:
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

    def classify_with_knn(self, out_folder_path, training_set, test_set, training_labels, test_labels, k=5):

        out_file_pre_path = os.path.join(out_folder_path, "knn" + str(k))  # Any output file should extend this path

        knn_classifier = neighbors.KNeighborsClassifier(k, weights='distance')
        knn_classifier.fit(training_set, training_labels)
        predicted = knn_classifier.predict(test_set)

        self.__export_confusion_matrix(test_labels, predicted, out_file_pre_path)

