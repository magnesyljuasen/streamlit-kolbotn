import streamlit as st
import streamlit_authenticator as stauth
import yaml
import base64
from PIL import Image
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.add_vertical_space import add_vertical_space

st.set_page_config(page_title="TRT", layout="centered", page_icon="src/data/img/AsplanViak_Favicon_32x32.png", initial_sidebar_state="collapsed")

with open("src/styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    st.markdown("""<style>[data-testid="collapsedControl"] {display: none}</style>""", unsafe_allow_html=True) # ingen sidebar
    st.markdown("""<style>div[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True) # litt av sidebar
    st.markdown('''<style>button[title="View fullscreen"]{visibility: hidden;}</style>''', unsafe_allow_html=True) # hide fullscreen
    st.markdown("""<style>.block-container {padding-top: 1rem;padding-bottom: 0rem;padding-left: 5rem;padding-right: 5rem;}</style>""", unsafe_allow_html=True)

st.title("Kontakt oss")
st.markdown("---")
st.write("Magne Syljuåsen")
st.write("✆ 451 92 540")
st.write("✉ magne.syljuasen@asplanviak.no")
st.markdown("---")
st.write("Sofie Hartvigsen")
st.write("✆ 948 38 786")
st.write("✉ sofie.hartvigsen@asplanviak.no")
st.markdown("---")
st.write("Johanne Strålberg")
st.write("✆ 948 47 316")
st.write("✉ johanne.stralberg@asplanviak.no") 
st.markdown("---")
st.write("Henrik Holmberg")
st.write("✆ 957 49 363")
st.write("✉ henrik.holmberg@asplanviak.no") 
st.markdown("---")
st.write("Randi Kalskin Ramstad")
st.write("✆ 975 13 942")    
st.write("✉ randi.kalskin.ramstad@asplanviak.no")
st.markdown("---")

st.info("Rapporter problem (her kommer det et skjema)")

st.markdown("---")
#add_vertical_space(5)
if st.button("Gå tilbake til forside"):
    switch_page("Hjem")



