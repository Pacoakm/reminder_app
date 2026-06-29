import streamlit as st
import backend

authenticator = backend.init_authenticator()

# streamlit-authenticator >= 0.3 stores the result in st.session_state instead of returning it
authenticator.login()

if st.session_state.get("authentication_status"):
    st.success(f"Welcome {st.session_state.get('name')}!")
    authenticator.logout("Logout", "sidebar")

elif st.session_state.get("authentication_status") is False:
    st.error("Username or password is incorrect")
elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your username and password")
