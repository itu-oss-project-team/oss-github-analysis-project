import os.path
import pandas as pd
import sys

from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn import linear_model, neighbors, tree
from sklearn.neural_network import MLPClassifier

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.analyzer.analysis_utilities import AnalysisUtilities
from github_analysis_tool.analyzer.classification import Classification
from github_analysis_tool.analyzer.network_analysis import NetworkAnalysis
from github_analysis_tool import OssConstants


class Classify:
    def __init__(self):
        self.network_analysis = NetworkAnalysis()
        self.analysis_utilities = AnalysisUtilities()
        self.classification = Classification()

        # Create list of desired labellings
        self.label_funcs = self.__create_label_funcs()  # {func:<labelling_function(df)>, name:<String>}
        # Create data frames
        self.data_sets = self.__create_data_sets()  # {df:<DataFrame>, name:<String>}
        # Create classifiers
        self.classifiers = self.__create_classifiers()  # {func:<Classifying method>, name:<String}
        # construct configurations
        self.configurations = self.__create_configurations()

    def __create_label_funcs(self):
        label_funcs = list()
        label_funcs.append({"func": self.classification.set_language_labels,
                            "name": "languageLabels"})
        label_funcs.append({"func": self.classification.set_two_class_language_labels,
                            "name": "twoClassLanguageLabels"})
        return label_funcs

    def __create_data_sets(self):
        data_sets = list()
        # File metrics data frame
        file_df = pd.read_csv(OssConstants.FILE_METRICS_PATH, sep=';', index_col=0)
        data_sets.append({"df": file_df,
                          "name": "fileMetric"})
        # Commit metrics data frame
        commit_df = pd.read_csv(OssConstants.COMMIT_METRICS_PATH, sep=';', index_col=0)
        data_sets.append({"df": commit_df,
                          "name": "commitMetric"})
        # Repo stats data frame
        repo_df = self.analysis_utilities.get_repo_stats_df()
        # File + commit metrics data frame
        file_commit_df = self.analysis_utilities.merge_dfs_on_indexes(file_df, commit_df, "_file", "_commit")
        data_sets.append({"df": file_commit_df,
                          "name": "fileMetric,CommitMetric"})
        # file + repo stats data frame
        file_repo_df = self.analysis_utilities.merge_dfs_on_indexes(file_df, repo_df, "", "")
        data_sets.append({"df": file_repo_df,
                          "name": "fileMetric,repoStat"})
        # commit + repo stats data frame
        commit_repo_df = self.analysis_utilities.merge_dfs_on_indexes(commit_df, repo_df, "", "")
        data_sets.append({"df": commit_repo_df,
                          "name": "commitMetric,repoStat"})
        # all
        file_commit_repo_df = self.analysis_utilities.merge_dfs_on_indexes(file_commit_df, repo_df)
        data_sets.append({"df": file_commit_repo_df,
                          "name": "fileMetric,commitMetric,repoStat"})

        return data_sets

    def __create_classifiers(self):
        classifiers = list()
        classifiers.append({"func": linear_model.SGDClassifier(loss="log"),
                            "name": "sgd"})
        classifiers.append({"func": neighbors.KNeighborsClassifier(1, weights='distance'),
                            "name": "knn1"})
        classifiers.append({"func": neighbors.KNeighborsClassifier(3, weights='distance'),
                            "name": "knn3"})
        classifiers.append({"func": neighbors.KNeighborsClassifier(5, weights='distance'),
                            "name": "knn5"})
        classifiers.append({"func": GaussianNB(),
                            "name": "naive_bayes"})

        # classifiers.append({"func": tree.DecisionTreeClassifier(), "name": "decision_tree"})
        # classifiers.append({"func": MLPClassifier(max_iter=10000), "name": "mlp"})
        # classifiers.append({"func": RandomForestClassifier(), "name": "random_forest"})
        return classifiers

    def __create_configurations(self):
        configurations = list()
        configurations.append({"sampling": False, "normalize": False})
        configurations.append({"sampling": False, "normalize": True})
        configurations.append({"sampling": True, "normalize": False})
        configurations.append({"sampling": True, "normalize": True})
        return configurations

    def start_classifying(self):
        print("--> Classification started")

        for label_func in self.label_funcs:
            for data_set in self.data_sets:
                for conf in self.configurations:
                    self.network_analysis.do_classification(classifiers=self.classifiers,
                                                       df=data_set["df"], df_name=data_set["name"],
                                                       labelling_func=label_func["func"],
                                                       labelling_name=label_func["name"],
                                                       sampling=conf["sampling"], normalize=conf["normalize"])

        print("--> Classification finished calculation finished")

if __name__ == "__main__":
    classify = Classify()
    classify.start_classifying()
