import mysql.connector
import os
from flask import g
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Verify database connection on startup."""
    try:
        # Testing the database connection
        test_conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        if test_conn.is_connected():
            print("!!! Database connection successful.")
            test_conn.close()
    except Exception as e:
        print(f"!!! Fatal error:Could not connect to database: {e}")