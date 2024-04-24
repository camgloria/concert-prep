import streamlit as st

st.set_page_config(page_title='Concert Prep', page_icon=':musical_note:')

auth_code = ""
if 'code' in st.query_params:
    auth_code = st.query_params['code']
    st.session_state.auth_code = auth_code

st.title("Concert Prep!")
st.write("This app uses the Spotify and Ticketmaster APIs to help you prepare for an upcoming concert!")
st.sidebar.header("Concert Prep")
st.sidebar.page_link("main.py", label="Home", icon="🎧")
st.sidebar.page_link("pages/playlist_creator.py", label="Playlist Creator", icon="🎤")
st.sidebar.page_link("pages/concert_info.py", label="Concert Info", icon="🎸")
st.sidebar.page_link("pages/vibe_checker.py", label="Vibe Checker", icon="🎶")