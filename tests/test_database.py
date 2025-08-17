from lib.database import *

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

def test_crud():
    load_dotenv()
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB")

    if not all([db_host, db_port, db_user, db_password, db_name]):
        print("Database environment variables are not set correctly.")
        return

    crud = CRUD(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        slack_channel=os.environ.get("SLACK_CHANNEL"),
        slack_token=os.environ.get("SLACK_TOKEN")
    )

    # Create a test table
    crud.create_table("test_table", "id SERIAL PRIMARY KEY, name VARCHAR(100)")
    
    # Insert a record
    crud.insert("test_table", "name", ["HeechanYang"])
    
    # Read the record back
    result = crud.read("test_table", conditions={"name": "HeechanYang"})
    
    assert len(result) == 1, "Should have inserted one record."
    assert result[0][1] == "HeechanYang", "Inserted record should match the expected value."

    # Clean up
    crud.drop_table("test_table")

def test_list_insertion():
    load_dotenv()

    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB")

    if not all([db_host, db_port, db_user, db_password, db_name]):
        print("Database environment variables are not set correctly.")
        return

    crud = CRUD(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        slack_channel=os.environ.get("SLACK_CHANNEL"),
        slack_token=os.environ.get("SLACK_TOKEN")
    )

    # Create a test table
    crud.create_table("test_table", "id SERIAL PRIMARY KEY, key TEXT, float_list REAL[]")

    # Insert a record
    crud.insert("test_table", "key, float_list", ["hcy", [1.1, 2.2, 3.3]])

    # Read the record back
    result = crud.read("test_table", columns="float_list", conditions={"key": "hcy"})

    assert len(result) == 1, "Should have inserted one record."
    assert result[0][0] == [1.1, 2.2, 3.3], "Inserted record should match the expected value."

    # Clean up
    crud.drop_table("test_table")
