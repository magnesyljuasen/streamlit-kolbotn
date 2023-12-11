import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import datetime as datetime
from datetime import datetime as dt

st.set_page_config(page_title="Driftsdata", page_icon="🔥")

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.title('Driftsdata for sesongvarmelager 🥵🥶')

filnavn = 'Trd_2023-06-27.csv'
filnavn2 = 'Trd_2023-06-27 (1).csv'

def custom_to_datetime(timestamp):
    return pd.to_datetime(timestamp, format="%d.%m.%Y %H:%M:%S")




df = pd.read_csv(filnavn, 
        sep=";", 
        skiprows=[0,1,2,3,4,5,6,7,8,9,10,11,12,13], 
        usecols=[0,1,2,3,4,5,6,7,8,9,10,11,12],
        header=0,
        names = ['utropstegn','tid','klokkeslett','temp_tilbane1','temp_frabane1','temp_tilbane2','temp_frabane2','RT402','RT502','temp_tilbronn1','temp_frabronn1','temp_tilbronn2','temp_frabronn2'])

df['tid'] = df['tid']+' '+df['klokkeslett']
df['tid'] = df['tid'].apply(custom_to_datetime)
df = df.drop('klokkeslett',axis=1)
#df['temp_tilbane1'] = df['temp_tilbane1'].astype(float)
#df['temp_frabane1'] = df['temp_frabane1'].astype(float)

#df['temp_tilbane2'] = df['temp_tilbane2'].astype(float)
#df['temp_frabane2'] = df['temp_frabane2'].astype(float)
#df['RT402'] = df['RT402'].astype(float)
#df['RT502'] = df['RT502'].astype(float)
#df['temp_tilbronn1'] = df['temp_tilbronn1'].astype(float)
#df['temp_frabronn1'] = df['temp_frabronn1'].astype(float)
#df['temp_tilbronn2'] = df['temp_tilbronn2'].astype(float)
#df['temp_frabronn2'] = df['temp_frabronn2'].astype(float)


df2 = pd.read_csv(filnavn2, 
        sep=";", 
        skiprows=[0,1,2,3,4,5,6,7,8,9,10,11,12,13], 
        usecols=[0,1,2,3,4,5,6,7,8,9,10,11,12],
        header=0,
        names = ['utropstegn','tid','klokkeslett','RT503','temp_VP_roed1','temp_VP_roed2','temp_VP_blaa1','temp_VP_blaa2','RT001','RT002','RP001','RP002','RN001'])
df2['tid'] = df2['tid']+' '+df2['klokkeslett']
df2['tid'] = df2['tid'].apply(custom_to_datetime)
df2 = df2.drop('klokkeslett',axis=1)



print(df2)

def plottefunksjon(x_data,x_navn,y_data1,y_navn1,y_data2,y_navn2,yakse_navn,tittel):

    til_plot = pd.DataFrame({x_navn : x_data, y_navn1 : y_data1, y_navn2 : y_data2})
    fig = px.line(til_plot, x=x_navn, y=[y_navn1,y_navn2], title=tittel, color_discrete_sequence=['#367A2F', '#FFC358'])
    fig.update_layout(xaxis_title=x_navn, yaxis_title=yakse_navn,legend_title=None)
    st.plotly_chart(fig)

# Baner
plottefunksjon(x_data=df['tid'],x_navn='Tid',y_data1=df['temp_tilbane1'],y_navn1='Temperatur til bane',y_data2=df['temp_frabane1'],y_navn2='Temperatur fra bane',yakse_navn='Temperatur (\u2103)',tittel='Tur- og returtemperaturer for bane 1')
plottefunksjon(x_data=df['tid'],x_navn='Tid',y_data1=df['temp_tilbane2'],y_navn1='Temperatur til bane',y_data2=df['temp_frabane2'],y_navn2='Temperatur fra bane',yakse_navn='Temperatur (\u2103)',tittel='Tur- og returtemperaturer for bane 2')

# Ukjent
plottefunksjon(x_data=df['tid'],x_navn='Tid',y_data1=df['RT402'],y_navn1='Ukjent temp. 1',y_data2=df['RT502'],y_navn2='Ukjent temp. 2',yakse_navn='Temperatur (\u2103)',tittel='Ukjente temperaturer')

# Brønner
plottefunksjon(x_data=df['tid'],x_navn='Tid',y_data1=df['temp_tilbronn1'],y_navn1='Temperatur til brønn',y_data2=df['temp_frabronn1'],y_navn2='Temperatur fra brønn',yakse_navn='Temperatur (\u2103)',tittel='Tur- og returtemperaturer for brønn 1')
plottefunksjon(x_data=df['tid'],x_navn='Tid',y_data1=df['temp_tilbronn2'],y_navn1='Temperatur til brønn',y_data2=df['temp_frabronn2'],y_navn2='Temperatur fra brønn',yakse_navn='Temperatur (\u2103)',tittel='Tur- og returtemperaturer for brønn 2')

# Varmepumpe
plottefunksjon(x_data=df2['tid'],x_navn='Tid',y_data1=df2['temp_VP_roed1'],y_navn1='Temperatur VP rød side 1',y_data2=df2['temp_VP_roed2'],y_navn2='Temperatur VP rød side 2',yakse_navn='Temperatur (\u2103)',tittel='Temperaturer rød side av VP')
plottefunksjon(x_data=df2['tid'],x_navn='Tid',y_data1=df2['temp_VP_blaa1'],y_navn1='Temperatur VP blå side 1',y_data2=df2['temp_VP_blaa2'],y_navn2='Temperatur VP blå side 2',yakse_navn='Temperatur (\u2103)',tittel='Temperaturer blå side av VP')



