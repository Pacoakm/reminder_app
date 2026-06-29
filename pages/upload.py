import streamlit as st
import backend
import os
uploaded_file = st.file_uploader("Upload your profile picture", type=["png", "jpg", "jpeg"])
username, logged_in = backend.current_state()

if uploaded_file is not None:
    # Define the path to save the file
    save_path = f"uploads/{username}"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    file_path = os.path.join(save_path, "icon.png")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    uid = backend.get_uid(username)
    backend.store_user_icon(uid, icon_path=file_path)
    st.success("Profile picture uploaded successfully!")