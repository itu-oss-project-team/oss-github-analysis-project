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
            `commits`,`repositories`, `users`;
    """)

    db.commit()


def initDB(db):
    cursor = db.cursor()
    cursor.execute("""
-- tables
-- Table: commits
CREATE TABLE commits (
    id int NOT NULL,
    url varchar(255) NOT NULL,
    sha varchar(40) NULL DEFAULT NULL,
    project_id int NOT NULL,
    author_id int NOT NULL,
    committer_id int NOT NULL,
    message text NULL DEFAULT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX sha (sha),
    CONSTRAINT commits_pk PRIMARY KEY (id)
) ENGINE InnoDB CHARACTER SET utf8;

CREATE INDEX committer_id ON commits (committer_id);

CREATE INDEX project_id ON commits (project_id);

CREATE INDEX author_id ON commits (author_id);

-- Table: repositories
CREATE TABLE repositories (
    id int NOT NULL,
    url varchar(255) NULL DEFAULT NULL,
    name varchar(255) NOT NULL,
    full_name varchar(255) NOT NULL,
    description text NULL DEFAULT NULL,
    owner_id int NULL DEFAULT NULL,
    language varchar(255) NULL DEFAULT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NULL DEFAULT NULL,
    stargazers_count int NULL DEFAULT NULL,
    watchers_count int NULL DEFAULT NULL,
    forks_count int NULL DEFAULT NULL,
    UNIQUE INDEX name (name,owner_id),
    CONSTRAINT projects_pk PRIMARY KEY (id)
) ENGINE InnoDB CHARACTER SET utf8;

CREATE INDEX owner_id ON repositories (owner_id);

-- Table: users
CREATE TABLE users (
    id int NOT NULL,
    url varchar(255) NOT NULL,
    login varchar(255) NOT NULL,
    name varchar(255) NULL DEFAULT NULL,
    company varchar(255) NULL DEFAULT NULL,
    email varchar(255) NULL DEFAULT NULL,
    bio text NULL DEFAULT NULL,
    CONSTRAINT id PRIMARY KEY (id)
) CHARACTER SET utf8;

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
    """)

    db.commit()

main()