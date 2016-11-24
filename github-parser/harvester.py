#!/usr/bin/python

import requests
from requester import GitHubRequester
from database_service import DatabaseService


# End point for harvesting GitHub API
class GitHubHarvester:
    def __init__(self, config, secret_config):
        # Generate a github_requester with imported GitHub tokens
        self.__requester = GitHubRequester(secret_config['github-api'])
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def retrieveProjects(self):
        requestURL = "https://api.github.com/search/repositories?q=stars:>5000&page=1&per_page=100"
        res = self.__requester.makeRequest(requestURL)

        if (res.status_code == 200): #API has responded with OK status
            returnJson = res.json()
            indexStart = res.links["last"]["url"].find("page=")
            indexEnd = res.links["last"]["url"].find("&per_page")
            last = res.links["last"]["url"][indexStart+5:indexEnd]

            for i in range(1, int(last)+1):
                print(i)
                requestURL = "https://api.github.com/search/repositories?q=stars:>5000&page=" + str(i) + "&per_page=100"
                res = self.__requester.makeRequest(requestURL)
                returnJson = res.json()

                for project in returnJson["items"]:
                    if project["language"] is None:
                        continue
                    self.__databaseService.insertProject(project)
                    # TODO: Fetch project contributors with https://api.github.com/repos/d3/d3/contributors
                    #       Then fetch project commits with https://developer.github.com/v3/repos/commits/
                    #       Remember that in order to obtain additions deletions GET /repos/:owner/:repo/commits/:sha
                    #           must be initiated for every single commit (might be headache)

        else:
            # TODO Definetly I entercoured with an error from API, what should I do now?
            print('Hatasiz kul olmaz, hatamla sev beni')

        return

    '''
    def retrieveUserInfo(self, userURL):
        res = self.__requester.makeRequest(userURL)
        userData = res.json()

        userId = userData["id"]
        userLogin = userData["login"].encode('utf-8', 'ignore')
        userName = userData["name"]
        if userName is not None:
            userName = userName.encode('utf-8', 'ignore')

        userCompany = userData["company"]
        if userCompany is not None:
            userCompany = userCompany.encode('utf-8', 'ignore')

        userEmail = userData["email"]
        if userEmail is not None:
            userEmail = userEmail.encode('utf-8', 'ignore')

        userBio = userData["bio"]
        if userBio is not None:
            userBio = userBio.encode('utf-8', 'ignore')

        userUrl = userData["url"]

        cursor.execute("""INSERT INTO users(id, login,name,company,email, bio, url) VALUES (%s,%s,%s,%s,%s,%s, %s)
                    ON DUPLICATE KEY UPDATE login = login""",
                    (userId, userLogin, userName, userCompany, userEmail, userBio, userUrl))

        db.commit()
        return
        '''