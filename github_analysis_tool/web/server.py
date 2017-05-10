import pandas
import os
import sys
import requests
from flask import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from github_analysis_tool import OUTPUT_DIR
app = Flask(__name__)


@app.route('/classification_results', methods=['POST', 'GET'])
def clsf_results():
    clsf_folder = os.path.join(OUTPUT_DIR, "classification")
    label_folders = [path for path in os.listdir(clsf_folder) if os.path.isdir(os.path.join(clsf_folder, path))]
    label_folders.reverse()
    datasets = {}
    for label_folder in label_folders:
        datasets[label_folder] = {}
        label_folder_path = os.path.join(clsf_folder, label_folder)
        ds_folders = [path for path in os.listdir(label_folder_path) if
                      os.path.isdir(os.path.join(label_folder_path, path))]
        for ds_folder in ds_folders:
            dataset_folder_path = os.path.join(label_folder_path, ds_folder)
            files = [file for file in os.listdir(dataset_folder_path) if file.endswith(".csv")]
            datasets[label_folder][ds_folder] = files

    if request.method == 'GET':
        return render_template("classification_results.html", label_folders=label_folders, datasets=datasets, df=None, message=None)
    elif request.method == 'POST':
        label_name = request.form["label-menu"]
        dataset_name = request.form["dataset-menu"]
        file_name = request.form["file-menu"]
        file_path = os.path.join(OUTPUT_DIR, "classification", label_name, dataset_name, file_name)
        df = pandas.read_csv(file_path, sep=';', index_col=0).fillna('')
        msg = label_name + " - " + dataset_name + " - " + file_name
        return render_template("classification_results.html", label_folders=label_folders, datasets=datasets, df=df, message=msg)

if __name__ == '__main__':
    app.run()