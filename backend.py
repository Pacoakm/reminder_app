import streamlit as st
import streamlit_authenticator as stauth
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime
from streamlit_cookies_controller import CookieController
import jwt
from dotenv import load_dotenv
import os

load_dotenv()

# Get the environment variables
db_host = os.getenv("DB_HOST")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
cookie_key = os.getenv("COOKIE_KEY")

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user=db_username,
            password=db_password,
            database=db_name
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None
def add_user(username, name, email, password, join_date):
    # register.py should already bcrypt the password before calling us
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        add_task_query = """
        INSERT INTO user (username, name, email, password, join_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(add_task_query, (username, name, email, password, join_date))
        connection.commit()
        cursor.close()
        connection.close()
        return True

    return False
def add_task(title, completed, adddate, duedate, cid, description, uid):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        add_task_query = """
        INSERT INTO tasks (title, completed, adddate, duedate, cid, description, uid)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(add_task_query, (title, completed, adddate, duedate, cid, description, uid))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    return False

def add_category(category, uid):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        add_task_query = """
        INSERT INTO category (cname, uid)
        VALUES (%s, %s)
        """
        cursor.execute(add_task_query, (category, uid))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    return False


def get_tasks(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tasks where uid in (select uid from user where username = %s)", (username,))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return rows
    return []


def get_all_category(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT cname FROM category where uid = (select uid from user where username = %s)", (username,))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return list (i[0] for i in rows)
    return []

def get_category(cid):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT cname from category where cid = %s", (cid,))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return rows[0]
    return []


def update_logged_in(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET logged_in = TRUE WHERE username = %s", (username,)
        )
        connection.commit()
        cursor.close()
        connection.close()


def update_logged_out(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET logged_in = FALSE WHERE username = %s",
            (username,),
        )
        connection.commit()
        cursor.close()
        connection.close()


def get_cid(cname, username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT cid FROM category where cname = %s and uid = (select uid from user where username = %s)", (cname, username))
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if row == None:
            return row
        else:
            return row[0]
    return []


def get_uid(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT uid from user where username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        return row[0]
    return []


def get_user_by_username(username):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM user WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user


def update_user_password(username, new_password):
    # new_password is expected to already be bcrypt-hashed by the caller
    connection = create_connection()
    cursor = connection.cursor()
    query = "UPDATE user SET password = %s WHERE username = %s"
    cursor.execute(query, (new_password, username))
    connection.commit()
    cursor.close()
    connection.close()


def delete_completed(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        delete_task_query = "DELETE FROM tasks WHERE completed = 1 and uid = (select uid from user where username = %s) "
        cursor.execute(delete_task_query, (username,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    return False


def delete_category(category, username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        uid = get_user_by_username(username)['uid']
        delete_query = "DELETE FROM category WHERE cname = %s and uid = %s "
        cursor.execute(delete_query, (category, uid))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    return False


def update_task(task_id, column, new_value):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE tasks SET %s = %s WHERE tid = %s",
            (column, new_value, task_id),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    return False

def init_authenticator():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    # password is bcrypt-hashed in the DB; streamlit-authenticator accepts hashed passwords
    query = "SELECT username, name, email, password FROM user"
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()
    connection.close()

    authenticator_credentials = {
        'usernames': {
            user['username']: {
                'name': user['name'],
                'email': user['email'],
                'password': user['password'],
            } for user in users
        }
    }

    authenticator = stauth.Authenticate(
        authenticator_credentials,
        'sessionid',
        cookie_key,
        cookie_expiry_days=30,
    )
    return authenticator


def current_state():
    login_state = -1
    controller = CookieController()
    username = -1
    try:
        token = controller.get("sessionid")
        decoded_token = jwt.decode(token, cookie_key, algorithms=["HS256"])
        username = decoded_token.get("username")
        login_state = 0
    except jwt.ExpiredSignatureError:
        login_state = 1
    except jwt.InvalidTokenError:
        login_state = 2
    return username, login_state

def store_user_icon(uid, icon_path):
    connection = create_connection()
    cursor = connection.cursor()
    query = "UPDATE user SET icon_path = %s WHERE uid = %s"
    cursor.execute(query, (icon_path, uid))
    connection.commit()
    cursor.close()
    connection.close()

def get_all_user():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT username, email FROM user")
        rows = cursor.fetchall()
        return rows
    return []
# if __name__ == "__main__":
#     # Test the functions
#     success = add_task(
#         "user123",
#         "Complete Python project",
#         False,
#         datetime.now().date(),
#         datetime(2024, 7, 1).date(),
#         "Programming",
#         "Finish the school-based assessment task for ICT.",
#     )
#     print("Task added:", success)

#     tasks = get_tasks()
#     print("Tasks:", tasks)

#     task = get_task(1)  # Example task_id to get
#     print("Task:", task)

#     deleted = delete_task(1)  # Example task_id to delete
#     print("Task deleted:", deleted)

#     updated = update_task(
#         2, "title", "Updated Task Title"
#     )  # Example task_id and new value
#     print("Task updated:", updated)
