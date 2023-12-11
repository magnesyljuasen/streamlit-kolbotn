import streamlit as st
import streamlit_authenticator as stauth
import yaml
import base64
from PIL import Image
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.add_vertical_space import add_vertical_space
from src.scripts import streamlit_settings, login
import pymongo
import pandas as pd
import numpy as np

def frontpage(name, authentication_status, username, authenticator):
    # ugyldig passord
    if authentication_status == False:
        st.error('Ugyldig brukernavn/passord')
        st.stop()
    # ingen input
    elif authentication_status == None:
        st.image(Image.open('src/data/img/illustrasjon.png'))
        st.stop()
    # app start
    elif authentication_status:
        #
        with st.sidebar:
            #st.image(Image.open('src/data/img/av_logo.png'))
            authenticator.logout('Logg ut')

def database_to_df(mycollection, substring):
    query = {"Name": {"$regex": f".*{substring}.*"}}
    cursor = mycollection.find(query)
    data = []
    for document in cursor:
        data.append(document)
    df = pd.DataFrame(data)
    columns_to_exclude = ['_id']
    df = df.drop(columns=columns_to_exclude)
    df = df.drop_duplicates()
    df = df.drop(columns="Name")
    df.replace('', np.nan, inplace=True)
    df.replace(' ', np.nan, inplace=True)
    df = df.dropna(how='all')
    df = df.dropna(axis = 1)
    return df

def get_names(df, substring):
    if substring == "TREND1":
        column_names = ["ID", "Date", "Time", "3202-RT401", "3202-RT501", "3203-RT401", "3203-RT501", "3201-RT402", "3201-RT502", "3501-RT403", "3501-RT501", "3501-RT404", "3501-RT502"]
    elif substring == "TREND2":
        column_names = ["ID", "Date", "Time", "3501-RT503", "3201-RT401", "3201-RT501", "3501-RT401", "3501-RT504", "3501-RT001", "3501-RT002", "3501-RP001", "3501-RP002", "BC-RN001"]
    elif substring == "TREND3":
        column_names = ["ID", "Date", "Time", "3201-OE501", "3202-OE501", "3203-OE501"]
    df.columns = column_names
    return df

def get_full_dataframe():
    #client = pymongo.MongoClient(**st.secrets["mongo"])
    client = pymongo.MongoClient("mongodb+srv://magnesyljuasen:jau0IMk5OKJWJ3Xl@cluster0.dlyj4y2.mongodb.net/")
    mydatabase = client["Kolbotn"]
    mycollection = mydatabase["Driftsdata"]
    
    #--
    substring = "TREND1"
    df = database_to_df(mycollection = mycollection, substring = substring)
    df1 = get_names(df = df, substring = substring)

    #--
    substring = "TREND2"
    df = database_to_df(mycollection = mycollection, substring = substring)
    df2 = get_names(df = df, substring = substring)

    #--
    substring = "TREND3"
    df = database_to_df(mycollection = mycollection, substring = substring)
    df3 = get_names(df = df, substring = substring)

    merged_df = pd.merge(df1, df2, on='ID')
    merged_df = pd.merge(merged_df, df3, on='ID')
    merged_df = merged_df.T.drop_duplicates().T
    merged_df['Tid'] = pd.to_datetime(merged_df['Date_x'] + ' ' + merged_df['Time_x'])
    merged_df = merged_df.drop(['Date_x', 'Time_x', 'ID'], axis=1)
    
    column_mapping = {
            '3501-RT503': 'Temperatur opp fra alle brønner (hovedrør)',
            '3501-RT403': 'Temperatur ned i 40 brønner',
            '3501-RT404': 'Temperatur ned i 20 brønner',
            '3501-RT501': 'Temperatur opp fra 40 brønner',
            '3501-RT502': 'Temperatur opp fra 20 brønner',
            '3501-RT401': 'Temperatur ut fra varmepumpe (kald side)',
            '3501-RT504': 'Temperatur inn til varmepumpe (kald side)',
            '3501-RT002': 'Finner ikke',
            '3501-RP001': 'Trykkmåler (banekrets) (pascal)',
            '3501-RP002': 'Trykkmåler (varmepumpe-krets) (pascal)',
            '3201-RT401': 'Turtemperatur VP (varm side)',
            '3202-RT501': 'Returtemperatur VP (varm side)',
            '3202-RT401': 'Ned i bane 1 (temp)',
            '3202-RT501': 'Opp fra bane 1 (temp)',
            '3203-RT401': 'Ned i bane 2 (temp)',
            '3203-RT501': 'Opp fra bane 2 (temp)',
            '3201-RT402': 'Varm (vet ikke helt)',
            '3201-RT502': 'Kaldere (vet ikke helt)'
        }
    
    merged_df.rename(columns=column_mapping, inplace=True)
    return merged_df

def show_dashboard():
    merged_df = get_full_dataframe()
    st.write(merged_df)
    st.bar_chart(data = merged_df, x = "Tid", y = "3201-OE501")

def main():
    streamlit_settings()
    name, authentication_status, username, authenticator = login()
    frontpage(name, authentication_status, username, authenticator)
    st.title("Driftsovervåkning")
    show_dashboard()


if __name__ == "__main__":
    main()


