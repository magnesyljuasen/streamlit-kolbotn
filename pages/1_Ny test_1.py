import streamlit as st
import streamlit_authenticator as stauth
import yaml
import pandas as pd
import numpy as np
import base64
from PIL import Image
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.add_vertical_space import add_vertical_space
from src.scripts import streamlit_settings, switch_pages, toggle_closed_expander

def well_placement_input(text_string):
    if text_string == "Skriv inn adresse":
        st.info("def adressefunksjon()")
    elif text_string == "Skriv inn koordinater":
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("NS", value = 63)
        with c2:
            long = st.number_input("ØV", value = 10)

streamlit_settings()

#st session state
if 'project_name' not in st.session_state:
    st.session_state.project_name = None
if 'lat' not in st.session_state:
    st.session_state.lat = None
if 'long' not in st.session_state:
    st.session_state.long = None


if "info_expanded" not in st.session_state:
    st.session_state.info_expanded = True
if "check" not in st.session_state:
    st.session_state.check = False

if st.session_state.check == True:
    check = "✅"
else:
    check = "✗"
with st.expander(f"{check} Informasjon om prosjektet", expanded=st.session_state.info_expanded):
    #with st.form("Informasjon om prosjektet"):
    project_name = st.text_input("Navn på prosjektet")
    if len(project_name) > 0:
        st.session_state.project_name = project_name

    if project_name == "Bygdehaven":
        st.warning("Mente du det allerede eksisterende prosjektet Bygdehaven?")
        if st.button("Gå til eksisterende prosjekt"):
            switch_page("Eksisterende_test")
    well_placement_input(selectbox("Plassering av brønn", ["Skriv inn adresse", "Skriv inn koordinater", "Plasser i kart"], no_selection_label="Velg"))
    well_id = st.number_input("Brønn ID GRANADA", value = 70135532)
    contact_person = st.text_input(f"Kontaktperson")

    if len(project_name) > 0 and len(contact_person) > 0:
        toggle_closed_expander("info_expanded")
        #st.form_submit_button("Registrer", on_click=toggle_closed_expander("info_expanded"))


with st.expander("Brønn og kollektor"):
    with st.form("Brønn og kollektor"):
        collector_type = selectbox("Kollektortype", ["Enkel-U", "Dobbel-U"], no_selection_label="Velg", key = "bk1")
        collector_fluid = selectbox("Kollektorvæske", ["HX24", "HX35"], no_selection_label="Velg", key = "bk2")
        collector_fluid = selectbox("Lengde kollektor", ["300 m", "250 m"], no_selection_label="Velg", key = "bk3")
        casing_diameter = selectbox("Diameter foringsrør", ["139 mm"], no_selection_label="Velg", key = "bk4")
        st.form_submit_button("Registrer")

with st.expander("Temperaturprofil før"):
    date = st.date_input("Dato", value = "today")
    ground_water_level = st.number_input("Grunnvansnivå [m]", value = 5)
    depth_array = np.arange(0, 305, 5)
    temperature_array = np.arange(0, 305, 5)
    df = pd.DataFrame({
        "Dyp [m]" : depth_array,
        "Temperatur [°C]" : temperature_array
    }
    )
    edited_df = st.data_editor(df, hide_index = True)

with st.expander("Temperaturprofil etter"):
    with st.form("Temperaturprofil etter"):
        st.info("Input")
        st.form_submit_button("Registrer")

comment = st.text_area("Eventuelle kommentarer")
uploaded_files = st.file_uploader("Last opp eventuelle vedlegg (bilder, testdata, andre filer)", accept_multiple_files=True)

switch_pages(previous_page_destination="Hjem", previous_page_text="Forrige", next_page_destination="Neste", next_page_text = "Ny_test_2")