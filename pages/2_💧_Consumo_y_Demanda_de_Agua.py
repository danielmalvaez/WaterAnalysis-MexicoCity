"""
Page 1 for Dashboard: Evolución de la sequía en México

Author: Daniel Malváez
"""

from __future__ import annotations

# Standard library imports.
import json
import unicodedata
import warnings

# Streamlit import
import streamlit as st

# --------------------
# Third Party Imports
# --------------------
# Data management
import pandas as pd
import numpy as np
import json
# Treemap visualization
import squarify
from shapely.geometry import Point
import seaborn as sns
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px # Interactive
from matplotlib import cm
from matplotlib.colors import Normalize, to_hex
# To make spatial data
from scipy.spatial import cKDTree
import geopandas as gpd
# No accents
import unicodedata
# Provide a running estimate
from tqdm import tqdm

# Configure warnings to keep the output clean.
warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------
@st.cache_data
def load_data(path, ext = 'csv', sheet_name = ''):
    """Function that loads information and stores in into the cache

    Args:
        path (str): internal path where the data or file is
        ext (str, optional): type of file. Defaults to 'csv'.
        sheet_name (str, optional): name of the sheet for excel files.
                                    Defaults to ''.

    Returns:
        Object : DataFrame Object
   """
    if ext == 'csv':
        return pd.read_csv(path)
    elif ext == 'xlsx' : 
        return pd.read_excel(path, sheet_name=sheet_name)
    elif ext == 'json' : 
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

# ------------------------------------------------------------------------------
# LOADING DATA
# ------------------------------------------------------------------------------

dataConsumo19 = load_data("../data/consumoAgua19.csv", "csv")

# ------------------------------------------------------------------------------
# PAGE INFORMATION
# ------------------------------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Dashboard : Futuro del Agua en CDMX",
    page_icon="🚰",  
    initial_sidebar_state="expanded"
    )

# Main page content
st.markdown("# Consumo de Agua en la Ciudad de México")
st.sidebar.markdown("# TreeMap y Pie Charts")

# Add filter
option = st.selectbox(
    "Selecciona un bimestre :",
    ("Febrero", "Abril", "Junio"),
)

mappingDate = {"Febrero" : "2019-02-28", 
               "Abril" : "2019-04-30",
               "Junio" : "2019-06-30"}

dataConsumo19F = dataConsumo19[dataConsumo19['fecha_referencia'] == mappingDate[option]]

# Neighborhood aggregation
consWatAgg = dataConsumo19F.groupby(['colonia', 'alcaldia']).agg({
    'consumo_total': 'sum',
    'inmuebles_domesticos': 'sum',
    'consumo_total_dom': 'sum',
    'inmuebles_no_domesticos': 'sum',
    'consumo_total_no_dom': 'sum',
    'inmuebles_mixtos': 'sum',
    'consumo_total_mixto': 'sum',
    'total_inmuebles': 'sum'
}).reset_index()

# We filter out rows where all consumption values are zero
consWatAgg = consWatAgg[~(consWatAgg.iloc[:, 2:] == 0).all(axis=1)]

# insert a pivot and create new columns based on indice_des 
shareIdxDev = dataConsumo19F.pivot_table(
    index=['colonia', 'alcaldia'],
    columns='indice_des',
    values='total_inmuebles',
    aggfunc='sum'
).reset_index()

allAgg = consWatAgg.merge(shareIdxDev, on=['colonia', 'alcaldia'], how='left')
allAgg.fillna(0, inplace=True)
allAgg.head()

nf_h = allAgg.sort_values(by='consumo_total', ascending=False)

# Prepare the data
d = nf_h.head(20).copy()

# Optional: format the custom label
d['label'] = d.apply(lambda row: f"{row['colonia']},<br>{row['alcaldia']}<br>({int(row['consumo_total'])} m³)", axis=1)

# Plotly treemap
fig = px.treemap(
    d,
    path=['alcaldia', 'colonia'],  # hierarchy levels
    values='consumo_total',
    hover_data={'consumo_total': True},
    color='consumo_total',
    color_continuous_scale='viridis'
)

fig.update_traces(textinfo="label+value")
fig.update_layout(
    title="Top 20 Colonias con Mayor Consumo Total de Agua (m³)",
    title_font_size=20,
    margin=dict(t=50, l=25, r=25, b=25)
)
st.write(fig)
