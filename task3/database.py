import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    
    if os.getenv("IN_DOCKER") or not db_url:
        host = "db" if os.getenv("IN_DOCKER") else os.getenv("POSTGRES_HOST", "localhost")
        user = os.getenv("POSTGRES_USER", "user")
        password = os.getenv("POSTGRES_PASSWORD", "password")
        dbname = os.getenv("POSTGRES_DB", "classicmodels")
        port = "5432" if os.getenv("IN_DOCKER") else os.getenv("POSTGRES_PORT", "5432")
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        
    return psycopg2.connect(db_url)

def execute_query(sql_query: str):
    """
    Executes a SQL query and returns the results as a list of dictionaries.
    Throws an exception if the query fails.
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql_query)
            # If it's not a SELECT or RETURNING, fetchall might fail, but validator ensures it's SELECT
            if cursor.description:
                result = cursor.fetchall()
                # Convert RealDictRow to standard dict for JSON serialization
                return [dict(row) for row in result]
            return []
    finally:
        if conn:
            conn.commit()
            conn.close()
