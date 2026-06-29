import streamlit as st
from datetime import datetime, date
import backend
import bcrypt
import pandas as pd
import re
@st.experimental_dialog("Add a Task")
def add_task():
    title = st.text_input("Title")
    description = st.text_area("Description")
    cat = backend.get_all_category(username)
    category = st.selectbox("Category", cat)
    cid = backend.get_cid(category, username)
    adddate = date.today()
    duedate = st.date_input("Due Date")
    uid = backend.get_uid(username)
    if st.button("Add"):
        if title.strip() == "":
            st.error("Title cannot be empty")
        elif adddate > duedate:
            st.error("Due Date cannot be earlier than Add Date")
        else:
            backend.add_task(title, 0, adddate, duedate, cid, description,uid)
            st.success("Task added successfully")
            st.rerun()


@st.experimental_dialog("Change Password")
def change_pw():
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

    old_password = st.text_input("Old Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button('Submit'):
        # the stored password is a bcrypt hash, so compare with bcrypt too
        stored_hash = user['password'].encode()
        if bcrypt.checkpw(old_password.encode(), stored_hash):
            validation_error = is_valid_password(new_password)
            if validation_error:
                st.error(validation_error)
            elif new_password != confirm_password:
                st.error("Passwords do not match!")
            else:
                new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                backend.update_user_password(username, new_hash)
                st.success("Password updated successfully!")
                st.rerun()
        else:
            st.error("Old password is not correct!")
st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="wide",
)


# Initialize CookieController

field = {"ID":"tid",
        "Title":"title",
        "Add Date":"adddate",
        "Due Date":"duedate",
        "Description":"description",
        "Category":"cid",
        "Completed":"completed"}

username, login_state = backend.current_state()

authenticator = backend.init_authenticator()
authenticator.logout('Logout', 'sidebar')
if login_state == 0:
    user_row = backend.get_user_by_username(username)
    st.header(f'Welcome back, {user_row["name"]}!')
    tab1, tab2, tab3 = st.tabs(["My Tasks", "Category", "User Info"])
    with tab1:
        st.experimental_dialog("Add Task")
        if "Add Task" not in st.session_state:
            if st.button("Add", key="task"):
                add_task()
        else:
            pass

        tasks = backend.get_tasks(username)
        incompleted_tasks = []
        completed_tasks = []
        for task in tasks:
            if not task[2]:  
                temp = []
                for i in [0, 1, 3, 4, 6]:
                    temp.append(task[i])
                temp.append(backend.get_category(task[5])[0])
                if task[2] == "0":
                    temp.append(True)
                else:
                    temp.append(False)
                
                incompleted_tasks.append(temp)
            
            else:  
                temp2 = []
                for i in [0, 1, 3, 4, 6]:
                    temp2.append(task[i])
                temp2.append(backend.get_category(task[5])[0])
                if task[2] == "1":
                    temp2.append(True)
                else:
                    temp2.append(False)
                
                completed_tasks.append(temp2)

        if incompleted_tasks:
            st.subheader("Incompleted")
            tasks_df = pd.DataFrame(
                incompleted_tasks,
                columns=[
                    "ID",
                    "Title",
                    "Add Date",
                    "Due Date",
                    "Description",
                    "Category",
                    "Completed",
                ],
            )

            edited_tasks_incompleted = st.data_editor(
                tasks_df,column_config={
        "Category": st.column_config.SelectboxColumn(
            "Category",
            help="The category of the app",
            width="medium",
            options=backend.get_all_category(username),
            required=True,
        )
    },  disabled=["ID", "Add Date"] ,
        key="data_editor_incomplete", hide_index=True, width=3000
            )

            # Check if there are changes and update backend
            if edited_tasks_incompleted is not None:
                for index, row in edited_tasks_incompleted.iterrows():
                    original_row = tasks_df.iloc[index]
                    for column in tasks_df.columns:
                        if row[column] != original_row[column]:
                            if column == "Completed":
                                backend.update_task(row["ID"], field[column], 1)
                                st.toast("Updated")
                                st.rerun()
                            elif column == "Category":
                                backend.update_task(row["ID"], field[column], backend.get_cid(row[column], username))
                                st.toast("Updated")
                            elif column == "Due Date":
                                if row[column] < row["Add Date"]:
                                    st.error("Due Date cannot be earlier than Add Date")
                                else:
                                    backend.update_task(row["ID"], field[column], row[column])
                                    st.toast("Updated")
                            else:   
                                backend.update_task(row["ID"], field[column], row[column])
                                st.toast("Updated")

        if completed_tasks:
            st.subheader("Completed")
            tasks_df = pd.DataFrame(
                completed_tasks,
                columns=[
                    "ID",
                    "Title",
                    "Add Date",
                    "Due Date",
                    "Description",
                    "Category",
                    "Completed",
                ],
            )

            edited_tasks_completed = st.data_editor(
                tasks_df,column_config={
        "Category": st.column_config.SelectboxColumn(
            "Category",
            help="The category of the app",
            width="medium",
            options=backend.get_all_category(username),
            required=True,
        )
    },  disabled=["ID", "Add Date"] ,
        key="data_editor_completed", hide_index=True, width=3000
            )

            # Check if there are changes and update backend
            if edited_tasks_completed is not None:
                for index, row in edited_tasks_completed.iterrows():
                    original_row = tasks_df.iloc[index]
                    for column in tasks_df.columns:
                        if row[column] != original_row[column]:
                            if column == "Completed":
                                backend.update_task(row["ID"], field[column], 0)
                                st.toast("Updated")
                                st.rerun()
                            elif column == "Category":
                                backend.update_task(row["ID"], field[column], backend.get_cid(row[column], username))
                                st.toast("Updated")
                            elif column == "Due Date":
                                if row[column] < row["Add Date"]:
                                    st.error("Due Date cannot be earlier than Add Date")
                                else:
                                    backend.update_task(row["ID"], field[column], row[column])
                                    st.toast("Updated")
                            else:   
                                backend.update_task(row["ID"], field[column], row[column])
                                st.toast("Updated")
            if st.button("Delete Completed"):
                backend.delete_completed(username)
                st.success("Sucessfully deleted completed task!")
                st.rerun()
    with tab2:
        category = st.text_input("Add a category: ", placeholder="Category Name")
        if category:
            dup = False
            for i in backend.get_all_category(username):
                if category.lower().strip() == i.lower().strip():
                    dup = True
            if dup:
                st.error("Category cannot be duplicated")
                
            elif category.strip() == "":
                st.error("Category cannot be empty")
            else:
                uid = backend.get_uid(username)
                backend.add_category(category, uid)
                st.success("Category added successfully")
        categories = backend.get_all_category(username)
        df = pd.DataFrame(categories, columns=["Category"]).reset_index(drop=True)
        
        # Add a new column for delete buttons
        df['Delete'] = ["Delete"] * len(df)
        
        # Display the dataframe with delete buttons
        for i, row in df.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(row['Category'])
            with col2:
                if st.button('Delete', key=f"delete_{i}"):
                    backend.delete_category(row['Category'], username)
                    st.toast(f"Category '{row['Category']}' deleted successfully!")
                    st.rerun() 
                
    with tab3:
        user = backend.get_user_by_username(username)
        
        if user:
            if user['icon_path']:
                st.image(user['icon_path'], use_column_width=False, width=200)
            st.subheader(f"Name: {user['name']}")
            st.write(f"Username: {user['username']}")
            st.write(f"Email: {user['email']}")
            st.write(f"Join Date: {user['join_date']}")
        if st.button('Change Password'):
            change_pw()

elif login_state == 1:
    st.error("Token has expired. Please log in again.")

elif login_state == 2:
    st.info("Please login first")
    if st.button("Login →"):
        st.switch_page("auth.py")
else:
    st.info("Please login first")
    if st.button("Login →"):
        st.switch_page("auth.py")
