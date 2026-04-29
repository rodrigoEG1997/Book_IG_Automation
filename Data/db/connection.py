import mysql.connector
from config.settings import DB_HOST, DB_PORT, DB_USER, DB_PASWORD, DB_NAME

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASWORD,
        database=DB_NAME
    )
