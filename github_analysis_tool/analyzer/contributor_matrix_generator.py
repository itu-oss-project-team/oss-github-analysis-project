import time

from github_analysis_tool.services.database_service import DatabaseService

from github_analysis_tool.services.db_column_constants import Columns

class ContributorMatrixGenerator:

    def __init__(self):
        self.__databaseService = DatabaseService()

    def create_matrix(self, repo_id):
        start_time = time.time()

        contributor_matrix = {}
        github_user_matrix = {}
        nongithub_user_matrix = {}
        
        contributor_file_array = {}
        
        contributor_info_array = {}
        
        commits = self.__databaseService.get_commits_of_repo(repo_id, get_only_ids=True)
        
        # For every commit in repo
        for commit_id in commits:

            files = self.__databaseService.get_files_changes_of_commit(commit_id)
            committer = self.__databaseService.get_contributor_of_commit(commit_id)
            first_cont_date = self.__databaseService.get_commit_date(commit_id)
            additions = self.__databaseService.get_commit_additions(commit_id)
            deletions = self.__databaseService.get_commit_deletions(commit_id)
            
            commit_files = [file[Columns.FileChanges.path] for file in files]
            committer_id = committer['author_id']
            commit_date = first_cont_date ['created_at']
            commit_additions = additions['additions']
            commit_deletions = deletions ['deletions']
            
            #contributor info/metrices
            if committer_id not in contributor_info_array:
                contributor_info_array[committer_id] = {}
                ## First commit date
                contributor_info_array[committer_id][0]=commit_date
                ## Overall commit number
                contributor_info_array[committer_id][1]=1 
                ## Overall line that changed by this contributor
                contributor_info_array[committer_id][2]= commit_additions + commit_deletions                 
            else:
                contributor_info_array[committer_id][1] += 1
                contributor_info_array[committer_id][2] += commit_additions + commit_deletions    
            
            if committer_id not in contributor_file_array:
                contributor_file_array[committer_id] = {}
                contributor_matrix[committer_id] = {}
            
            #add file to contributor files 
            for file in commit_files:
                file_exists = 0
                for files in contributor_file_array[committer_id]:                    
                    if contributor_file_array[committer_id][files] == file:
                        file_exists = 1
                        break
                if file_exists == 0:
                    contributor_file_array[committer_id][len(contributor_file_array[committer_id])]=file
           
        for contributor1 in contributor_file_array:                              
            for contributor2 in contributor_file_array:                    
                ############DÜZENLE / 2 contributorun ortak dosyalarını düzgün bulmuyor
                if (contributor1 == contributor2):
                    shared_items = 0
                else:
                    print (contributor_file_array[contributor1])
                    print (contributor_file_array[contributor2])
                    shared_items =0
                    for item1 in contributor_file_array[contributor1]:
                        for item2 in contributor_file_array[contributor2]:
                            if contributor_file_array[contributor1][item1] == contributor_file_array[contributor2][item2]:
                                shared_items= shared_items + 1
                                    
                self.__increment_file_count(contributor_matrix, contributor1, contributor2, shared_items)
                print(shared_items)
                print('\n')
        #Calculate project metrics                    
        min_edited_lines=9999999999999999;
        max_edited_lines=0;
        average_edited_lines=0;
        contributor_number=0;
        for contributor in contributor_info_array:
            contributor_number +=1
            if contributor_info_array[contributor][2]>max_edited_lines:
                 max_edited_lines = contributor_info_array[contributor][2]
            if contributor_info_array[contributor][2]<min_edited_lines:     
                 min_edited_lines = contributor_info_array[contributor][2]
            average_edited_lines=(average_edited_lines*(contributor_number-1)+contributor_info_array[contributor][2])/contributor_number
            
        #Write
        with open(str(repo_id) + "_cont_matrix.txt", "w") as out_file:
            out_file.write("max edited lines: %d " % max_edited_lines)
            out_file.write("min edited lines: %d " % min_edited_lines)
            out_file.write("average edited lines: %d\n\n" % average_edited_lines)
            for contributor in contributor_info_array:
                out_file.write("%d " % contributor)
                out_file.write("first commit date: %s " % str(contributor_info_array[contributor][0]))
                out_file.write("overall commit number: %d " % contributor_info_array[contributor][1])
                out_file.write("edited lines: %d\n" % contributor_info_array[contributor][2])
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
                is_github_user = self.__databaseService.check_contributor_status(contributor)
                check_user_status=is_github_user['is_github_user']
                if check_user_status == 0:
                    out_file.write("%d\n" % contributor)
                    nongithub_user_matrix[contributor]=contributor_matrix[contributor]                    
                    
            out_file.write("\n")
            for contributor1 in nongithub_user_matrix:
                for contributor2 in nongithub_user_matrix: 
                        if not contributor2 in contributor_matrix[contributor1]:
                            out_file.write("%3d " % 0)
                        else:
                            out_file.write("%3d " % contributor_matrix[contributor1][contributor2])
                out_file.write("\n")
        
        with open(str(repo_id) + "_user_matrix.txt", "w") as out_file:
            for contributor in contributor_file_array:
                is_github_user = self.__databaseService.check_contributor_status(contributor)
                check_user_status=is_github_user['is_github_user']
                if check_user_status == 1:
                    out_file.write("%d\n" % contributor)
                    github_user_matrix[contributor]=contributor_matrix[contributor]
                    
            out_file.write("\n")
            for contributor1 in github_user_matrix:
                for contributor2 in github_user_matrix: 
                        if not contributor2 in contributor_matrix[contributor1]:
                            out_file.write("%3d " % 0)
                        else:
                            out_file.write("%3d " % contributor_matrix[contributor1][contributor2])
                out_file.write("\n")
        
        elapsed_time = time.time() - start_time
        print("---> Contributor matrix generated for repo (" + str(repo_id) + ") in " + str(elapsed_time) + " seconds.")

    def __increment_file_count(self, contributor_matrix, contributor1, contributor2, amount):
        if contributor1 not in contributor_matrix:
            contributor_matrix[contributor1] = {}
        else:
            contributor_matrix[contributor1][contributor2] = amount
