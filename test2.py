import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
load_dotenv()

# Get the environment variables
db_host = os.getenv("DB_HOST")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
cookie_key = os.getenv("COOKIE_KEY")


def test_ssl_connection():
    try:
        connection = mysql.connector.connect(
            host=db_host,
            user=db_username,
            password=db_password,
            database=db_name,
            ssl_cert='/home/pacoakm/domain.crt',
            ssl_ca='/home/pacoakm/root_bundle.crt',
            ssl_key='/home/pacoakm/privkey.key',
        )
        if connection.is_connected():
            print("Connection successful")
            connection.close()
    except Error as e:
        print(f"Error: {e}")

test_ssl_connection()