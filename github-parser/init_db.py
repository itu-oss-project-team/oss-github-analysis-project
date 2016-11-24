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
    clearDB(db)
    initDB(db)


def clearDB(db):
    cursor = db.cursor()
    cursor.execute("""
            DROP TABLE IF EXISTS
            `commits`, `issues`, `repositories`, `users`;
    """)

    db.commit()


def initDB(db):
    cursor = db.cursor()
    cursor.execute("""


            -- tables

            -- Table: commits
            CREATE TABLE commits (
                id int(11) NOT NULL,
                sha varchar(40) NULL DEFAULT NULL,
                author_id int(11) NOT NULL,
                committer_id int(11) NOT NULL,
                project_id int(11) NULL DEFAULT NULL,
                created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                message text NULL,
                url varchar(255) NOT NULL,
                UNIQUE INDEX sha (sha),
                CONSTRAINT commits_pk PRIMARY KEY (id)
            ) ENGINE InnoDB;

            CREATE INDEX committer_id ON commits (committer_id);

            CREATE INDEX project_id ON commits (project_id);

            CREATE INDEX author_id ON commits (author_id);

            -- Table: issues
            CREATE TABLE issues (
                id int(11) NOT NULL,
                repo_id int(11) NULL DEFAULT NULL,
                reporter_id int(11) NULL DEFAULT NULL,
                assignee_id int(11) NULL DEFAULT NULL,
                pull_request tinyint(1) NOT NULL,
                pull_request_id int(11) NULL DEFAULT NULL,
                created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                issue_id int(11) NOT NULL,
                CONSTRAINT issues_pk PRIMARY KEY (id)
            ) ENGINE InnoDB;

            CREATE INDEX repo_id ON issues (repo_id);

            CREATE INDEX reporter_id ON issues (reporter_id);

            CREATE INDEX assignee_id ON issues (assignee_id);

            CREATE INDEX issue_id ON issues (issue_id);

            -- Table: repositories
            CREATE TABLE repositories (
                id int(11) NOT NULL,
                url varchar(255) NULL,
                owner_id int(11) NOT NULL,
                name varchar(255) NOT NULL,
                full_name varchar(255) NOT NULL,
                description varchar(255) NULL DEFAULT NULL,
                language varchar(255) NULL DEFAULT NULL,
                created_at timestamp NULL,
                updated_at timestamp NULL,
                stargazers_count int NOT NULL,
                watchers_count int NOT NULL,
                forks_count int NOT NULL,
                html_url varchar(255) NULL,
                UNIQUE INDEX name (name,owner_id),
                CONSTRAINT projects_pk PRIMARY KEY (id)
            ) ENGINE InnoDB;

            CREATE INDEX owner_id ON repositories (owner_id);

            -- Table: users
            CREATE TABLE users (
                id int(11) NOT NULL,
                login varchar(255) NOT NULL,
                name varchar(255) NULL,
                email varchar(255) NULL,
                company varchar(255) NULL,
                bio text NULL,
                url varchar(255) NOT NULL,
                CONSTRAINT id PRIMARY KEY (id)
            );

            -- foreign keys

            -- Reference: fk_repositories_owner_id (table: users)
            ALTER TABLE repositories ADD CONSTRAINT fk_repositories_owner_id FOREIGN KEY fk_repositories_owner_id (owner_id)
                REFERENCES users (id);

            -- Reference: fk_commits_authors (table: commits)
            ALTER TABLE commits ADD CONSTRAINT fk_commits_authors FOREIGN KEY fk_commits_authors (committer_id)
                REFERENCES users (id);

            -- Reference: fk_commits_committers (table: commits)
            ALTER TABLE commits ADD CONSTRAINT fk_commits_committers FOREIGN KEY fk_commits_committers (author_id)
                REFERENCES users (id);

            -- Reference: fk_commits_repositories (table: commits)
            ALTER TABLE commits ADD CONSTRAINT fk_commits_repositories FOREIGN KEY fk_commits_repositories (project_id)
                REFERENCES repositories (id);

            -- Reference: fk_issues_repositories (table: issues)
            ALTER TABLE issues ADD CONSTRAINT fk_issues_repositories FOREIGN KEY fk_issues_repositories (repo_id)
                REFERENCES repositories (id);
    """)

    db.commit()

main()