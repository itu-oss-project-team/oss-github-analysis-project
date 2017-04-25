import collections
import numpy as np
import os.path
from sklearn import neighbors
from sklearn.metrics import confusion_matrix, accuracy_score
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
        headers, repos, observations = self.__analysis_utilities.decompose_df(df)
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

    def set_two_class_language_labels(self, df):
        headers, repos, observations = self.__analysis_utilities.decompose_df(df)
        labels = []
        repo_labels = collections.OrderedDict()

        for repo in repos:
            language = self.__database_service.get_language_by_repo_full_name(repo)

            if language == "JavaScript" or language == "TypeScript" or language == "CoffeeScript" \
                    or language == "HTML" or language == "CSS" or language == "PHP" \
                    or language == "Jupyter Notebook":
                label = "Web"
            else:
                label = "Non-Web"

            repo_labels[repo] = label
            labels.append(label)

        return labels, repo_labels, []  # No ignored repos

    def set_star_labels(self, df):
        headers, repos, observations = self.__analysis_utilities.decompose_df(df)
        labels = []
        repo_labels = collections.OrderedDict()
        for repo in repos:
            result = self.__database_service.get_repo_by_full_name(repo)
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

            repo_labels[repo] = label
            labels.append(label)

        return labels, repo_labels, []  # No ignored repos

    def set_no_of_commits_labels(self, df):
        headers, repos, observations = self.__analysis_utilities.decompose_df(df)
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

    def __retrieve_confusion_matrix(self, labels, predicted, out_file_pre_path):
        success = accuracy_score(labels, predicted, normalize=False)
        fail = len(labels) - success
        ratio = accuracy_score(labels, predicted)
        print(success, fail, ratio)

        label_names = np.unique(labels)

        conf_matrix = confusion_matrix(labels, predicted, label_names)

        self.__analysis_utilities.export_confusion_matrix(out_file_pre_path, conf_matrix,
                                                          label_names, success, fail)

        return conf_matrix

    def knn_classify(self, out_folder_path, training_set, test_set, training_labels, test_labels, k=3, msg=""):
        out_file_pre_path = os.path.join(out_folder_path, "knn" + str(k) + msg)  # Any output file should extend this path

        knn_classifier = neighbors.KNeighborsClassifier(k, weights='distance')
        knn_classifier.fit(training_set, training_labels)
        predicted = knn_classifier.predict(test_set)

        success = accuracy_score(test_labels, predicted, normalize=False)
        conf_matrix = self.__retrieve_confusion_matrix(test_labels, predicted, out_file_pre_path)
        return conf_matrix, success

