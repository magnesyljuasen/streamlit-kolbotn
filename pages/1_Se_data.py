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

st.title("Data")


st.markdown("---")
#add_vertical_space(5)
if st.button("Gå tilbake til forside"):
    switch_page("Hjem")