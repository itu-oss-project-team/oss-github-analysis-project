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
            `filechanges`, `commits`, `filesofproject`, `repositories`, `users`;
    """)

    db.commit()


def initDB(db):
    cursor = db.cursor()
    cursor.execute("""
        -- tables
        -- Table: commits
        CREATE TABLE commits (
            sha varchar(191) NOT NULL,
            url varchar(191) NOT NULL,
            project_id int NOT NULL,
            author_id int NULL,
            committer_id int NULL,
            message text NULL DEFAULT NULL,
            created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            additions int NULL,
            deletions int NULL,
            UNIQUE INDEX sha (sha),
            CONSTRAINT commits_pk PRIMARY KEY (sha)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        CREATE INDEX committer_id ON commits (committer_id);

        CREATE INDEX project_id ON commits (project_id);

        CREATE INDEX author_id ON commits (author_id);

        -- Table: filechanges
        CREATE TABLE filechanges (
            sha varchar(191) NOT NULL,
            project_id int NOT NULL,
            commit_sha varchar(191) NOT NULL,
            filename varchar(191) NULL,
            status varchar(191) NULL,
            additions int NULL,
            deletions int NULL,
            changes int NULL,
            CONSTRAINT filechanges_pk PRIMARY KEY (sha)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        -- Table: filesofproject
        CREATE TABLE filesofproject (
            filename varchar(191) NOT NULL,
            project_id int NOT NULL,
            CONSTRAINT file_name PRIMARY KEY (filename)
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
            UNIQUE INDEX name (name,owner_id),
            CONSTRAINT projects_pk PRIMARY KEY (id)
        ) ENGINE InnoDB CHARACTER SET utf8mb4;

        CREATE INDEX owner_id ON repositories (owner_id);

        -- Table: users
        CREATE TABLE users (
            id int NOT NULL,
            url varchar(191) NOT NULL,
            login varchar(191) NOT NULL,
            name varchar(191) NULL DEFAULT NULL,
            company varchar(191) NULL DEFAULT NULL,
            email varchar(191) NULL DEFAULT NULL,
            bio text NULL DEFAULT NULL,
            CONSTRAINT id PRIMARY KEY (id)
        ) CHARACTER SET utf8mb4;

        -- foreign keys
        -- Reference: fk_commits_authors (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_authors FOREIGN KEY fk_commits_authors (committer_id)
            REFERENCES users (id);

        -- Reference: fk_commits_committers (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_committers FOREIGN KEY fk_commits_committers (author_id)
            REFERENCES users (id);

        -- Reference: fk_commits_repositories (table: commits)
        ALTER TABLE commits ADD CONSTRAINT fk_commits_repositories FOREIGN KEY fk_commits_repositories (project_id)
            REFERENCES repositories (id);

        -- Reference: fk_filechanges_commits (table: filechanges)
        ALTER TABLE filechanges ADD CONSTRAINT fk_filechanges_commits FOREIGN KEY fk_filechanges_commits (commit_sha)
            REFERENCES commits (sha);

        -- Reference: fk_filechanges_repositories (table: filechanges)
        ALTER TABLE filechanges ADD CONSTRAINT fk_filechanges_repositories FOREIGN KEY fk_filechanges_repositories (project_id)
            REFERENCES repositories (id);

        -- Reference: fk_filesofproject_repositories (table: filesofproject)
        ALTER TABLE filesofproject ADD CONSTRAINT fk_filesofproject_repositories FOREIGN KEY fk_filesofproject_repositories (project_id)
            REFERENCES repositories (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;

        -- Reference: fk_repositories_users (table: repositories)
        ALTER TABLE repositories ADD CONSTRAINT fk_repositories_users FOREIGN KEY fk_repositories_users (owner_id)
            REFERENCES users (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    """)



    db.commit()

main()