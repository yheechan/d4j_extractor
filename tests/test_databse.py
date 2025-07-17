from lib.database import Database

import os
from dotenv import load_dotenv

def test_database_connection():
    load_dotenv()
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB")

    if not all([db_host, db_port, db_user, db_password, db_name]):
        print("Database environment variables are not set correctly.")
        return

    db = Database(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        slack_channel=os.environ.get("SLACK_CHANNEL"),
        slack_token=os.environ.get("SLACK_TOKEN")
    )

    assert db is not None, "Database connection should be established."