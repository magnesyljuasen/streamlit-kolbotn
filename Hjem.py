import streamlit as st
import streamlit_authenticator as stauth
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.add_vertical_space import add_vertical_space
import pymongo
import pandas as pd
import numpy as np
import plotly.express as px
import yaml
import base64
from PIL import Image
import datetime

class Dashboard:
    def __init__(self):
        pass

    def streamlit_settings(self):
        st.set_page_config(
            page_title = "Kolbotn Dashboard", 
            layout = "wide", 
            page_icon = "src/data/img/AsplanViak_Favicon_32x32.png", 
            initial_sidebar_state = "expanded"
            )
        with open("src/styles/main.css") as f:
            st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
            st.markdown('''<style>button[title="View fullscreen"]{visibility: hidden;}</style>''', unsafe_allow_html=True) # hide fullscreen
            #st.markdown("""<style>[data-testid="collapsedControl"] {display: none}</style>""", unsafe_allow_html=True) # ingen sidebar
            #st.markdown("""<style>div[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True) # litt av sidebar
            #st.markdown("""<style>.block-container {padding-top: 1rem;padding-bottom: 0rem;padding-left: 5rem;padding-right: 5rem;}</style>""", unsafe_allow_html=True)

    def streamlit_login(self):
        with open('src/login/config.yaml') as file:
            config = yaml.load(file, Loader=stauth.SafeLoader)
            authenticator = stauth.Authenticate(config['credentials'],config['cookie']['name'],config['cookie']['key'],config['cookie']['expiry_days'])
            name, authentication_status, username = authenticator.login('Innlogging', 'main')
        return name, authentication_status, username, authenticator

    def streamlit_login_page(self, name, authentication_status, username, authenticator):
        if authentication_status == False: # ugyldig passord
            st.error('Ugyldig brukernavn/passord')
            st.stop()
        elif authentication_status == None: # ingen input
            st.image(Image.open('src/data/img/kolbotn_sesongvarmelager.jpg'))
            st.stop()
        elif authentication_status: # app start
            with st.sidebar:
                #st.image(Image.open('src/data/img/av_logo.png')) # logo
                st.write(f"*Velkommen {name}!*")
                authenticator.logout('Logg ut')
                st.markdown("---")

    def database_to_df(self, mycollection, substring):
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

    def get_names(self, df, substring):
        if substring == "TREND1":
            column_names = ["ID", "Date", "Time", "3202-RT401", "3202-RT501", "3203-RT401", "3203-RT501", "3201-RT402", "3201-RT502", "3501-RT403", "3501-RT501", "3501-RT404", "3501-RT502"]
        elif substring == "TREND2":
            column_names = ["ID", "Date", "Time", "3501-RT503", "3201-RT401", "3201-RT501", "3501-RT401", "3501-RT504", "3501-RT001", "3501-RT002", "3501-RP001", "3501-RP002", "BC-RN001"]
        elif substring == "TREND3":
            column_names = ["ID", "Date", "Time", "3201-OE501", "3202-OE501", "3203-OE501"]
        df.columns = column_names
        return df

    def convert_to_float(self, value):
        return float(str(value).replace(',', '.'))

    def get_full_dataframe(self):
        #client = pymongo.MongoClient(**st.secrets["mongo"])
        client = pymongo.MongoClient("mongodb+srv://magnesyljuasen:jau0IMk5OKJWJ3Xl@cluster0.dlyj4y2.mongodb.net/")
        mydatabase = client["Kolbotn"]
        mycollection = mydatabase["Driftsdata"]
        #--
        substring = "TREND1"
        df = self.database_to_df(mycollection = mycollection, substring = substring)
        df1 = self.get_names(df = df, substring = substring)
        #--
        substring = "TREND2"
        df = self.database_to_df(mycollection = mycollection, substring = substring)
        df2 = self.get_names(df = df, substring = substring)
        #--
        substring = "TREND3"
        df = self.database_to_df(mycollection = mycollection, substring = substring)
        df3 = self.get_names(df = df, substring = substring)

        merged_df = pd.merge(df1, df2, on='ID')
        merged_df = pd.merge(merged_df, df3, on='ID')
        merged_df = merged_df.T.drop_duplicates().T
        merged_df['Tid'] = merged_df['Date_x'] + ' ' + merged_df['Time_x']
        merged_df = merged_df.drop(['Date_x', 'Time_x', 'ID'], axis=1)
        time_df = merged_df["Tid"]
        merged_df = merged_df.drop(["Tid"], axis = 1)
        merged_df = merged_df.applymap(self.convert_to_float)
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
        merged_df = merged_df.reset_index(drop = True)
        merged_df['Tilført energi - Bane 1'] = merged_df['Tilført energi - Bane 1'] - 435675 # correction
        return merged_df

    def download_csv(self, dataframe):
        csv_file = dataframe.to_csv(index=False)
        b64 = base64.b64encode(csv_file.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">Trykk her for å laste ned data</a>'
        return href

    def energy_plot(self, df, series, series_name):
        #df['Change_Per_Unit'] = df[series_name].diff()
        #df.at[0, 'Change_Per_Unit'] = 0
        fig = px.line(df, x='Tid', y=series, labels={'Value': series, 'Timestamp': 'Tid'}, color_discrete_sequence=["rgba(29, 60, 52, 0.75)"])
        #fig.add_scatter(x=df['Tid'], y=df['Change_Per_Unit'], mode='lines', yaxis="y2", line=dict(color='rgba(0, 0, 255, 1)'))
        fig.update_xaxes(type='category')
        average_cummulative = np.average(df[series].to_numpy())
        #average_increase = np.average(df['Change_Per_Unit'].to_numpy())
        fig.update_xaxes(
            gridwidth=0.3,
        )
        fig.update_yaxes(
            tickformat=",",
            ticks="outside",
            gridwidth=0.3,
        )
        fig.update_layout(
            xaxis=dict(showticklabels=False),
            showlegend=False,
            yaxis=dict(range=[average_cummulative-average_cummulative/10, average_cummulative+average_cummulative/10]),
            margin=dict(l=0,r=0,b=0,t=0,pad=0),
            separators="* .*",
            yaxis_title=f"Energi {series_name.lower()} (kWh)",
            xaxis_title="",
            height = 200
            )
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

    def temperature_plot(self, df, series, series_name, min_value = 0, max_value = 10):
        fig = px.line(df, x='Tid', y=series, labels={'Value': series, 'Timestamp': 'Tid'}, color_discrete_sequence=[f"rgba(29, 60, 52, 0.75)"])
        fig.update_xaxes(type='category')
        fig.update_xaxes(
            gridwidth=0.3,
        )
        fig.update_yaxes(
            tickformat=",",
            ticks="outside",
            gridcolor="lightgrey",
            gridwidth=0.3,
        )

        fig.update_layout(
            xaxis=dict(showticklabels=False),
            showlegend=False,
            yaxis=dict(range=[min_value, max_value]),
            margin=dict(l=10,r=10,b=10,t=10,pad=0),
            #separators="* .*",
            yaxis_title=f"Temperatur {series_name.lower()} (ºC)",
            xaxis_title="",
            height = 200,
            )
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

    def temperature_plot_two_series(self, df, series_1, series_name_1, series_2, series_name_2, min_value = 0, max_value = 10):
        fig1 = px.line(df, x='Tid', y=series_1, labels={'Value': series_1, 'Timestamp': 'Tid'}, color_discrete_sequence=[f"rgba(29, 60, 52, 0.5)"])
        fig2 = px.line(df, x='Tid', y=series_2, labels={'Value': series_2, 'Timestamp': 'Tid'}, color_discrete_sequence=[f"rgba(29, 60, 52, 0.5)"])
        fig = fig1
        fig.add_traces(fig2.data)
        fig.update_xaxes(type='category')
        fig.update_xaxes(
            gridwidth=0.3,
        )
        fig.update_yaxes(
            tickformat=",",
            ticks="outside",
            gridcolor="lightgrey",
            gridwidth=0.3,
        )
        fig.update_layout(
            xaxis=dict(showticklabels=False),
            showlegend=False,
            yaxis=dict(range=[min_value, max_value]),
            margin=dict(l=10,r=10,b=10,t=10,pad=0),
            #separators="* .*",
            yaxis_title=f"Temperatur (ºC)",
            xaxis_title="",
            height = 200,
            )
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

    def embed_url_in_iframe(self, url):
        html = f'<div style="display: flex; justify-content: center;"><iframe src="{url}" width="800" height="600"></iframe></div>'
        st.components.v1.html(html, height = 600)

    def show_weather_statistics(self):
        url_pent = "https://pent.no/59.79672,10.81356"
        url_yr = "https://www.yr.no/nb/v%C3%A6rvarsel/daglig-tabell/1-74394/Norge/Viken/Nordre%20Follo/Sofiemyr"
        self.embed_url_in_iframe(url = url_pent)

    def show_webcam(self):
        url_webcam = "https://xn--vindn-qra.no/webkamera/viken/nordre-follo/sofiemyr-e6-taraldrud-(retning-taraldrud)-d0025d"
        self.embed_url_in_iframe(url = url_webcam)

    def date_picker(self, df):
        date_range = st.date_input("Velg tidsintervall", (df["Tid"][0].to_pydatetime(), df["Tid"][len(df["Tid"]) - 1].to_pydatetime()))
        if len(date_range) == 1:
            st.error("Du må velge et tidsintervall")
            st.stop()
        filtered_df = df[(df['Tid'] >= pd.Timestamp(date_range[0])) & (df['Tid'] <= pd.Timestamp(date_range[1]))]
        filtered_df = filtered_df.reset_index(drop = True)
        if len(filtered_df) == 0:
            st.error("Ingen data i tidsintervall")
            st.stop()
        return filtered_df
    
    def column_to_metric(self, df, metric_name, unit, rounding = -2):
        metric = f"{round(int(df[metric_name].to_numpy()[-1]), rounding):,} {unit}".replace(",", " ")
        return metric
    
    def column_to_delta(self, df, metric_name, unit, rounding = -2):
        delta = f"Siste døgn: {round(int(df[metric_name].to_numpy()[-1] - df[metric_name].to_numpy()[-23]), rounding):,} {unit}".replace(",", " ")
        return delta
    
    def default_kpi(self, df):
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(
            label = "Energi til bane 1 (totalt)",
            value = self.column_to_metric(df = df, metric_name = "Tilført energi - Bane 1", unit = "kWh"),
            delta = self.column_to_delta(df = df, metric_name = "Tilført energi - Bane 1", unit = "kWh")
        )
        kpi2.metric(
            label = "Energi til bane 2 (totalt)",
            value = self.column_to_metric(df = df, metric_name = "Tilført energi - Bane 2", unit = "kWh"),
            delta = self.column_to_delta(df = df, metric_name = "Tilført energi - Bane 2", unit = "kWh")
        )
        kpi3.metric(
            label="Energi fra varmepumpe (totalt)",
            value = self.column_to_metric(df = df, metric_name = "Energi levert fra varmepumpe", unit = "kWh"),
            delta = self.column_to_delta(df = df, metric_name = "Energi levert fra varmepumpe", unit = "kWh")
        )

    def default_charts(self, df):
        c1, c2 = st.columns(2)
        with c1:
            self.temperature_plot(df = df, series = 'Opp fra bane 1 (temp)', series_name = "Fra bane 1", min_value = 0, max_value = 5)
        with c2:
            self.temperature_plot(df = df, series = 'Opp fra bane 2 (temp)', series_name = "Fra bane 2", min_value = 0, max_value = 15)
        c1, c2 = st.columns(2)
        with c1:
            self.energy_plot(df = df, series = "Tilført energi - Bane 1", series_name = "Tilført bane 1")
        with c2:
            self.energy_plot(df = df, series = "Tilført energi - Bane 2", series_name = "Tilført bane 2")
        c1, c2 = st.columns(2)
        with c1:
            self.temperature_plot_two_series(df = df, series_1 = 'Temperatur ned i 40 brønner', series_name_1 = 'Til 40 brønner', series_2 = 'Temperatur ned i 20 brønner', series_name_2 = 'Til 20 brønner', min_value = 0, max_value = 10)
        with c2:
            self.temperature_plot_two_series(df = df, series_1 = 'Temperatur opp fra 40 brønner', series_name_1 = 'Fra 40 brønner', series_2 = 'Temperatur opp fra 20 brønner', series_name_2 = 'Fra 20 brønner', min_value = 0, max_value = 10)
            
    def show_weather_stats(self):
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("Vær", expanded = True):
                self.show_weather_statistics()
        with c2:
            with st.expander("Webkamera", expanded = True):
                self.show_webcam()

    def main(self):
        self.streamlit_settings()
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            name, authentication_status, username, authenticator = self.streamlit_login()
            self.streamlit_login_page(name, authentication_status, username, authenticator)
        st.title("Sesongvarmelager KIL Drift") # page title
        df = self.get_full_dataframe() # get dataframe
        with st.sidebar:
            df = self.date_picker(df = df) # top level filter 
            st.selectbox("Velg modus", options = [""])
            st.selectbox("Velg oppløsning", options = [""])
        with st.container():
            self.default_kpi(df = df) # kpis
        with st.container():
            self.default_charts(df = df)
        st.dataframe(data = df, height = 200, use_container_width = True, ) # data table
        st.markdown(self.download_csv(df), unsafe_allow_html=True) # download button
        self.show_weather_stats()

if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.main()