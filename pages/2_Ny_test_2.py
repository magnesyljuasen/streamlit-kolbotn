import streamlit as st
import streamlit_authenticator as stauth
import yaml
import base64
from PIL import Image
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.add_vertical_space import add_vertical_space
from src.scripts import streamlit_settings, switch_pages

streamlit_settings()

if st.session_state.project_name != 0:
    st.header(st.session_state.project_name)

if st.button("Lagre utkast"):
    st.success("Takk! Utkastet er lagret", icon = "✅")

if st.button("Send inn ferdig utfylt skjema"):
    st.success("Takk! ditt skjema er innsendt", icon = "✅")

switch_pages(previous_page_destination="Ny_test_1", previous_page_text="Forrige", next_page_destination="Gå tilbake til forside", next_page_text = "Hjem")