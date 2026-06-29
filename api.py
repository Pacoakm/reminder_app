from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import jwt

load_dotenv()

app = Flask(__name__)
CORS(app)

# Get the environment variables
db_host = os.getenv("DB_HOST")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
cookie_key = os.getenv("COOKIE_KEY")


def create_connection():
    try:
        connection = mysql.connector.connect(
            host=db_host, user=db_username, password=db_password, database=db_name
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None


@app.route("/add_task", methods=["POST"])
def add_task():
    data = request.json
    title = data["title"]
    completed = data["completed"]
    adddate = data["adddate"]
    duedate = data["duedate"]
    cid = data["cid"]
    description = data["description"]
    uid = data["uid"]

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        add_task_query = """
        INSERT INTO tasks (title, completed, adddate, duedate, cid, description, uid)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            add_task_query, (title, completed, adddate, duedate, cid, description, uid)
        )
        connection.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 500


@app.route("/get_tasks/<username>", methods=["GET"])
def get_tasks(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE uid IN (SELECT uid FROM user WHERE username = %s)",
            (username,),
        )
        rows = cursor.fetchall()
        return jsonify(rows)
    return jsonify([]), 500


@app.route("/get_all_category/<username>", methods=["GET"])
def get_all_category(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT cname FROM category WHERE uid = (SELECT uid FROM user WHERE username = %s)",
            (username,),
        )
        rows = cursor.fetchall()
        return jsonify([row[0] for row in rows])
    return jsonify([]), 500


@app.route("/get_category/<cid>", methods=["GET"])
def get_category(cid):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT cname FROM category WHERE cid = %s", (cid,))
        row = cursor.fetchone()
        return jsonify(row[0] if row else "")
    return jsonify(""), 500


@app.route("/update_logged_in", methods=["POST"])
def update_logged_in():
    data = request.json
    username = data["username"]
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET logged_in = TRUE WHERE username = %s", (username,)
        )
        connection.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 500


@app.route("/update_logged_out", methods=["POST"])
def update_logged_out():
    data = request.json
    username = data["username"]
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET logged_in = FALSE WHERE username = %s", (username,)
        )
        connection.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 500


@app.route("/get_cid/<username>/<cname>", methods=["GET"])
def get_cid(username, cname):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT cid FROM category WHERE cname = %s AND uid = (SELECT uid FROM user WHERE username = %s)",
            (cname, username),
        )
        row = cursor.fetchone()
        return jsonify(row[0] if row else None)
    return jsonify(None), 500


@app.route("/get_uid/<username>", methods=["GET"])
def get_uid(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT uid FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
        return jsonify(row[0] if row else None)
    return jsonify(None), 500


@app.route("/get_user_by_username/<username>", methods=["GET"])
def get_user_by_username(username):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM user WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return jsonify(user)


@app.route("/update_user_password", methods=["POST"])
def update_user_password():
    data = request.json
    username = data["username"]
    new_password = data["new_password"]
    connection = create_connection()
    cursor = connection.cursor()
    query = "UPDATE user SET password = %s WHERE username = %s"
    cursor.execute(query, (new_password, username))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"success": True})


@app.route("/delete_completed/<username>", methods=["DELETE"])
def delete_completed(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        delete_task_query = "DELETE FROM tasks WHERE completed = 1 AND uid = (SELECT uid FROM user WHERE username = %s)"
        cursor.execute(delete_task_query, (username,))
        connection.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 500


@app.route("/update_task", methods=["POST"])
def update_task():
    data = request.json
    task_id = data["task_id"]
    column = data["column"]
    new_value = data["new_value"]
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            f"UPDATE tasks SET {column} = %s WHERE tid = %s", (new_value, task_id)
        )
        connection.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 500
import bcrypt

def check_password(username, password):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and password.encode('utf-8') == user['password'].encode('utf-8'):
            return True
    return False

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    
    if check_password(username, password):
        return jsonify({"success": True, "message": "Login successful!"})
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)