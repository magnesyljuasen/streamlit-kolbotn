import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
import datetime as datetime
from datetime import datetime as dt
import yaml
import base64
from PIL import Image
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.add_vertical_space import add_vertical_space
from src.scripts import streamlit_settings, switch_pages

streamlit_settings()

class VisualizeData:
    def __init__(self):
        self.FILEPATH1 = 'src/data/csv/Kolbotn_1.txt'
        self.FILEPATH2 = 'src/data/csv/Kolbotn_2.txt'

    def __to_datetime(self, timestamp):
        return pd.to_datetime(timestamp, format="%d.%m.%Y %H:%M:%S")

    def __csv_to_dataframe(self, filepath):
        df = pd.read_csv(
            filepath, 
            sep = ';', 
            skiprows = 14,
            header=0,
            #names = ['utropstegn','tid','klokkeslett','RT503','temp_VP_roed1','temp_VP_roed2','temp_VP_blaa1','temp_VP_blaa2','RT001','RT002','RP001','RP002','RN001','unnamed']
            )
        #--
        df['Datetime'] = df['Date'] + ' ' + df['Time']
        df['Datetime'] = df['Datetime'].apply(self.__to_datetime)
        df = df.drop(['Time', 'Date'], axis=1)
        df = df.drop(['#!(s)', 'Unnamed: 13'], axis=1)

        column_mapping = {
            'Datetime': 'Tid',
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

        df.rename(columns=column_mapping, inplace=True)
        return df

    def import_csv(self):
        self.df1 = self.__csv_to_dataframe(filepath = self.FILEPATH1)
        self.df2 = self.__csv_to_dataframe(filepath = self.FILEPATH2)
        df_concatted = pd.concat([self.df1.set_index('Tid'), self.df2.set_index('Tid')], axis=1, join='outer')
        df_concatted.reset_index(inplace=True)
        self.df = df_concatted
        
    
    def plot_xy(self, df):
        fig = px.line(df, x='Tid', y=df.columns.values)
        fig["data"][0]["showlegend"] = True
        fig.update_layout(
        margin=dict(l=50,r=50,b=10,t=10,pad=0),
        yaxis_title="Parameter",
        xaxis_title="Tid",
        plot_bgcolor="white",
        )
        fig.update_xaxes(
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        st.plotly_chart(fig)

        

def main():
    visualize_data = VisualizeData()
    visualize_data.import_csv()
    st.write(visualize_data.df)
    visualize_data.plot_xy(visualize_data.df)

if __name__ == "__main__":
    main()
