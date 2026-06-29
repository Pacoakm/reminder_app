import streamlit as st
import datetime
import bcrypt
import backend
import re


def hash_password(password):
    # bcrypt hash, salted; stored as bytes -> decode to utf-8 for MySQL
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def is_valid_username(username):
    # username must be lowercase letters / digits / underscores / hyphens, no spaces or capitals
    return re.match(r'^[a-z0-9_-]+$', username) is not None


def is_valid_password(password):
    if len(password) <= 8:
        return "Password must be longer than 8 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    if re.search(r"\s", password):
        return "Password must not contain spaces."
    if re.search(r"[^a-zA-Z0-9]", password):
        return "Password must not contain special characters."
    return None


def register():
    st.title("Register")
    with st.form(key='register_form'):
        username = st.text_input("Username")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button(label='Register')

    if submit_button:
        valid_form = True
        dup_user = False
        dup_email = False

        # backend.get_all_user returns rows of (username, email)
        for i in backend.get_all_user():
            if i[0].lower().strip() == username.lower().strip():
                dup_user = True

        for j in backend.get_all_user():
            if j[1].lower().strip() == email.lower().strip():
                dup_email = True

        if dup_user:
            st.error("Username already used")
            valid_form = False
        if dup_email:
            st.error("Email already used")
            valid_form = False
        if name.strip() == "":
            st.error("Name cannot be empty")
            valid_form = False
        if email.strip() == "":
            st.error("Email cannot be empty")
            valid_form = False
        if not is_valid_username(username):
            st.error("Username must contain only lowercase letters, numbers, underscores, and hyphens, with no spaces or capital letters.")
            valid_form = False

        if password != confirm_password:
            st.error("Passwords do not match!")
            valid_form = False

        pw_error = is_valid_password(password)
        if pw_error:
            st.error(pw_error)
            valid_form = False

        if valid_form:
            hashed_password = hash_password(password)
            join_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            backend.add_user(username, name, email, hashed_password, join_date)
            st.success("User registered successfully!")


if __name__ == "__main__":
    register()
