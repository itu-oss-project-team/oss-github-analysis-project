
from github_analysis_tool.services.database_service import DatabaseService

def IssueLinker(self,issueid,issueassigned,repoId):
    
    self.database = DatabaseService(secret_config['mysql'])
    commits = database.getCommitsOfRepo(repoId)
    keywords = ["Fix", "fixed", "edit", "edited", "modify", "modified", "correct", "corrected","close","closed","resolves","resolved","bug"]
    
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
                   
                        
        if commit.committerid == issueassigned:
            syntactic +=1;
           
            
        
     