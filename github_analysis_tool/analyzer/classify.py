import os.path
import pandas as pd
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.analyzer.analysis_utilities import AnalysisUtilities
from github_analysis_tool.analyzer.classification2 import Classification
from github_analysis_tool.analyzer.network_analysis import NetworkAnalysis
from github_analysis_tool import OssConstants

print("--> Classification started")

network_analysis = NetworkAnalysis()
analysis_utilities = AnalysisUtilities()
classification = Classification()

# Create list of desired labellings
label_funcs = list()  # {func:<labelling_function(df)>, name:<String>}

label_funcs.append({"func": classification.set_language_labels, "name": "languageLabels"})
label_funcs.append({"func": classification.set_two_class_language_labels, "name": "twoClassLanguageLabels"})
label_funcs.append({"func": classification.set_star_labels, "name": "starLabels"})

# Create data frames
data_sets = list()  # {df:<DataFrame>, name:<String>}

# File metrics data frame
file_df = pd.read_csv(OssConstants.FILE_METRICS_PATH, sep=';', index_col=0)
data_sets.append({"df": file_df, "name": "(fileMetric)"})

# Commit metrics data frame
commit_df = pd.read_csv(OssConstants.COMMIT_METRICS_PATH, sep=';', index_col=0)
data_sets.append({"df": commit_df, "name": "(commitMetric)"})

# Repo stats data frame
repo_df = analysis_utilities.get_repo_stats_df()

# File + commit metrics data frame
file_commit_df = analysis_utilities.merge_dfs_on_indexes(file_df, commit_df, "_file", "_commit")
data_sets.append({"df": file_commit_df, "name": "(fileMetric,CommitMetric)"})

# file + repo stats data frame
file_repo_df = analysis_utilities.merge_dfs_on_indexes(file_df, repo_df, "", "")
data_sets.append({"df": file_repo_df, "name": "(fileMetric,repoStat)"})

# commit + repo stats data frame
commit_repo_df = analysis_utilities.merge_dfs_on_indexes(commit_df, repo_df, "", "")
data_sets.append({"df": file_repo_df, "name": "(commitMetric,repoStat)"})

# all
file_commit_repo_df = analysis_utilities.merge_dfs_on_indexes(file_commit_df, repo_df)
data_sets.append({"df": file_commit_repo_df, "name": "(fileMetric,commitMetric,repoStat)"})

configurations = list()
configurations.append({"sampling": False, "normalize": False})
configurations.append({"sampling": False, "normalize": True})
configurations.append({"sampling": True, "normalize": False})
configurations.append({"sampling": True, "normalize": True})

for label_func in label_funcs:
    for data_set in data_sets:
        for conf in configurations:
            network_analysis.do_classification(df=data_set["df"], df_name=data_set["name"],
                                           labelling_func=label_func["func"], labelling_name=label_func["name"],
                                           sampling=conf["sampling"], normalize=conf["normalize"])

print("--> Classification finished calculation finished")
