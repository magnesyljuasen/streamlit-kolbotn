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
import plotly.express as px


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
    merged_df = merged_df.sort_values('Tid')
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

def download_csv(dataframe):
    csv_file = dataframe.to_csv(index=False)
    b64 = base64.b64encode(csv_file.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">Trykk her for å laste ned data</a>'
    return href

def show_energy_plot(merged_df, bane):
    merged_df['Change_Per_Unit'] = merged_df[bane].diff()
    merged_df.at[0, 'Change_Per_Unit'] = 0
    st.metric("Siste 24 timer", value = f"{int(merged_df[bane].to_numpy()[-1] - merged_df[bane].to_numpy()[-24]):,} kWh".replace(",", " "))
    fig = px.line(merged_df, x='Tid', y=bane, labels={'Value': bane, 'Timestamp': 'Tid'}, color_discrete_sequence=["black"])
    fig.add_scatter(x=merged_df['Tid'], y=merged_df['Change_Per_Unit'], mode='lines', yaxis="y2", line=dict(color='rgba(0, 0, 255, 0.2)'))
    fig.update_xaxes(type='category')
    average_cummulative = np.average(merged_df[bane].to_numpy())
    average_increase = np.average(merged_df['Change_Per_Unit'].to_numpy())
    fig.update_xaxes(
        ticks="outside",
        #linecolor="black",
        #gridcolor="lightgrey",
        gridwidth=0.3,
    )
    fig.update_yaxes(
        tickformat=",",
        ticks="outside",
        #linecolor="black",
        #gridcolor="lightgrey",
        gridwidth=0.3,
    )
    fig.update_layout(
        showlegend=False,
        yaxis=dict(range=[average_cummulative-average_cummulative/10, average_cummulative+average_cummulative/10]),
        margin=dict(l=0,r=0,b=0,t=0,pad=0),
        separators="* .*",
        yaxis_title="Energi [kWh]",
        xaxis_title="",
        yaxis2=dict(
            title='Effekt [kW]',
            overlaying='y',
            side='right',
            range=[0, average_increase+average_increase/0.5]
        ),
        )
    st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

def show_temperature_plot(merged_df, series, min_value, max_value):
    fig = px.line(merged_df, x='Tid', y=series, labels={'Value': series, 'Timestamp': 'Tid'}, color_discrete_sequence=["black"])
    fig.update_xaxes(type='category')
    fig.update_xaxes(
        ticks="outside",
        #linecolor="black",
        #gridcolor="lightgrey",
        gridwidth=0.3,
    )
    fig.update_yaxes(
        tickformat=",",
        ticks="outside",
        #linecolor="black",
        #gridcolor="lightgrey",
        gridwidth=0.3,
    )
    fig.update_layout(
        showlegend=False,
        yaxis=dict(range=[min_value, max_value]),
        margin=dict(l=0,r=0,b=0,t=0,pad=0),
        #separators="* .*",
        yaxis_title="Temperatur [grader]",
        xaxis_title="",
        )
    st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

def show_dashboard():
    #--
    with st.sidebar:
        st.selectbox("Velg modus", options = [""])
        st.selectbox("Velg oppløsning", options = [""])
    #--
    merged_df = get_full_dataframe()
    with st.expander("Se data", expanded = False):
        st.write(merged_df)
        st.markdown(download_csv(merged_df), unsafe_allow_html=True)
    with st.expander("Vær", expanded = False):
        show_weather_statistics()
    with st.expander("Webkamera", expanded = False):
        show_webcam()
    
    with st.expander("Energi", expanded = True):
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Tilført energi - Bane 1", value = f"{int(merged_df['Tilført energi - Bane 1'].to_numpy()[-1]):,} kWh".replace(",", " "))
        with c2:
            st.metric("Tilført energi - Bane 2", value = f"{int(merged_df['Tilført energi - Bane 2'].to_numpy()[-1]):,} kWh".replace(",", " "))
        #--
        c1, c2 = st.columns(2)
        with c1:
            show_energy_plot(merged_df, bane = "Tilført energi - Bane 1")
        with c2:
            show_energy_plot(merged_df, bane = "Tilført energi - Bane 2")
        #--
    with st.expander("Temperatur til baner", expanded = False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("Til bane 1")
            show_temperature_plot(merged_df = merged_df, series = 'Ned i bane 1 (temp)', min_value = 0, max_value = 8)
        with c2:
            st.markdown("Fra bane 1")
            show_temperature_plot(merged_df = merged_df, series = 'Opp fra bane 1 (temp)', min_value = 0, max_value = 8)
    #--
    with st.expander("Temperatur til brønner", expanded = False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("Til 40 brønner")
            show_temperature_plot(merged_df = merged_df, series = 'Temperatur ned i 40 brønner', min_value = 0, max_value = 12)
            st.markdown("Til 20 brønner")
            show_temperature_plot(merged_df = merged_df, series = 'Temperatur ned i 20 brønner', min_value = 0, max_value = 12)
        with c2:
            st.markdown("Fra 40 brønner")
            show_temperature_plot(merged_df = merged_df, series = 'Temperatur opp fra 40 brønner', min_value = 0, max_value = 12)
            st.markdown("Fra 20 brønner")
            show_temperature_plot(merged_df = merged_df, series = 'Temperatur opp fra 20 brønner', min_value = 0, max_value = 12)
            
        

def embed_url_in_iframe(url):
    html = f'<div style="display: flex; justify-content: center;"><iframe src="{url}" width="800" height="600"></iframe></div>'
    st.components.v1.html(html, height = 600)

def show_weather_statistics():
    url_pent = "https://pent.no/59.79672,10.81356"
    url_yr = "https://www.yr.no/nb/v%C3%A6rvarsel/daglig-tabell/1-74394/Norge/Viken/Nordre%20Follo/Sofiemyr"
    embed_url_in_iframe(url = url_pent)

def show_webcam():
    url_webcam = "https://xn--vindn-qra.no/webkamera/viken/nordre-follo/sofiemyr-e6-taraldrud-(retning-taraldrud)-d0025d"
    embed_url_in_iframe(url = url_webcam)
    
    #with c2:
    
    #embed_url_in_iframe(url = url3)



def main():
    streamlit_settings()
    name, authentication_status, username, authenticator = login()
    frontpage(name, authentication_status, username, authenticator)
    show_dashboard()

    


if __name__ == "__main__":
    main()


