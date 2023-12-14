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

def convert_to_float(value):
    return float(str(value).replace(',', '.'))

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
    merged_df['Tid'] = pd.to_datetime((merged_df['Date_x'] + ' ' + merged_df['Time_x']))
    merged_df = merged_df.drop(['Date_x', 'Time_x', 'ID'], axis=1)
    time_df = merged_df["Tid"]
    merged_df = merged_df.drop(["Tid"], axis = 1)
    merged_df = merged_df.applymap(convert_to_float)
    merged_df["Tid"] = time_df
    #merged_df['Tid'] = merged_df['Tid'].apply(lambda x: x.replace(day=x.month, month=x.day))
    merged_df["3201-OE501"] = merged_df["3201-OE501"] * 10
    merged_df["3202-OE501"] = merged_df["3202-OE501"] * 10
    merged_df["3203-OE501"] = merged_df["3203-OE501"] * 10

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
            '3201-RT502': 'Kaldere (vet ikke helt)',
            '3201-OE501' : 'Energi levert fra varmepumpe',
            '3202-OE501' : 'Tilført energi - Bane 1',
            '3203-OE501' : 'Tilført energi - Bane 2'
        }
    
    merged_df.rename(columns=column_mapping, inplace=True)
    return merged_df

def show_dashboard():
    st.subheader("Energi")
    #--
    merged_df = get_full_dataframe()
    with st.expander("Data", expanded = False):
        st.write(merged_df)
    st.selectbox("Velg modus", options = [""])
    st.selectbox("Velg oppløsning", options = [""])
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Tilført energi - Bane 1", value = f"{int(merged_df['Tilført energi - Bane 1'].to_numpy()[-1]):,} kWh".replace(",", " "))
    with c2:
        st.metric("Tilført energi - Bane 2", value = f"{int(merged_df['Tilført energi - Bane 2'].to_numpy()[-1]):,} kWh".replace(",", " "))
    #--
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.metric("Siste 24 timer", value = f"{int(merged_df['Tilført energi - Bane 1'].to_numpy()[-1] - merged_df['Tilført energi - Bane 1'].to_numpy()[-24]):,} kWh".replace(",", " "))
        st.bar_chart(merged_df['Tilført energi - Bane 1'].to_numpy())
    #st.bar_chart(data = merged_df, x = "Tid", y = "Tilført energi - Bane 1")
        #st.bar_chart(data = merged_df, x = )
    with c2:
        st.metric("Siste 24 timer", value = f"{int(merged_df['Tilført energi - Bane 2'].to_numpy()[-1] - merged_df['Tilført energi - Bane 2'].to_numpy()[-24]):,} kWh".replace(",", " "))
        st.bar_chart(merged_df['Tilført energi - Bane 2'].to_numpy())
    #--
    st.subheader("Temperaturer")
    st.write("Kommer ...")
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(merged_df['Opp fra bane 1 (temp)'])
    with c2:
        st.line_chart(merged_df['Ned i bane 1 (temp)'])
        

def embed_url_in_iframe(url):
    html = f'<iframe src="{url}" width="800" height="600" frameborder="0"></iframe>'
    st.components.v1.html(html, width=800, height=600)

def show_weather_statistics():
    url1 = "https://xn--vindn-qra.no/webkamera/viken/nordre-follo/sofiemyr-e6-taraldrud-(retning-taraldrud)-d0025d"
    url2 = "https://pent.no/59.79672,10.81356"
    url3 = "https://www.yr.no/nb/v%C3%A6rvarsel/daglig-tabell/1-74394/Norge/Viken/Nordre%20Follo/Sofiemyr"
    c1, c2 = st.columns(2)
    with c1:
        embed_url_in_iframe(url = url1)
    with c2:
        embed_url_in_iframe(url = url2)
    #embed_url_in_iframe(url = url3)



def main():
    streamlit_settings()
    name, authentication_status, username, authenticator = login()
    frontpage(name, authentication_status, username, authenticator)
    st.info("Sette opp mail direkte til grunnvarme@asplanviak.no")
    st.title("Driftsovervåkning")
    show_dashboard()
    show_weather_statistics()

    


if __name__ == "__main__":
    main()


