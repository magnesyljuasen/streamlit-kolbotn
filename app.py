import streamlit as st
import streamlit_authenticator as stauth
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.add_vertical_space import add_vertical_space
import pymongo
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import yaml
import base64
from PIL import Image
import datetime
import requests
import json

def streamlit_login():
    with open('src/login/config.yaml') as file:
        config = yaml.load(file, Loader=stauth.SafeLoader)
        authenticator = stauth.Authenticate(config['credentials'],config['cookie']['name'],config['cookie']['key'],config['cookie']['expiry_days'])
        name, authentication_status, username = authenticator.login(fields = {'Form name' : 'Logg inn', 'Username' : 'Brukernavn', 'Password' : 'Passord', 'Login' : 'Logg inn'})

    return name, authentication_status, username, authenticator

def streamlit_login_page(name, authentication_status, username, authenticator):
    if authentication_status == False: # ugyldig passord
        st.error('Ugyldig brukernavn/passord')
        st.stop()
    elif authentication_status == None: # ingen input
        st.image(Image.open('src/data/img/kolbotn_sesongvarmelager.jpg'), use_container_width=True)
        st.stop()
    elif authentication_status: # app start
        with st.sidebar:
            #st.image(Image.open('src/data/img/av_logo.png')) # logo
            st.write(f"*Velkommen {name}!*")
            authenticator.logout('Logg ut')
            st.markdown("---")

def convert_to_float(value):
    return float(str(value).replace(',', '.'))

@st.cache_resource(show_spinner='Laster inn data...')
def get_full_dataframe():
    def database_to_df(mycollection, substring):
        query = {"Name": {"$regex": f".*{substring}.*"}}
        cursor = mycollection.find(query)
        data = []
        for document in cursor:
            data.append(document)
        df = pd.DataFrame(data)
        df.to_csv(f'eksport_{substring}.csv')
        columns_to_exclude = ['_id']
        df = df.drop(columns=columns_to_exclude)
        df = df.drop_duplicates()
        df = df.drop(columns="Name")
        df.replace('', np.nan, inplace=True)
        df.replace(' ', np.nan, inplace=True)
        df = df.dropna(how='all')
        df = df.dropna(axis = 1, thresh=1)
        return df

    def get_names(df, substring):
        if substring == "TREND1":
            column_names = ["ID", "Date", "Time", "3202-RT401", "3202-RT501", "3203-RT401", "3203-RT501", "3201-RT402", "3201-RT502", "3501-RT403", "3501-RT501", "3501-RT404", "3501-RT502"]
        elif substring == "TREND2":
            column_names = ["ID", "Date", "Time", "3501-RT503", "3201-RT401", "3201-RT501", "3501-RT401", "3501-RT504", "3501-RT001", "3501-RT002", "3501-RP001", "3501-RP002", "BC-RN001"]
        elif substring == "TREND3":
            column_names = ["ID", "Date", "Time", "3201-OE501", "3202-OE501", "3203-OE501", "Utetemperatur", "SEKVENS"]
        df.columns = column_names
        return df

    #client = pymongo.MongoClient(**st.secrets["mongo"])
    client = pymongo.MongoClient("mongodb+srv://magnesyljuasen:jau0IMk5OKJWJ3Xl@cluster0.dlyj4y2.mongodb.net/")
    mydatabase = client["Kolbotn"]
    mycollection = mydatabase["Driftsdata"]
    documents = list(mycollection.find())
    with open('driftsdata.json', 'w') as file:
        json.dump(documents, file, default=str)
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
    merged_df['Tid'] = merged_df['Date_x'] + ' ' + merged_df['Time_x']
    merged_df = merged_df.drop(['Date_x', 'Time_x', 'ID'], axis=1)
    time_df = merged_df["Tid"]
    merged_df = merged_df.drop(["Tid"], axis = 1)
    merged_df = merged_df.applymap(convert_to_float)
    merged_df["Tid"] = time_df
    merged_df['Tid'] = pd.to_datetime(merged_df['Tid'], format='%d.%m.%y %H:%M:%S')
    merged_df = merged_df.sort_values('Tid')
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
            '3501-RT001': 'Temperaturføler i brønn (ytre)',
            '3501-RT002': 'Temperaturføler i brønn (midten)',
            '3501-RP001': 'Trykkmåler (banekrets) (pascal)',
            '3501-RP002': 'Trykkmåler (varmepumpe-krets) (pascal)',
            '3201-RT401': 'Turtemperatur VP (varm side)',
            '3202-RT501': 'Returtemperatur VP (varm side)',
            '3202-RT401': 'Til bane 1',
            '3202-RT501': 'Fra bane 1',
            '3203-RT401': 'Til bane 2',
            '3203-RT501': 'Fra bane 2',
            #'3201-RT402': 'Varm (vet ikke helt)',
            #'3201-RT502': 'Kaldere (vet ikke helt)',
            '3201-OE501' : 'Energi levert fra varmepumpe',
            '3202-OE501' : 'Tilført energi - Bane 1',
            '3203-OE501' : 'Tilført energi - Bane 2'
        }
    merged_df.rename(columns=column_mapping, inplace=True)
    merged_df = merged_df.reset_index(drop = True)
    merged_df['Tilført energi - Bane 1'] = merged_df['Tilført energi - Bane 1'] - 435675 # correction
    merged_df['Tid'] = pd.to_datetime(merged_df['Tid'])
    # df["CO2 - Bane 1"] = df["Tilført energi - Bane 1"] * (238/(1000*1000))
    return merged_df

@st.cache_resource(show_spinner='Laster inn strømforbruk...')
def get_electric_df():
    df_el = pd.read_excel("src/data/elforbruk/data.xlsx")
    df_el['dato'] = pd.to_datetime(df_el['dato'], format='%d.%m.%Y')
    df_el['Tidsverdier'] = df_el['dato'].dt.strftime('%d/%m-%y, %H:01')
    df_el['Tid'] = df_el['dato'].dt.strftime('%Y-%m-%d 01:01')
    df_el = df_el.drop("dato", axis = 1)
    df_el.rename(columns = {'kWh' : 'Strømforbruk'}, inplace = True)
    df_el['Tid'] = pd.to_datetime(df_el['Tid'])
    df_el['Strømforbruk'] = df_el['Strømforbruk'].astype(float)
    return df_el

@st.cache_resource(show_spinner='Henter temperaturdata fra værstasjon...')
def get_temperature_series():
    client_id = "248d45de-6fc1-4e3b-a4b0-e2932420605e"
    endpoint = f"https://frost.met.no/observations/v0.jsonld?"
    parameters = {
        'sources' : 'SN17820',
        'referencetime' : f"2023-11-01/{datetime.date.today()}",
        'elements' : 'mean(air_temperature P1D)',
        'timeoffsets': 'PT0H',
        'timeresolutions' : 'P1D'
        }
    r = requests.get(endpoint, parameters, auth=(client_id,""))
    json = r.json()["data"]
    temperature_array, time_array = [], []
    for i in range(0, len(json)):
        reference_time = pd.to_datetime(json[i]["referenceTime"])
        formatted_date = reference_time.strftime("%d/%m-%y, %H:01")
        temperature = float(json[i]["observations"][0]["value"])
        temperature_array.append(temperature)
        time_array.append(formatted_date)
    
    df_temperature = pd.DataFrame({
        "Tidsverdier" : time_array,
        "Utetemperatur (MET)" : temperature_array
        })
    return df_temperature

@st.cache_resource(show_spinner=False)
def calculate_more_columns(df, window_size=1):
    def electric_column_to_hours(df):
        for index, row in df.iterrows():
            daily_sum = row['Strømforbruk']
            if daily_sum > 0:
                hourly_sum = daily_sum/23
            #if row['Til bane 1'] > -50:
            if row['Tilført energi - Bane 1'] > 0:
                df.at[index, 'Strømforbruk'] = hourly_sum
            else:
                df.at[index, 'Strømforbruk'] = None
        return df

    def remove_outliers(df, series):
        Q1 = df[series].quantile(0.1)
        Q3 = df[series].quantile(0.9)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df.loc[(df[series] < lower_bound) | (df[series] > upper_bound), series] = np.nan
        return df

    def find_missing_time_data(df):
        df['Tid'] = pd.to_datetime(df['Tid'])
        date_range = pd.date_range(start=df['Tid'].min(), end=df['Tid'].max(), freq='h')
        df_date_range = pd.DataFrame(date_range, columns=['Tid'])
        merged_df = pd.merge(df_date_range, df, on='Tid', how='left')
        merged_df.sort_values(by='Tid', inplace=True)
        merged_df.reset_index(drop=True, inplace=True)
        return merged_df

    df = electric_column_to_hours(df=df)

    df['Tilført effekt - Bane 1'] = df["Tilført energi - Bane 1"].diff().rolling(window=window_size).mean()
    df['Tilført effekt - Bane 2'] = df["Tilført energi - Bane 2"].diff().rolling(window=window_size).mean()
    df['Tilført effekt - Varmepumpe'] = df["Energi levert fra varmepumpe"].diff().rolling(window=window_size).mean()

    df['Strømforbruk_akkumulert'] = df['Strømforbruk'].cumsum()

    df = remove_outliers(df, "Tilført effekt - Bane 1")
    df = remove_outliers(df, "Tilført energi - Bane 1")
    df = remove_outliers(df, "Tilført effekt - Varmepumpe")

    df = find_missing_time_data(df)
    df["Tidsverdier"] = df['Tid'].dt.strftime("%d/%m-%y, %H:01").tolist()
    return df

def date_picker(df):
    def get_date_string(date):
        datestring = str(date).split("-")
        day = int(datestring[2].split(" ")[0])
        year = datestring[0]
        month = int(datestring[1])
        month_map = {
            1 : 'jan',
            2 : 'feb',
            3 : 'mar',
            4 : 'apr',
            5 : 'mai',
            6 : 'jun',
            7 : 'jul',
            8 : 'aug',
            9 : 'sep',
            10 : 'okt',
            11 : 'nov',
            12 : 'des'
        }
        month = month_map[month]
        datestring = f"{day}. {month}, {year}"
        return datestring

    # Predefined seasons
    predefined_seasons = {
        "Fyringssesong 2024/2025": ("2024-09-15", "2025-05-12"),
        "Fyringssesong 2023/2024": ("2023-08-01", "2024-04-02"),
        "Ladesesong 2025" : ("2025-05-12", "2025-09-15"),
        "Ladesesong 2024" : ("2024-04-02", "2024-09-15"), #Veksling
        "Egendefinert periode": None
    }

    selection = st.radio(
        "Velg sesong eller egendefinert periode:",
        list(predefined_seasons.keys())
    )

    helpstring = """Velg tidsintervall her for å filtere dataene. Alle tall og grafer vil oppdatere seg. Her er det mulig å se verdier for en måned ved å filtrere for f.eks. 1. desember til 31. desember."""
    
    if selection == "Egendefinert periode":
        date_range = st.date_input(
            "Velg tidsintervall",
            (df["Tid"].iloc[0].to_pydatetime(), df["Tid"].iloc[-1].to_pydatetime()),
            help=helpstring
        )
        if len(date_range) == 1:
            st.error("Du må velge et tidsintervall")
            st.stop()
        start, end = date_range
    else:
        start_str, end_str = predefined_seasons[selection]
        start = pd.to_datetime(start_str)
        end = pd.to_datetime(end_str)
        st.info(f"Filtrerer for {selection}: {start.date()} til {end.date()}")

    filtered_df = df[(df['Tid'] >= pd.Timestamp(start)) & (df['Tid'] <= pd.Timestamp(end))]
    filtered_df = filtered_df.reset_index(drop=True)
    if len(filtered_df) == 0:
        st.error("Ingen data i tidsintervall")
        st.stop()

    start_date = get_date_string(filtered_df['Tid'].iloc[0])
    end_date = get_date_string(filtered_df['Tid'].iloc[-1])
    
    return filtered_df, start_date, end_date

def energy_effect_plot(df, series, series_label, average = False, separator = False, min_value = None, max_value = None, chart_type = "Line"):
        if chart_type == "Line":
            fig = px.line(df, x=df['Tidsverdier'], y=series, labels={'Value': series, 'Timestamp': 'Tid'}, color_discrete_sequence=["rgba(27, 39, 52, 0.75)"])
        elif chart_type == "Bar":
            fig = px.bar(df, x=df['Tidsverdier'], y=series, labels={'Value': series, 'Timestamp': 'Tid'}, color_discrete_sequence=["rgba(29, 60, 52, 0.75)"])
        fig.update_xaxes(
            title='',
            type='category',
            gridwidth=0.3,
            tickmode='auto',
            nticks=4,  
            tickangle=30)
        fig.update_yaxes(
            title=f"Temperatur (ºC)",
            tickformat=",",
            ticks="outside",
            gridcolor="lightgrey",
            gridwidth=0.3,
        )
        if average == True:
            average = df[series].mean()
            delta_average = average * 0.98
            fig.update_layout(yaxis=dict(range=[average - delta_average, average + delta_average]))
        if separator == True:
            fig.update_layout(separators="* .*")
            
        fig.update_layout(
                #xaxis=dict(showticklabels=False),
                showlegend=False,
                margin=dict(l=20,r=20,b=20,t=20,pad=0),
                yaxis_title=series_label,
                yaxis=dict(range=[min_value, max_value]),
                xaxis_title="",
                height = 300
                )
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

def temperature_plot(df, series, min_value = 0, max_value = 10):
    fig = px.line(df, x=df['Tidsverdier'], y=series, labels={'Value': series, 'Timestamp': 'Tid'}, color_discrete_sequence=[f"rgba(29, 60, 52, 0.75)"])
    fig.update_xaxes(type='category')
    fig.update_xaxes(
        title='',
        type='category',
        gridwidth=0.3,
        tickmode='auto',
        nticks=4,  
        tickangle=30)
    fig.update_yaxes(
        title=f"Temperatur (ºC)",
        tickformat=",",
        ticks="outside",
        gridcolor="lightgrey",
        gridwidth=0.3,
    )
    fig.update_layout(
        #xaxis=dict(showticklabels=False),
        showlegend=False,
        yaxis=dict(range=[min_value, max_value]),
        margin=dict(l=20,r=20,b=20,t=20,pad=0),
        #separators="* .*",
        #yaxis_title=f"Temperatur {series_name.lower()} (ºC)",
        xaxis_title="",
        height = 300,
        )
    st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

def temperature_plot_two_series(df, series_1, series_2, min_value = 0, max_value = 10):
    fig1 = px.line(df, x=df['Tidsverdier'], y=series_1, labels={'Value': series_1, 'Timestamp': 'Tid'}, color_discrete_sequence=[f"rgba(72, 162, 63, 0.5)"])
    fig2 = px.line(df, x=df['Tidsverdier'], y=series_2, labels={'Value': series_2, 'Timestamp': 'Tid'}, color_discrete_sequence=[f"rgba(29, 60, 52, 0.5)"])
    fig = fig1
    fig.add_traces(fig2.data)
    fig.update_xaxes(
        title='',
        type='category',
        gridwidth=0.3,
        tickmode='auto',
        nticks=4,  
        tickangle=30)
    fig.update_yaxes(
        title=f"Temperatur (ºC)",
        tickformat=",",
        ticks="outside",
        gridcolor="lightgrey",
        gridwidth=0.3,
    )
    fig.update_layout(
        #xaxis=dict(showticklabels=False),
        showlegend=False,
        yaxis=dict(range=[min_value, max_value]),
        margin=dict(l=20,r=20,b=20,t=20,pad=0),
        #separators="* .*",
        height = 300,
        )
    st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

### App start ###

st.set_page_config(
    page_title = "Kolbotn Dashboard", 
    layout = "wide", 
    page_icon = "src/data/img/AsplanViak_Favicon_32x32.png", 
    initial_sidebar_state = "expanded"
    )

with open("src/styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    
name, authentication_status, username, authenticator = streamlit_login()
streamlit_login_page(name, authentication_status, username, authenticator)

st.title("Sesongvarmelager KIL Drift") # page title
df = get_full_dataframe() # get dataframe
df_el = get_electric_df()
df_temperature = get_temperature_series()
df_el = pd.merge(df_el, df_temperature, on='Tidsverdier', how='outer')
df = pd.merge(df, df_el, on='Tid', how='outer')
df = calculate_more_columns(df=df, window_size=1)

with st.sidebar:
    df, start_date, end_date = date_picker(df)

    sequence_dict = {
        "1.0": ":blue[Vinter: Vi henter varme direkte fra varmelager og leverer til baner]",
        "2.0": ":blue[Vinter: Varmepumpe leverer varme til baner]",
        "3.1": ":red[Sommer: Vi henter varme direkte fra baner og lader opp varmelager]",
        "3.2": ":red[Sommer: Vi henter varme direkte fra baner og lader opp varmelager]",
        "4.0": ":red[Sommer: Vi henter varme fra baner via varmepumpe og lader opp varmelager]"
    }

    description_to_keys = {}
    for key, desc in sequence_dict.items():
        description_to_keys.setdefault(desc, []).append(key)

    # Create radio options
    options = ['Alle'] + list(description_to_keys.keys())
    selected_description = st.radio('Velg sekvens', options=options)

    # Filtering logic
    if selected_description == 'Alle':
        df = df
    else:
        matching_keys = description_to_keys[selected_description]
        df = df[df['SEKVENS'].astype(str).isin(matching_keys)]

    

st.info(f'Viser nå data mellom {start_date} og {end_date}', icon=':material/info:')

with st.container(border=True):
    st.header('Utetemperatur og levert energi fra varmepumpe')
    c1, c2 = st.columns(2)
    with c1:
        st.caption("**Utetemperatur**")
        energy_effect_plot(df = df, series = "Utetemperatur", series_label = "Utetemperatur (°C)", separator = True, chart_type = "Line", min_value=None, max_value = None)
    with c2:
        st.caption(f"**Energi levert fra varmepumpe: {int(df['Energi levert fra varmepumpe'].max() - df['Energi levert fra varmepumpe'].min()):,} kWh**".replace(',', ' '))
        energy_effect_plot(df = df, series = "Energi levert fra varmepumpe", series_label = "Energi (kWh)", separator = True, chart_type = "Line", min_value=0, max_value = df["Energi levert fra varmepumpe"].max()*1.1)
    
with st.container(border=True):
    st.header('Bane 1 og bane 2')
    c1, c2 = st.columns(2)
    with c1:
        st.caption("**Temperatur til og fra bane 1**")
        temperature_plot_two_series(df = df, series_1 = 'Fra bane 1', series_2 = 'Til bane 1', min_value = None, max_value = None)
    with c2:
        st.caption("**Temperatur til og fra bane 2**")
        temperature_plot_two_series(df = df, series_1 = 'Fra bane 2', series_2 = 'Til bane 2', min_value = None, max_value = None)
    with c1:
        st.caption(f"**Energi tilført bane 1 (akkumulert): {int(df['Tilført energi - Bane 1'].max() - df['Tilført energi - Bane 1'].min()):,} kWh**".replace(',', ' '))
        y_max = df["Tilført energi - Bane 1"].max() * 1.1
        energy_effect_plot(df = df, series = "Tilført energi - Bane 1", series_label = "Energi (kWh)", separator = True, chart_type = "Line", min_value=0, max_value = y_max)
    with c2:
        st.caption(f"**Energi tilført bane 2 (akkumulert): {int(df['Tilført energi - Bane 2'].max() - df['Tilført energi - Bane 2'].min()):,} kWh**".replace(',', ' '))
        energy_effect_plot(df = df, series = "Tilført energi - Bane 2", series_label = "Energi (kWh)", separator = True, chart_type = "Line", min_value=0, max_value = y_max)
    with c1:
        y_max = df["Tilført effekt - Bane 1"].max() * 1.1
        st.caption("**Effekt tilført bane 1 (beregnet)**")
        energy_effect_plot(df = df, series = "Tilført effekt - Bane 1", series_label = "Effekt (kW)", separator = True, chart_type = "Bar", min_value=0, max_value = y_max)
    with c2:
        st.caption("**Effekt tilført bane 2 (beregnet)**")
        energy_effect_plot(df = df, series = "Tilført effekt - Bane 2", series_label = "Effekt (kW)", separator = True, chart_type = "Bar", min_value=0, max_value = y_max)

with st.container(border=True):
    st.header('Temperaturfølere')
    c1, c2 = st.columns(2)
    with c1:
        st.caption("**Temperaturføler i brønn (ytre og midten)**")
        ymax = df['Temperaturføler i brønn (midten)'].max() * 1.1
        temperature_plot_two_series(df = df, series_1 = 'Temperaturføler i brønn (ytre)', series_2 = 'Temperaturføler i brønn (midten)', min_value = None, max_value = ymax)
    with c2:
        st.caption("**Temperatur opp fra 20 og 40 brønner**")
        temperature_plot_two_series(df = df, series_1 = 'Temperatur opp fra 40 brønner', series_2 = 'Temperatur opp fra 20 brønner', min_value = None, max_value = ymax)
    # with c2:
    #     st.caption("**Temperatur ned i 20 og 40 brønner**")
    #     temperature_plot_two_series(df = df, series_1 = 'Temperatur ned i 40 brønner', series_2 = 'Temperatur ned i 20 brønner', min_value = None, max_value = None)
    
    # with c2:
    #     st.caption("**Turtemperatur varmepumpe (varm side)**")
    #     temperature_plot(df = df, series = 'Turtemperatur VP (varm side)', min_value = None, max_value = None)

with st.container(border=True):
    st.header('Strømforbruk')
    # st.caption("**Sekvens**")
    # energy_effect_plot(df = df, series = "SEKVENS", series_label = "Sekvens", separator = False, chart_type = "Line", min_value=None, max_value = None)
    st.caption("**Strømforbruk per dag**")
    energy_effect_plot(df = df_el, series = "Strømforbruk", series_label = "Effekt (kW)", separator = True, chart_type = "Bar", min_value=0, max_value = 2000)

with st.container(border=True):
    st.header('Nedlasting')
    st.dataframe(df, use_container_width=True, height=400)