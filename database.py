
import os
import mysql.connector
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "SQLAssiatant")
    )


def save_query_history(query_text, rows_returned, status="Success"):
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO query_history
            (query_text, rows_returned, status)
            VALUES (%s, %s, %s)
        """
        cursor.execute(
            sql,
            (query_text, rows_returned, status)
        )
        connection.commit()

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()