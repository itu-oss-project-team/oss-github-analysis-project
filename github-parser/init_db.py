import os.path
import pymysql
import yaml


def main():
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
        config = yaml.load(ymlfile)

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    mysql_config = secret_config['mysql']
    db = pymysql.connect(host=mysql_config['host'], port=mysql_config['port'], db=mysql_config['db'],
                                user=mysql_config['user'],
                                passwd=mysql_config['passwd'])

    print("Dropping tables from \"" + mysql_config['db'] + "\"...")
    clearDB(db)
    print("Tables dropped")
    print("Creating tables on \"" + mysql_config['db'] + "\"...")
    initDB(db)
    print("Tables created.")


def clearDB(db):
    cursor = db.cursor()
    cursor.execute("""
            DROP TABLE IF EXISTS
            `filestats`, `projectstats`, `contributings`, `filechanges`, `commits`, `filesofproject`,`issues`, `repositories`, `users`;
    """)

    db.commit()


def initDB(db):
    cursor = db.cursor()
    cursor.execute("""
        -- tables
        -- Table: commits
        CREATE TABLE commits (
            id bigint NOT NULL AUTO_INCREMENT,
            sha varchar(191) NULL,
            url varchar(191) NOT NULL,
            repo_id int NOT NULL,
            author_id int NULL,
            committer_id int NULL,
            message text NULL DEFAULT NULL,
            created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            additions int NULL,
            deletions int NULL,
            UNIQUE INDEX sha (sha),
            CONSTRAINT commits_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        CREATE INDEX committer_id ON commits (committer_id);

        CREATE INDEX project_id ON commits (repo_id);

        CREATE INDEX author_id ON commits (author_id);

        -- Table: contributings
        CREATE TABLE contributings (
            user_id int NOT NULL,
            repo_id int NOT NULL,
            contributions int NULL
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        -- Table: filechanges
        CREATE TABLE filechanges (
            id bigint NOT NULL AUTO_INCREMENT,
            sha varchar(191) NOT NULL,
            repo_id int NOT NULL,
            file_path varchar(191) NULL,
            status varchar(191) NULL,
            additions int NULL,
            deletions int NULL,
            changes int NULL,
            commit_id bigint NOT NULL,
            commit_sha varchar(191) NULL,
            file_id bigint NOT NULL,
            CONSTRAINT filechanges_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        -- Table: filesofproject
        CREATE TABLE filesofproject (
            id bigint NOT NULL AUTO_INCREMENT,
            repo_id int NOT NULL,
            file_path varchar(191) NOT NULL,
            CONSTRAINT filesofproject_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        CREATE  UNIQUE INDEX filesofproject_idx_1 ON filesofproject (repo_id,file_path);

        -- Table: filestats
        CREATE TABLE filestats (
            id int NOT NULL AUTO_INCREMENT,
            repo_id int NOT NULL,
            project_full_name varchar(191) NOT NULL,
            file_path varchar(191) NOT NULL,
            no_of_commits int NULL,
            first_commit_date timestamp NULL,
            last_commit_date timestamp NULL,
            commit_frequency float NULL,
            no_of_developers int NULL,
            top_developer_id int NULL,
            CONSTRAINT filestats_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        CREATE  UNIQUE INDEX filestats_idx_1 ON filestats (repo_id,file_path);

        -- Table: issues
        CREATE TABLE issues (
            id int NOT NULL,
            url varchar(191) NOT NULL,
            number int NULL,
            title text NULL,
            repo_id int NOT NULL,
            reporter_id int NOT NULL,
            assignee_id int NULL,
            state varchar(191) NULL,
            comments int NULL,
            created_at timestamp NULL,
            updated_at timestamp NULL,
            closed_at int NULL,
            CONSTRAINT issues_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        -- Table: projectstats
        CREATE TABLE projectstats (
            id int NOT NULL AUTO_INCREMENT,
            repo_id int NOT NULL,
            start_date timestamp NULL,
            end_date timestamp NULL,
            no_of_commits int NULL,
            no_of_contributors int NULL,
            no_of_changed_files int NULL,
            no_of_file_changes int NULL,
            CONSTRAINT projectstats_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        -- Table: repositories
        CREATE TABLE repositories (
            id int NOT NULL,
            url varchar(191) NULL DEFAULT NULL,
            name varchar(191) NOT NULL,
            full_name varchar(191) NOT NULL,
            description text NULL DEFAULT NULL,
            owner_id int NOT NULL,
            language varchar(191) NULL DEFAULT NULL,
            created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp NULL DEFAULT NULL,
            stargazers_count int NULL DEFAULT NULL,
            watchers_count int NULL DEFAULT NULL,
            forks_count int NULL DEFAULT NULL,
            filled_at timestamp NULL DEFAULT NULL,
            UNIQUE INDEX name (name,owner_id),
            CONSTRAINT projects_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        CREATE INDEX owner_id ON repositories (owner_id);

        -- Table: users
        CREATE TABLE users (
            user_id int NOT NULL AUTO_INCREMENT,
            github_user_id int NULL,
            url varchar(191) NULL,
            login varchar(191) NULL,
            name varchar(191) NULL DEFAULT NULL,
            company varchar(191) NULL DEFAULT NULL,
            email varchar(191) NULL DEFAULT NULL,
            bio text NULL DEFAULT NULL,
            is_github_user bool NOT NULL,
            CONSTRAINT users_pk PRIMARY KEY (user_id)
        ) CHARACTER SET utf8mb4;

        -- foreign keys
        -- Reference: contributings_repositories (table: contributings)
        ALTER TABLE contributings ADD CONSTRAINT contributings_repositories FOREIGN KEY contributings_repositories (repo_id)
            REFERENCES repositories (id);

        -- Reference: contributings_users (table: contributings)
        ALTER TABLE contributings ADD CONSTRAINT contributings_users FOREIGN KEY contributings_users (user_id)
            REFERENCES users (user_id);

        -- Reference: filechanges_filesofproject (table: filechanges)
        ALTER TABLE filechanges ADD CONSTRAINT filechanges_filesofproject FOREIGN KEY filechanges_filesofproject (file_id)
            REFERENCES filesofproject (id);

        -- Reference: fk_commits_authors (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_authors FOREIGN KEY fk_commits_authors (committer_id)
            REFERENCES users (user_id);

        -- Reference: fk_commits_committers (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_committers FOREIGN KEY fk_commits_committers (author_id)
            REFERENCES users (user_id);

        -- Reference: fk_commits_repositories (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_repositories FOREIGN KEY fk_commits_repositories (repo_id)
            REFERENCES repositories (id);

        -- Reference: fk_filechanges_commits (table: filechanges)
        ALTER TABLE filechanges ADD CONSTRAINT fk_filechanges_commits FOREIGN KEY fk_filechanges_commits (commit_id)
            REFERENCES commits (id);

        -- Reference: fk_filechanges_repositories (table: filechanges)
        ALTER TABLE filechanges ADD CONSTRAINT fk_filechanges_repositories FOREIGN KEY fk_filechanges_repositories (repo_id)
            REFERENCES repositories (id);

        -- Reference: fk_filesofproject_repositories (table: filesofproject)
        ALTER TABLE filesofproject ADD CONSTRAINT fk_filesofproject_repositories FOREIGN KEY fk_filesofproject_repositories (repo_id)
            REFERENCES repositories (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;

        -- Reference: fk_filestats_repositories (table: filestats)
        ALTER TABLE filestats ADD CONSTRAINT fk_filestats_repositories FOREIGN KEY fk_filestats_repositories (repo_id)
            REFERENCES repositories (id);

        -- Reference: fk_filestats_users (table: filestats)
        ALTER TABLE filestats ADD CONSTRAINT fk_filestats_users FOREIGN KEY fk_filestats_users (top_developer_id)
            REFERENCES users (user_id);

        -- Reference: fk_projectstats_repositories (table: projectstats)
        ALTER TABLE projectstats ADD CONSTRAINT fk_projectstats_repositories FOREIGN KEY fk_projectstats_repositories (repo_id)
            REFERENCES repositories (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;

        -- Reference: fk_repositories_users (table: repositories)
        ALTER TABLE repositories ADD CONSTRAINT fk_repositories_users FOREIGN KEY fk_repositories_users (owner_id)
            REFERENCES users (user_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;

        -- Reference: issues_repositories (table: issues)
        ALTER TABLE issues ADD CONSTRAINT issues_repositories FOREIGN KEY issues_repositories (repo_id)
            REFERENCES repositories (id);

        -- Reference: issues_users (table: issues)
        ALTER TABLE issues ADD CONSTRAINT issues_users FOREIGN KEY issues_users (assignee_id)
            REFERENCES users (user_id);

        -- End of file.
    """)

    db.commit()

main()
