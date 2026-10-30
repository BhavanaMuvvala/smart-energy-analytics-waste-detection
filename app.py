from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from src.analyze import evaluate
st.set_page_config(page_title='Smart Energy Analytics',layout='wide')
st.title('⚡ Smart Energy Analytics & Waste Detection')
folder=Path('data')
if not (folder/'EnergyReading.csv').exists():
 st.error('Generate data first: python -m src.generator --out data');st.stop()
@st.cache_data
def read(name):
    return pd.read_csv(
        folder / f"{name}.csv",
        low_memory=False
    )
r=read('EnergyReading');t=read('Tariff');b=read('ProductionBatch');r['timestamp']=pd.to_datetime(r['timestamp'],utc=True);r['day']=r['timestamp'].dt.date
# Drop duplicate telemetry for analytics; flag anomalous rows separately.
r=r.drop_duplicates(['meter_id','timestamp'])
r['hour']=r['timestamp'].dt.hour
rates={int(h):float(next(x.rate_per_kwh for x in t.itertuples() if x.start_hour<=h<x.end_hour)) for h in range(24)}
r['rate']=r['hour'].map(rates);r['cost']=r.energy_kwh*r.rate
metrics=evaluate(folder)
a,b1,c,d=st.columns(4)
a.metric('Recorded energy (kWh)',f'{r.energy_kwh.sum():,.1f}')
b1.metric('Estimated energy cost (USD)',f'${r.cost.sum():,.2f}')
c.metric('Peak demand (kW)',f'{r.power_kw.max():,.1f}')
d.metric('Detection F1',f'{metrics["f1"]:.2%}')
st.caption('Costs are illustrative synthetic USD tariffs; anomalous telemetry is not corrected automatically.')
daily=r.groupby('day',as_index=False).agg(energy_kwh=('energy_kwh','sum'),cost=('cost','sum'))
st.plotly_chart(px.line(daily,x='day',y='energy_kwh',title='Daily energy consumption'),width="stretch")
st.plotly_chart(px.bar(r.groupby('meter_id',as_index=False)['energy_kwh'].sum(),x='meter_id',y='energy_kwh',title='Consumption by meter'),width="stretch")
st.subheader('Detected issues and evaluation');st.json(metrics)
st.dataframe(read('Recommendation'),width="stretch")
st.subheader('Production energy intensity')
st.metric('kWh per output unit (plant-level indicative)',round(r.energy_kwh.sum()/b.output_units.sum(),4))
st.warning('Ground truth is used only for evaluation, not as model features. Timezone mismatch detection is illustrative and requires external timezone evidence for production use.')
