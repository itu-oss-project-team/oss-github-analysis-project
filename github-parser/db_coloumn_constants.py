class Coloumns:
    class Repo:
        id = 'id'
        url = 'url'
        name = 'name'
        full_name = 'full_name'
        description = 'description'
        owner_id = 'owner_id'
        language = 'language'
        created_at = 'created_at'
        updated_at = 'updated_at'
        stargazers = 'stargazers_count'
        watchers = 'watchers_count'
        forks = 'forks_count'
        filled_at = 'filled_at'

    class User:
        id = 'user_id'
        github_id = 'github_user_id'
        url = 'url'
        login = 'login'
        name = 'name'
        company = 'company'
        bio = 'bio'
        is_github_user = 'is_github_user'

    class FileChanges:
        id = 'id'
        sha = 'sha'
        repo_id = 'repo_id'
        commit_sha = 'commit_sha'
        path = 'file_path'
        status = 'status'
        additions = 'additions'
        deletions = 'deletions'
        changes = 'changes'
        file_id = 'file_id'

    class FilesOfProject:
        id = 'id'
        repo_id = 'repo_id'
        path = 'file_path'