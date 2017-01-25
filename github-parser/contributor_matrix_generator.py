from database_service import DatabaseService

class ContributorMatrixGenerator:

    def __init__(self, secret_config):
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def create_matrix(self, repo_id):
       
        contributor_matrix = {}
        github_user_matrix = {}
        nongithub_user_matrix = {}
        
        contributor_file_array = {}
        
        commits = self.__databaseService.getCommitsOfRepo(repo_id, get_only_shas=True)
        
        # For every commit in repo
        for commit_sha in commits:

            files = self.__databaseService.getFilesChangesOfCommit(commit_sha)
            committer = self.__databaseService.getContributorOfCommit (commit_sha)
            
            commit_files = [file['filename'] for file in files]
            committer_id = committer['author_id']
            
            
            
            if committer_id not in  contributor_file_array:
                contributor_file_array[committer_id] = {}
                contributor_matrix[committer_id] = {}
            
            for file in commit_files:
                if file not in  contributor_file_array[committer_id]:    
                    contributor_file_array[committer_id][len(contributor_file_array[committer_id])+1]=file
            
            for file1 in contributor_file_array[committer_id]:                                
                for contributor2 in contributor_file_array:                    
                    if file1 in contributor_file_array[contributor2]:
                        self.__increment_file_count(contributor_matrix, committer_id, contributor2)
                        

        ####WRITE 
        
        with open(str(repo_id) + "_cont_matrix.txt", "w") as out_file:
            for contributor in contributor_file_array:
                out_file.write("%d\n" % contributor)
            out_file.write("\n")
            for contributor1 in contributor_file_array:
                for contributor2 in contributor_file_array:
                    if not contributor2 in contributor_matrix[contributor1]:
                        out_file.write("%3d " % 0)
                    else:
                        out_file.write("%3d " % contributor_matrix[contributor1][contributor2])
                out_file.write("\n")
        
        with open(str(repo_id) + "_nonuser_matrix.txt", "w") as out_file:
            for contributor in contributor_file_array:
                is_github_user = self.__databaseService.checkContributorStatus(contributor)
                check_user_status=is_github_user['is_github_user']
                if check_user_status == 0:
                    out_file.write("%d\n" % contributor)
            out_file.write("\n")
            for contributor1 in contributor_file_array:
                for contributor2 in contributor_file_array:
                    is_github_user = self.__databaseService.checkContributorStatus(contributor)
                    check_user_status=is_github_user['is_github_user']
                    if check_user_status == 0:
                        if not contributor2 in contributor_matrix[contributor1]:
                            out_file.write("%3d " % 0)
                        else:
                            out_file.write("%3d " % contributor_matrix[contributor1][contributor2])
                out_file.write("\n")
        
        with open(str(repo_id) + "_user_matrix.txt", "w") as out_file:
            for contributor in contributor_file_array:
                is_github_user = self.__databaseService.checkContributorStatus(contributor)
                check_user_status=is_github_user['is_github_user']
                if check_user_status == 1:
                    out_file.write("%d\n" % contributor)
                    
            out_file.write("\n")
            for contributor1 in contributor_file_array:
                for contributor2 in contributor_file_array:
                    is_github_user = self.__databaseService.checkContributorStatus(contributor)
                    check_user_status=is_github_user['is_github_user']                    
                    if check_user_status == 1:
                        if not contributor2 in contributor_matrix[contributor1]:
                            out_file.write("%3d " % 0)
                        else:
                            out_file.write("%3d " % contributor_matrix[contributor1][contributor2])
                out_file.write("\n")
        print('done')        

    def __increment_file_count(self, contributor_matrix, committer_id, contributor2):
        if committer_id not in contributor_matrix:
            contributor_matrix[committer_id] = {}
        if contributor2 in contributor_matrix[committer_id]:
            contributor_matrix[committer_id][contributor2] += 1
        else:
            contributor_matrix[committer_id][contributor2] = 1
