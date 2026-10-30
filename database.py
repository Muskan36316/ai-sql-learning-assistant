
import os
import mysql.connector
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")


def get_setting(name, default=None):
    try:
        value = st.secrets.get(name)
        if value is not None:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


def get_connection():
    return mysql.connector.connect(
        host=get_setting("DB_HOST", "mysql-2b823613-ai-sql-learning-assistant.d.aivencloud.com"),
        port=int(get_setting("DB_PORT", "23926")),
        user=get_setting("DB_USER", "avnadmin"),
        password=get_setting("DB_PASSWORD"),
        database=get_setting("DB_NAME", "defaultdb"),
        ssl_ca=get_setting("DB_SSL_CA"),
        ssl_verify_cert=True,
        connection_timeout=30
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