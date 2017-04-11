import os
import sys
from github_analysis_tool.services.database_service import DatabaseService

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def IssueLinker(issueid,repoId,secret_config):

    database = DatabaseService(secret_config['mysql'])
    commits = database.getCommitsOfRepo(repoId)
    keywords = ["Fix", "fixed", "edit", "edited", "modify", "modified", "correct", "corrected","close","closed","resolves","resolved","bug","issue"]
    
    for commit in commits:
        semantic = 0
        syntactic = 0
        keywordfound = False
        idfound = False
        
        message = commit[1]
        for word in message.split():
            if idfound is False:
                    if word == str(issueid):
                        semantic += 1
                        idfound = True
                        print ("Found issue id")
                        
            for keyword in keywords:
                if keywordfound is False:
                    if word == keyword:
                        semantic += 1
                        keywordfound = True
                        print ("Found keyword")

    print("Commit: " + str(commits["id"]))                    
        #if commit.author.login == closedby.login:
        #    syntactic +=1;
           
           
        #if semantic == 2 and syntactic == 1:
         #   print(commit.id)
    
        

