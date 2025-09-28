import os

from dotenv import load_dotenv, find_dotenv
import psycopg2

load_dotenv(find_dotenv())

def test_pg_connection():
    pg_connection = conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

    cursor = pg_connection.cursor()
    cursor.execute("SELECT version();")
    print(cursor.fetchone())
