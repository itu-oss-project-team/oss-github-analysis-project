import os
import sys
from github_analysis_tool.services.database_service import DatabaseService

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    print("main")


def IssueLinker(issueId,repoId,secret_config):

    database = DatabaseService(secret_config['mysql'])
    commits = database.get_commits_of_repo(repoId, False)
    issue = database.getIssue(issueId)
    keywords = ["Fix", "fixed", "edit", "edited", "modify", "modified", "correct", "corrected","close","closed","resolves","resolved","bug","issue"]
    maxpoint = 0
    fixingcommit = None
    
    for commit in commits:
        semantic = 0
        syntactic = 0
        keywordfound = False
        idfound = False
        issuehash = "#"+ str(issueId)
        message = commit[1]
        for word in message.split():
            if idfound is False:
                    if word == str(issueId) or word == issuehash:
                        semantic += 2
                        idfound = True
                        print ("Found issue id")
                        
            for keyword in keywords:
                if keywordfound is False:
                    if word == keyword:
                        semantic += 1
                        keywordfound = True
                        print ("Found keyword")
                        
        if issue.title in message:
            syntactic += 1
            print("exact message match")
        
        if issue["closedby"] is not None:
            if issue["closedby"] == commit.author.id:
                syntactic += 1
                print("User match")

        point = semantic + syntactic
        if point > maxpoint:
            point = maxpoint
            fixingcommit = commit
        
    print("Commit: " + str(fixingcommit["sha"]))                    

def BugInducingCommitFinder(commitsha,issue,repoId,secret_config):
        print("Boşluk")
        
        database = DatabaseService(secret_config['mysql'])
        commits = database.get_commits_of_repo(repoId, False)
        fixchanges = database.get_files_of_files_changes_of_commit(commitsha, False)
        
        for commit in commits:
            commitid = commit["sha"]
            committime = commit["created_at"]
            if committime > issue["created_at"]:
                inducingchanges = database.get_files_of_files_changes_of_commit(commitid, False)
            
            inducingchanges.sort()
            fixchanges.sort()
            if inducingchanges == fixchanges:
                return commitid
                
                    
        

