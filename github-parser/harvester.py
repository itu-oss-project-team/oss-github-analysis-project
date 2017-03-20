#!/usr/bin/python

from requester import GitHubRequester
from database_service import DatabaseService
from _datetime import datetime
#from datetime import datetime
from db_column_constants import Columns
import time


# End point for harvesting GitHub API
class GitHubHarvester:
    def __init__(self, config, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__requester = GitHubRequester(secret_config['github-api'])
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def fetchRepo(self, owner, repo, since_date=None, until_date=None, force_fetch=False):
        repo_url = "https://api.github.com/repos/" + owner + "/" + repo
        time_param = self.__buildTimeParameterString(since_date, until_date)
        res = self.__requester.makeRequest(repo_url)

        if res.status_code == 200:  # API has responded with OK status
            repo = res.json()
            repo_id = repo['id']
            if repo["language"] is None:
                print("Project language is none, skipped.")
                return
            user_login = repo["owner"]["login"]
            if not self.__databaseService.checkIfGithubUserExist(user_login):
                self.__retrieveSingleUser(user_login)
            self.__databaseService.insertProject(repo)
        else:  # Request gave an error
            print("Error while retrieving: " + repo_url)
            print("Status code: " + str(res.status_code))

        if not force_fetch and self.__databaseService.checkIfRepoFilled(repo_id):
            # Repo filled before so i can skip it now
            print("Repo already fetched: " + repo_url)
            return

        print("---> Fetching: " + repo_url)
        # Repo can be new as it's first info
        start_time_string = str(datetime.now())
        start_time = time.time()
        self.__retrieveIssuesofRepo(repo_url, repo_id)
        self.__retrieveCommitsOfRepo(repo_url, repo_id, time_param)
        #self.__retrieveContributorsOfRepo(repo_url, repo_id)
        #self.__retrieveIssuesofRepo(repo_url, repo_id)
        # Let's mark the repo as filled with time which is beginning of fetching
        self.__databaseService.setRepoFilledAt(repo_id, start_time_string)
        elapsed_time = time.time() - start_time
        print("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")
        return

    def fetchRepos(self, min_stars, since_date=None, until_date=None, force_fetch=False):
        self.__retrieveProjects(min_stars)

        repos = self.__databaseService.getRepoUrls()
        for repo in repos:
            repo_url = repo[Columns.Repo.url]
            if repo_url == "https://api.github.com/repos/torvalds/linux":
                continue

            repo_id = repo[Columns.Repo.id]

            print("---> Fetching: " + repo_url)
            # Repo can be new as it's first info
            start_time_string = str(datetime.now())
            start_time = time.time()

            if repo[Columns.Repo.filled_at] is not None and force_fetch is False:
                repo_filled_at = repo[Columns.Repo.filled_at]
                print("---> Repo: " + repo_url + " has some data in it, starting from this time: " + str(repo_filled_at))
                repo_filled_at_str = str(repo_filled_at).split()
                repo_filled_at_string =  repo_filled_at_str[0] + "T" + repo_filled_at_str[1] + "Z"
                time_param = self.__buildTimeParameterString(repo_filled_at_string, until_date)
            else:
                time_param = self.__buildTimeParameterString(since_date, until_date)
                
            self.__retrieveIssuesofRepo(repo_url, repo_id)
            self.__retrieveCommitsOfRepo(repo_url, repo_id, time_param)
            #self.__retrieveContributorsOfRepo(repo_url, repo_id)
            #self.__retrieveIssuesofRepo(repo_url, repo_id)

            # Let's mark the repo as filled with time which is beginning of fetching
            self.__databaseService.setRepoFilledAt(repo_id, start_time_string)
            elapsed_time = time.time() - start_time
            print("---> " + repo_url + " fetched in " + str(elapsed_time) + " seconds.")

    def __retrieveProjects(self, stars_count):
        requestURL = "https://api.github.com/search/repositories?q=stars:>" + str(stars_count) + "&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)
        print("Started retriving projects")
        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            if res.links:
                #print(res.links)
                indexStart = res.links["last"]["url"].find("page=")
                indexEnd = res.links["last"]["url"].find("&per_page")
                last = res.links["last"]["url"][indexStart+5:indexEnd]
            else:
                last = 1

            for i in range(1, int(last)+1):
                print("Repositories: " + str(i))
                _requestURL = "https://api.github.com/search/repositories?q=stars:>" + str(stars_count) + "&page=" + str(i) + "&per_page=100"
                res = self.__requester.makeRequest(_requestURL)
                returnJson = res.json()

                for project in returnJson["items"]:
                    if project["language"] is None:
                        continue
                    userLogin = project["owner"]["login"]
                    if self.__databaseService.checkIfGithubUserExist(userLogin) == False:
                        self.__retrieveSingleUser(userLogin)
                    self.__databaseService.insertProject(project)
        else: # Request gave an error
            print("Error while retrieving: " + requestURL)
            print("Status code: "  + str(res.status_code))
        print("Finished retriving projects")
        return

    def __retrieveSingleUser(self, userLogin):
        userURL = "https://api.github.com/users/" + userLogin
        res = self.__requester.makeRequest(userURL)
        userData = res.json()
        if (res.status_code == 200):  # API has responded with OK status
            self.__databaseService.insertGithubUser(userData)
        else:  # Request gave an error
            print("Error while retriving: " + userURL)
            print("Status code: " + str(res.status_code))

        return

    def __retrieveCommitsOfRepo(self, repoURL, repo_id, since):
        print("Retriving commits from " + repoURL)
        requestURL = str(repoURL) + "/commits?" + since + "&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)
        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            if res.links:
                indexStart = res.links["last"]["url"].find("page=")
                indexEnd = res.links["last"]["url"].find("&per_page")
                last = res.links["last"]["url"][indexStart+5:indexEnd]
            else:
                last = 1

            for i in range(1, int(last)+1):
                print("Commits page: " , i)
                _requestURL = str(repoURL) + "/commits?" + since + "&page=" + str(i) + "&per_page=100"
                res = self.__requester.makeRequest(_requestURL)
                returnJson = res.json()

                for commit in returnJson:
                    if self.__databaseService.checkIfCommitExist(commit["sha"]) == False:
                        __requestURL = str(repoURL) + "/commits/" + str(commit["sha"])
                        res = self.__requester.makeRequest(__requestURL)
                        commitDetail = res.json()

                        #print( str(repoURL) + " current commit sha: " + commitDetail["sha"])
                        if commitDetail is not None:

                            if "sha" not in commitDetail:
                                with open("commit_problems.txt", "a") as commit_problems_file:
                                    commit_problems_file.write(str(datetime.now())+ " " + str(repoURL) + " page: " + str(i))
                                continue

                            if "author" not in commitDetail:
                                with open("commit_problems.txt", "a") as commit_problems_file:
                                    commit_problems_file.write(str(datetime.now())+ " " + str(repoURL) + " current commit sha: " + commitDetail["sha"])
                                continue

                            elif "committer" not in commitDetail:
                                with open("commit_problems.txt", "a") as commit_problems_file:
                                    commit_problems_file.write(str(datetime.now())+ " " + str(repoURL) + " current commit sha: " + commitDetail["sha"])
                                continue

                            # insert Author

                            if commitDetail["author"] is not None: #if there's an author field.

                                if "login" not in commitDetail["author"]: #if author key does not have a login value.
                                    with open("commit_problems.txt", "a") as commit_problems_file:
                                        commit_problems_file.write(str(datetime.now())+ " " + str(repoURL) + " current commit sha: " + commitDetail["sha"])
                                    continue

                                #if user does not exist in database.
                                if self.__databaseService.checkIfGithubUserExist(commitDetail["author"]["login"]) == False:
                                    self.__retrieveSingleUser(commitDetail["author"]["login"]) # retrieve and add user.

                            else: #if there's no author field. --> non-github user.
                                #if non-github user exist in database
                                if commitDetail["commit"]["author"]["email"]: #if non-github user has an email info.
                                    if self.__databaseService.checkIfUserExist(commitDetail["commit"]["author"]["email"]) == False:
                                        self.__databaseService.insertUser(commitDetail["commit"]["author"]) # add non-github user.
                                else:
                                    with open("commit_problems.txt", "a") as commit_problems_file:
                                        commit_problems_file.write(str(datetime.now())+ " " + str(repoURL) + " current commit sha: " + commitDetail["sha"])
                                    continue

                            #insert Committer key

                            if commitDetail["committer"] is not None: #if there's an committer field.
                                if "login" not in commitDetail["committer"]: #if committer key does not have a login value.
                                    with open("commit_problems.txt", "a") as commit_problems_file:
                                        commit_problems_file.write(str(datetime.now())+ " " + str(repoURL) + " current commit sha: " + commitDetail["sha"])
                                    continue
                                #if user does not exist in database.
                                if self.__databaseService.checkIfGithubUserExist(commitDetail["committer"]["login"]) == False:
                                        self.__retrieveSingleUser(commitDetail["committer"]["login"]) #retrieve and add user.

                            else: #if there's no committer field. --> non-github user.
                                 #if non-github user exist in database
                                if commitDetail["commit"]["committer"]["email"]:
                                    if self.__databaseService.checkIfUserExist(commitDetail["commit"]["committer"]["email"]) == False:
                                        self.__databaseService.insertUser(commitDetail["commit"]["committer"]) #add non-github user

                                else:
                                    with open("commit_problems.txt", "a") as commit_problems_file:
                                        commit_problems_file.write(str(datetime.now())+ " " + str(repoURL) + " current commit sha: " + commitDetail["sha"])
                                    continue

                            self.__databaseService.insertCommit(commitDetail, repo_id)

        else: # Request gave an error
            print("Error while retrieving: " + requestURL)
            print("Status code: "  + str(res.status_code))

    def __retrieveContributorsOfRepo(self, repoUrl, repo_id):
        index = 1

        while(1):
            contributionsURL = repoUrl + "/contributors?page= " +  str(index) + "&per_page=100"
            result = self.__requester.makeRequest(contributionsURL)

            if(result.status_code == 200):
                resultJson = result.json()
                index = index + 1

                if not resultJson:
                    break
                else:
                    for contributor in resultJson:
                        login = contributor["login"]
                        contributions = contributor["contributions"]

                        #print("Adding the user with login: " + login)
                        if(self.__databaseService.checkIfGithubUserExist(login) is False):
                            # There is no user entry in our DB with this login info so just fetch and insert it
                            self.__retrieveSingleUser(login)

                        userid = self.__databaseService.getUserIdFromLogin(login)
                        self.__databaseService.insertContribution(userid, repo_id, contributions)

            else: # Request gave an error
                print("Error while retrieving: " + contributionsURL)
                print("Status code: "  + str(result.status_code))

    def __retrieveIssuesofRepo(self, repoURL, repo_id):
        index = 1

        while(1):
            IssuesURL = repoURL + "/issues?page="+ str(index) + "&per_page=100"
            result = self.__requester.makeRequest(IssuesURL)
            print("Issues page: " + str(index))
            if(result.status_code == 200):
                resultJson = result.json()
                index = index + 1

                if not resultJson:
                    break
                else:
                    for issues in resultJson:
                            id = issues["id"]
                            url = issues["url"]
                            number = issues["number"]
                            title =  issues["title"]
                            repo_id = repo_id
                            reporter_id = issues["user"]["id"]
                            assignee_id = None
                            #assignee_id = issues["assignee"]
                            #if assignee_id:
                              # assignee_id =assignee_id["id"]
                            state = issues["state"]
                            comments = issues["comments"]
                            created_at = str(issues["created_at"])[:10]
                            updated_at = str(issues["updated_at"])[:10]
                            print(str(issues["closed_at"]))
                            closed_at = "0000-00-00"
                            if (str(issues["closed_at"]) == "None"):
                                closed_at = "2000-01-01 00:00:00"
                            else:
                                 closed_at = str(issues["closed_at"])[:10]



                            print(issues["number"])
                            print(title)
                            print (closed_at)
                            self.__databaseService.insertIssue(id,url,number,title,repo_id,reporter_id, assignee_id, state,comments, created_at, updated_at, closed_at)

                            print (str(url))

            else: # Request gave an error
                print("Error while retrieving: " + IssuesURL)
                print("Status code: "  + str(result.status_code))

    def __buildTimeParameterString(self, since_date, until_date):
        # Let's build time parameters string for requests that accept time intervals as parameters
        time_param = ""
        if since_date is not None:
            time_param = time_param + "&since=" + since_date
        if until_date is not None:
            time_param = time_param + "&until=" + until_date
        return time_param

