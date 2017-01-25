from database_service import DatabaseService
import yaml
import os.path
from math import log10

class Tfidf:
    def __init__(self, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__databaseService = DatabaseService(secret_config['mysql'])
        self.__commits = []

    def addCommitToDictionary(self, commit_sha, commit_message):
        commit_msg = str(commit_message).encode('utf-8')
        commit_msg = str(commit_msg)
        #sha, message, tf-idf
        self.__commits.append([commit_sha, commit_msg, 0])

    def printValues(self, commitList):
        print("size: " + str(len(commitList)) + "\n")
        for commit in commitList:
            commit_msg = str(commit[1])
            print(commit_msg + "  tf-idf: " + str(commit[2]))

    def generateContainer(self):
        repos = self.__databaseService.getAllRepos(get_only_ids=True)
        for repo_id in repos:
            commits = self.__databaseService.getCommitsOfRepo(repo_id, get_only_shas=False)
            for commit in commits:
                self.addCommitToDictionary(commit["sha"], commit["message"])

        return

    def tf_idf(self, keywords, threshold_value=0):
        scored_commits = []
        count_of_all_occurances=0
        print("Total number of commits: " + str(len(self.__commits)))
        #idf calculation
        for commit in self.__commits:
            commit_msg = commit[1]
            for word in commit_msg.split():
                for keyword in keywords:
                    if word == keyword:
                        count_of_all_occurances += 1
                        break

        idf = log10(len(self.__commits)/count_of_all_occurances)
        print("idf: " + str(idf))

        #tf calculation for each commit message
        for commit in self.__commits:
            commit_msg = commit[1]
            count_of_similarities_in_msg=0
            for word in commit_msg.split():
                for keyword in keywords:
                    if word == keyword:
                        count_of_similarities_in_msg += 1

            score = count_of_similarities_in_msg / len(commit_msg.split())
            score = score * idf
            commit[2] = score
            if score > threshold_value:
                #sha, message, score
                scored_commits.append([commit[0], commit[1], commit[2]])
        scored_commits.sort(key=lambda x:x[2])
        return scored_commits

def main():
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    tfidf = Tfidf(secret_config)
    tfidf.generateContainer()

    print("\nBUG-FIX COMMITS\n")
    bugfix_commits = tfidf.tf_idf(["Fix", "fixed", "edit", "edited", "modify", "modified", "correct", "corrected"], 0.0)
    tfidf.printValues(bugfix_commits)

    print("\nADD NEW FEATURE COMMITS\n")
    add_commits = tfidf.tf_idf(["add", "added", "impelement", "implemented", "feat", "feature"], 0.0)
    tfidf.printValues(add_commits)

    print("\nREMOVE COMMITS\n")
    remove_commits = tfidf.tf_idf(["delete", "deleted", "remove", "removed"], 0.0)
    tfidf.printValues(remove_commits)

    return

main()



