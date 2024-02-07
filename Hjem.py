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
        df = df.dropna(axis = 1, thresh=1)
        return df

    def get_names(self, df, substring):
        if substring == "TREND1":
            column_names = ["ID", "Date", "Time", "3202-RT401", "3202-RT501", "3203-RT401", "3203-RT501", "3201-RT402", "3201-RT502", "3501-RT403", "3501-RT501", "3501-RT404", "3501-RT502"]
        elif substring == "TREND2":
            column_names = ["ID", "Date", "Time", "3501-RT503", "3201-RT401", "3201-RT501", "3501-RT401", "3501-RT504", "3501-RT001", "3501-RT002", "3501-RP001", "3501-RP002", "BC-RN001"]
        elif substring == "TREND3":
            column_names = ["ID", "Date", "Time", "3201-OE501", "3202-OE501", "3203-OE501", "Utetemperatur"]
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
        return merged_df

    def download_csv(self, dataframe):
        csv_file = dataframe.to_csv(index=False)
        b64 = base64.b64encode(csv_file.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">Trykk her for å laste ned data</a>'
        return href

    def energy_effect_plot(self, df, series, series_label, average = False, separator = False, min_value = None, max_value = None, chart_type = "Line"):
        if chart_type == "Line":
            fig = px.line(df, x=df['Tidsverdier'], y=series, labels={'Value': series, 'Timestamp': 'Tid'}, color_discrete_sequence=["rgba(29, 60, 52, 0.75)"])
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

    def temperature_plot(self, df, series, min_value = 0, max_value = 10):
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

    def temperature_plot_two_series(self, df, series_1, series_2, min_value = 0, max_value = 10):
        fig1 = px.line(df, x=df['Tidsverdier'], y=series_1, labels={'Value': series_1, 'Timestamp': 'Tid'}, color_discrete_sequence=[f"rgba(29, 60, 52, 0.5)"])
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
        st.info(
            """ Velg tidsintervall her 
            for å filtere dataene. Alle tall og grafer vil oppdatere seg. Her er det mulig å se verdier for en måned ved å filtrere for f.eks. 1. desember til 31. desember.
            """, icon="ℹ️")
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
    
    def column_to_metric(self, df, metric_name, unit, rounding = -1):
        metric = f"{round(int(df[metric_name].to_numpy()[-1]), rounding):,} {unit}".replace(",", " ")
        return metric
    
    def column_to_delta(self, df, metric_name, unit, last_value, last_value_text, rounding = -2):
        delta = f"Forrige {last_value_text}: {round(int(df[metric_name].to_numpy()[-1] - df[metric_name].to_numpy()[last_value]), rounding):,} {unit}".replace(",", " ")
        return delta
    
    def get_temperature_series(self):
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
        
        self.df_temperature = pd.DataFrame({
            "Tidsverdier" : time_array,
            "Temperatur" : temperature_array
            })
    
    def default_kpi(self, df):
        days = len(df)/23
        value_1 = round(int(df['Tilført effekt - Bane 1'].sum()), -2)
        value_3 = round(int(df['Strømforbruk'].sum()), -2)
        value_2 = round(int(self.total_energyuse), -2)
        value_4 = round(int(self.total_poweruse), -2)
        unit = "kWh"

        tab1, tab2 = st.tabs(["I valgt tidsintervall", "Totalt"])
        with tab1:
            #####
            kpi1, kpi2 = st.columns(2)
            kpi1.metric(
                label = "Energi til bane 1 **i valgt tidsintervall**",
                value = f"{value_1:,} {unit}".replace(",", " "),
                #delta = f"{round(value_1/days):,} {unit} per dag".replace(",", " "),
                help="Dette er energi tilført bane 1 i tidsintervallet."
                )
            #####
            kpi1.metric(
                label = "Strømforbruk **i valgt tidsintervall**",
                value = f"{value_3:,} {unit}".replace(",", " "),
                #delta = f"{round(value_3/days):,} {unit} per dag".replace(",", " "),
                help="Dette er strømforbruk i tidsintervallet."
                )
            #####
            value_diff_1 = value_1 - value_3
            kpi2.metric(
                label = "Besparelse **i valgt tidsintervall**",
                value = f"{value_diff_1:,} {unit}".replace(",", " "),
                #delta = f"{round(value_diff_1/days):,} {unit} per dag".replace(",", " "),
                help="Dette er besparelsen i tidsintervallet."
                )
            #####   
            value_5 = round(value_1/value_3, 1)
            kpi2.metric(
                label = "Gjennomsnittlig COP **i valgt tidsintervall**",
                value = f"{value_5:,}".replace(".", ","),
                help="""Koeffisienten for ytelse (COP) er et viktig begrep innenfor 
                termodynamikk og energieffektivitet, spesielt for varmepumper og 
                kjølesystemer. COP måler hvor effektivt et system kan produsere 
                ønsket termisk effekt (som oppvarming eller nedkjøling) i forhold til 
                energien som brukes til å drive systemet."""
                )
            #####
        with tab2:
            #####
            kpi1, kpi2 = st.columns(2)
            kpi1.metric(
                label = "Energi til bane 1 (**totalt**)",
                value = f"{value_2:,} kWh".replace(",", " "),
                #delta = f"{round(value_2/self.total_days):,} kWh per dag".replace(",", " "),
                help="Totalt tilført energi bane 1."
            )
            #####
            kpi1.metric(
                label = "Strømforbruk (**totalt**)",
                value = f"{value_4:,} kWh".replace(",", " "),
                #delta = f"{round(value_4/self.total_days):,} kWh per dag".replace(",", " "),
                help="Totalt strømforbruk."
            )
            #####
            value_diff_2 = value_2 - value_4
            kpi2.metric(
                label = "Besparelse (**totalt**)",
                value = f"{value_diff_2:,} kWh".replace(",", " "),
                #delta = f"{round(value_diff_2/self.total_days):,} kWh per dag".replace(",", " "),
                help="Total besparelse."
            )
            #####
            value_6 = round(value_2/value_4, 1)
            kpi2.metric(
                label = "Gjennomsnittlig COP (**totalt**)",
                value = f"{value_6:,}".replace(".", ","),
                help= 
                """ Koeffisienten for ytelse (COP) er et viktig begrep innenfor 
                termodynamikk og energieffektivitet, spesielt for varmepumper og 
                kjølesystemer. COP måler hvor effektivt et system kan produsere 
                ønsket termisk effekt (som oppvarming eller nedkjøling) i forhold til 
                energien som brukes til å drive systemet. """
            )

#        kpi2.metric(
#            label = "Energi tilført bane 2 ",
#            value = self.column_to_metric(df = df, metric_name = "Tilført energi - Bane 2", unit = "kWh"),
#            delta = self.column_to_delta(df = df, metric_name = "Tilført energi - Bane 2", unit = "kWh", last_value = last_value, last_value_text = last_value_text)
#        )
#        kpi3.metric(
#            label="Energi levert fra varmepumpe ",
#            value = self.column_to_metric(df = df, metric_name = "Energi levert fra varmepumpe", unit = "kWh"),
#            delta = self.column_to_delta(df = df, metric_name = "Energi levert fra varmepumpe", unit = "kWh", last_value = last_value, last_value_text = last_value_text)
#        )

    ## Åsmund fyll inn her
    def new_charts(self, df):
        def subplot(df, y_label, y_label_temperature = "Temperatur (ºC)"):
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.2, 0.1, 0.1])

            fig.add_trace(go.Bar(x=df['Tidsverdier'], y=df['Tilført effekt - Bane 1'], name='Tilført energi - Bane 1'), row=1, col=1)
            fig.add_trace(go.Bar(x=df['Tidsverdier'], y=df['Strømforbruk'], name='Strømforbruk'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Tidsverdier'], y=df['COP'], mode='markers', name='COP'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df['Tidsverdier'], y=df['Utetemperatur'], mode='lines+markers', name='Utetemperatur'), row=3, col=1)

            fig.update_traces(marker_color=f"rgba(29, 60, 52, 0.75)", row=1, col=1, selector=dict(name='Tilført energi - Bane 1'))
            fig.update_traces(marker_color=f"rgba(72, 162, 63, 0.75)", row=1, col=1, selector=dict(name='Strømforbruk'))
            fig.update_traces(marker=dict(color=f"rgba(51, 111, 58, 0.75)", size=5), row=2, col=1, selector=dict(name='COP'))
            fig.update_traces(line_color=f"rgba(255, 195, 88, 0.75)",row=3, col=1, selector=dict(name='Utetemperatur'))

            fig.update_xaxes(type='category')
            fig.update_xaxes(title='', type='category', gridwidth=0.3, tickmode='auto', nticks=4, tickangle=30)

            fig.update_yaxes(title_text=y_label, tickformat=" ", row=1, col=1)
            fig.update_yaxes(title_text="COP", row=2, col=1)
            fig.update_yaxes(title_text=y_label_temperature, row=3, col=1)

            fig.update_layout(height=600, width=300)
            fig.update_layout(legend=dict(orientation="h", yanchor="top", y=10), margin=dict(l=20,r=20,b=20,t=20,pad=0))
            st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        
        numeric_columns = df.select_dtypes(include=[float, int]).columns.tolist()
        columns_to_sum = [
            'Energi levert fra varmepumpe', 
            'Tilført energi - Bane 1', 
            'Tilført energi - Bane 2', 
            'CO2', 
            'Strømforbruk', 
            'Tilført effekt - Bane 1', 
            'Tilført effekt - Bane 2', 
            'Tilført effekt - Varmepumpe'
            ] # flere kolonner som skal summeres i stedet for å gjennomsnitt-es?
        aggregations = {col: np.sum if col in columns_to_sum else np.nanmean for col in numeric_columns}
        df_day = df.groupby(pd.Grouper(key='Tid', freq="D", offset='0S'))[numeric_columns].agg(aggregations).reset_index()
        df_day["Tidsverdier"] = df_day['Tid'].dt.strftime("%d/%m-%y, %H:01").tolist()

        df_week = df.groupby(pd.Grouper(key='Tid', freq="W", offset='0S'))[numeric_columns].agg(aggregations).reset_index()
        df_week["Tidsverdier"] = df_week['Tid'].dt.strftime("%d/%m-%y, %H:01").tolist()

        tab1, tab2, tab3 = st.tabs(["Timesoppløsning", "Dagsoppløsning", "Ukesoppløsning"])
        with tab1:
            st.caption("**Sammenstilling (energi per time, strømforbruk og utetemperatur)**")
            subplot(df=df, y_label = "Timesmidlet effekt (kWh/h)")
            st.info("Vi har ikke fått strømdata med timesoppløsning - derav jevn fordeling per døgn.")
        with tab2:
            st.caption("**Sammenstilling (energi per dag, strømforbruk og utetemperatur)**")
            subplot(df=df_day, y_label = "Energi (kWh)", y_label_temperature = "Gj.snittlig temperatur (ºC)")
        with tab3:
            if len(df)/23 >= 6:
                st.caption("**Sammenstilling (energi per uke, strømforbruk og utetemperatur)**")
                subplot(df=df_week, y_label = "Energi (kWh)", y_label_temperature = "Gj.snittlig temperatur (ºC)")
            else:
                st.warning("Det er valgt færre enn 7 dager (1 uke) i tidsintervallet.")
        
        st.markdown("---")
    ## Slutt på Åsmund fyll inn her

    def default_charts(self, df):
        #options = ["Fra bane 1", "Turtemperatur VP (varm side)", "Utetemperatur", "Temperatur ned i 40 brønner", "Temperatur opp fra 40 brønner"]
        #columns = st.multiselect("velg", options = options)
        #new_df = df[columns]
        #st.line_chart(new_df)
        c1, c2 = st.columns(2)
        with c1:
            st.caption("**Temperatur fra bane 1**")
            self.temperature_plot(df = df, series = 'Fra bane 1', min_value = -10, max_value = 5)
#        with c2:
#            st.caption("**Temperatur fra bane 2**")
#            self.temperature_plot(df = df, series = 'Fra bane 2', min_value = 0, max_value = 15)
        with c2:
            st.caption("**Turtemperatur varmepumpe (varm side)**")
            self.temperature_plot(df = df, series = 'Turtemperatur VP (varm side)', min_value = 10, max_value = 40)
        c1, c2 = st.columns(2)
        with c1:
            st.caption("**Temperatur ned i 40 brønner**")
            self.temperature_plot_two_series(df = df, series_1 = 'Temperatur ned i 40 brønner', series_2 = 'Temperatur ned i 20 brønner', min_value = -5, max_value = 15)
        with c2:
            st.caption("**Temperatur opp fra 20 og 40 brønner**")
            self.temperature_plot_two_series(df = df, series_1 = 'Temperatur opp fra 40 brønner', series_2 = 'Temperatur opp fra 20 brønner', min_value = -5, max_value = 15)
        c1, c2 = st.columns(2)
        with c1:
            st.caption("**Temperaturføler i brønn (ytre og midten)**")
            self.temperature_plot_two_series(df = df, series_1 = 'Temperaturføler i brønn (ytre)', series_2 = 'Temperaturføler i brønn (midten)', min_value = -5, max_value = 15)
        with c2:
            st.caption("**Energi tilført bane 1 (akkumulert)**")
            self.energy_effect_plot(df = df, series = "Tilført energi - Bane 1", series_label = "Energi (kWh)", separator = True, chart_type = "Bar", min_value=0, max_value = 400000)
#        with c2:
#            st.caption("**Energi tilført bane 2**")
#            self.energy_effect_plot(df = df, series = "Tilført energi - Bane 2", series_label = "Energi (kWh)", chart_type = "Bar")
#        with c2:
#            st.caption("**Energi levert fra varmepumpe (akkumulert)**")
#            self.energy_effect_plot(df = df, series = "Energi levert fra varmepumpe", series_label = "Energi (kWh)", separator = True, chart_type = "Bar", min_value=0, max_value = 1000000)
        #--
#        c1, c2 = st.columns(2)
#        with c1:
#            st.caption("**CO2 tilført bane 1**")
#            self.energy_effect_plot(df = df, series = "CO2", series_label = "tonn CO2", separator = True, chart_type = "Bar")
#        with c2:
#            st.caption("**Energi tilført bane 2**")
#            self.energy_effect_plot(df = df, series = "Tilført energi - Bane 2", series_label = "Energi (kWh)", chart_type = "Bar")
#        with c2:
#            pass
        #--
#        c1, c2 = st.columns(2)
#        with c1:
#            st.caption("**Effekt tilført bane 1**")
#            self.energy_effect_plot(df = df, series = "Tilført effekt - Bane 1", series_label = "Timesmidlet effekt (kWh/h)", average = True, chart_type = "Bar", min_value = 0, max_value = 400)
#        with c2:
#            st.caption("**Effekt tilført bane 2**")
#            self.energy_effect_plot(df = df, series = "Tilført effekt - Bane 2", series_label = "Timesmidlet effekt (kWh/h)", average = True, min_value = 0, max_value = 400)
#        with c2:
#            st.caption("**Effekt levert fra varmepumpe**")
#            self.energy_effect_plot(df = df, series = "Tilført effekt - Varmepumpe", series_label = "Timesmidlet effekt (kWh/h)", average = True, chart_type = "Bar", min_value = 0, max_value = 400, separator = False)
 
        st.markdown("---")
        st.caption("**Strømforbruk**")
        self.energy_effect_plot(df = self.df_el, series = "kWh", series_label = "Strøm (kWh)", separator = True, chart_type = "Bar")
#        st.caption("**Utetemperatur fra nærmeste værstasjon**")
#        self.energy_effect_plot(df = self.df_temperature, series = "Temperatur", series_label = "Utetemperatur", separator = True, chart_type = "Line")
#        self.energy_effect_plot(df = df, series = "Utetemperatur", series_label = "Energi (kWh)", separator = True, chart_type = "Line")   

    def show_weather_stats(self):
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("Vær", expanded = False):
                self.show_weather_statistics()
        with c2:
            with st.expander("Webkamera", expanded = False):
                self.show_webcam()

    def add_columns_to_df(self, df):
        window_size = 3
        df['Tilført effekt - Bane 1'] = df["Tilført energi - Bane 1"].diff().rolling(window=window_size).mean()
        df['Tilført effekt - Bane 2'] = df["Tilført energi - Bane 2"].diff().rolling(window=window_size).mean()
        df['Tilført effekt - Varmepumpe'] = df["Energi levert fra varmepumpe"].diff().rolling(window=window_size).mean()
        return df
    
    def resolution_picker(self, df):
        selected_option = st.selectbox("Velg oppløsning", options = ["Rådata", "Timer", "Daglig", "Ukentlig", "Månedlig", "År"])
        resolution_mapping = {
           "Rådata" : "Rådata",
           "Timer" : "H",
            "Daglig": "D",
            "Ukentlig": "W",
            "Månedlig": "M",
            "År" : "Y"
        }
        self.selected_resolution = resolution_mapping[selected_option]
        #self.selected_resolution = "Rådata"
        if self.selected_resolution != "Rådata":
            numeric_columns = df.select_dtypes(include=[float, int]).columns.tolist()
            df = df.groupby(pd.Grouper(key='Tid', freq="D", offset='0S'))[numeric_columns].mean().reset_index()
        df["Tidsverdier"] = df['Tid'].dt.strftime("%d/%m-%y, %H:01").tolist()
        return df
    
    def select_mode(self):
        with st.expander("Driftsmodus", expanded = False):
            st.selectbox("Velg modus", options = ["", "Modus 1", "Modus 2", "Modus 3", "Modus 4"])
            st.caption("*:blue[Vinter]*")
            st.write("1) :blue[Vi henter varme direkte fra varmelager og leverer til baner]")
            st.write("2) :blue[Varmepumpe leverer varme til baner]")
            st.caption("*:red[Sommer]*")
            st.write("3) :red[Vi henter varme direkte fra baner og lader opp varmelager]")
            st.write("4) :red[Vi henter varme fra baner via varmepumpe og lader opp varmelager]")
            st.warning("Mangler en kolonne som sier noe om modus")

    def get_electric_df(self):
        df_el = pd.read_excel("src/data/elforbruk/data.xlsx")
        df_el['dato'] = pd.to_datetime(df_el['dato'], format='%d.%m.%Y')
        df_el['Tidsverdier'] = df_el['dato'].dt.strftime('%d/%m-%y, %H:%M')
        self.df_el = df_el

    def remove_outliers(self, df, series):
        Q1 = df[series].quantile(0.1)
        Q3 = df[series].quantile(0.9)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df.loc[(df[series] < lower_bound) | (df[series] > upper_bound), series] = np.nan
        return df

    def main(self):
        self.streamlit_settings()
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            name, authentication_status, username, authenticator = self.streamlit_login()
            self.streamlit_login_page(name, authentication_status, username, authenticator)
        st.title("Sesongvarmelager KIL Drift") # page title
        df = self.get_full_dataframe() # get dataframe
        #df["CO2"] = df["Tilført energi - Bane 1"] * (238/(1000*1000))
        
        self.get_electric_df()
        self.get_temperature_series()

        df_el = self.df_el 
        df_el['Tidsverdier'] = pd.to_datetime(df_el['Tidsverdier'], format="%d/%m-%y, %H:%M")
        start = df['Tid'].iloc[0]
        end = df['Tid'].iloc[-1]
        res_date = start
        while res_date <= end:
            indexes_this_day = df.index[df['Tid'].dt.date == res_date.date()]
            el_this_day = df_el[df_el['Tidsverdier'].dt.date == res_date.date()]
            try:
                el_this_day = el_this_day['kWh'].iloc[0]
                el_per_h = float(el_this_day)/24
            except:
                el_per_h = float('NaN')
            for j in indexes_this_day:  
                df.at[j, 'Strømforbruk'] = el_per_h
            res_date += datetime.timedelta(days=1)
        df['Strømforbruk'] = df['Strømforbruk'].astype(float)
        df = self.add_columns_to_df(df)
        df['COP'] = df['Tilført effekt - Bane 1']/df['Strømforbruk']
        df['COP'].astype(float)
        df["Tidsverdier"] = df['Tid'].dt.strftime("%d/%m-%y, %H:01").tolist()
        df = df.mask(df == 0, None)
        df['Tilført effekt - Bane 1'] = df['Tilført effekt - Bane 1'].round()
        df['Strømforbruk'] = df['Strømforbruk'].round()
        df['Strømforbruk_akkumulert'] = df['Strømforbruk'].cumsum()
        self.total_poweruse = df['Strømforbruk_akkumulert'].max()
        self.total_energyuse = df['Tilført energi - Bane 1'].max()
        self.total_days = len(df)/23
        ####
        df = self.remove_outliers(df, "Tilført effekt - Bane 1")
        df = self.remove_outliers(df, "Tilført energi - Bane 1")
        df = self.remove_outliers(df, "COP")
        ####
        df = self.date_picker(df = df) # top level filter
            
        with st.sidebar:
            #df = self.resolution_picker(df = df)
            self.select_mode()
        with st.container():
            self.default_kpi(df = df) # kpis
        with st.container():
            ############# Åsmund
            self.new_charts(df = df)
            ############# Åsmund

            ############# Original
            self.default_charts(df = df)
            ############# Original

        st.dataframe(
            data = df, 
            height = 300, 
            use_container_width = True,
            ) # data table
        st.markdown(self.download_csv(df), unsafe_allow_html=True) # download button
        self.show_weather_stats()

if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.main()