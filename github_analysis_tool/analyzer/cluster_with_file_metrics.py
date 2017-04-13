import os.path
import pandas
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool.analyzer.network_analysis import NetworkAnalysis
from github_analysis_tool import OUTPUT_DIR

def cluster_with_file_metrics():
    print("--> Network analysis for file metrics started")

    network_analysis = NetworkAnalysis()
    file_metrics_path = os.path.join(OUTPUT_DIR, "file_metrics.csv")

    # Create data frames
    data_sets = list()  # {df:<DataFrame>, name:<String>}

    # Original data frame
    original_df = pandas.read_csv(file_metrics_path, sep=';', index_col=0)
    data_sets.append({"df": original_df, "name": "original"})

    # Without min-max columns
    columns = list(original_df)
    min_max_columns = [column for column in columns if ("_min" in column) or ("_max" in column)]

    no_min_max_df = original_df.drop(min_max_columns, axis=1)
    data_sets.append({"df": no_min_max_df, "name": "no_min_max"})

    '''
    # Without JavaScript repos
    javascript_rows = list()
    for repo in network_analysis.repo_languages:
        if network_analysis.repo_languages[repo] in ["JavaScript", "TypeScript", "CoffeeScript"]:
            javascript_rows.append(repo)
    # Take only repos that exists in our data set
    to_drop_rows = [js_repo for js_repo in javascript_rows if js_repo in original_df.index]

    no_js_df = original_df.drop(to_drop_rows)
    data_sets.append({"df": no_js_df, "name": "no_js_df"})

    # Without min-max columns and JavaScript repos
    no_min_max_no_js_df = no_min_max_df.drop(to_drop_rows)
    data_sets.append({"df": no_min_max_no_js_df, "name": "no_min_max_js_df"})
    '''
    # Repo stats
    database_service = DatabaseService()
    repo_stats = database_service.get_repo_stats()
    repo_stats_df = pandas.DataFrame.from_dict(repo_stats)
    repo_stats_df.set_index(keys="full_name", inplace=True)
    data_sets.append({"df": repo_stats_df, "name": "repo_stats_df"})

    '''
    # Repo stats without JS
    # Take only repos that exists in our data set
    to_drop_rows = [js_repo for js_repo in javascript_rows if js_repo in repo_stats_df.index]
    repo_stats_no_js_df = repo_stats_df.drop(to_drop_rows)
    data_sets.append({"df": repo_stats_no_js_df, "name": "repo_stats_no_js_df"})
    '''

    for data_set in data_sets:
        network_analysis.do_clustering(data_frame=data_set["df"], data_set_name=data_set["name"])

    print("--> Network analysis for file metrics finished")

cluster_with_file_metrics()
