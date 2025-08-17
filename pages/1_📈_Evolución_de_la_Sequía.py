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
        
def plot_static_map(df, title, show=True, write=False, file_name=None) : 
    # Define your color mapping
    color_discrete_map = {
        'ROJO': '#d73027',
        'NARANJA': '#fdae61',
        'AMARILLO': '#ffffbf',
        'VERDE': '#1a9850',
        'PRE-ALERTA': '#a6d96a',
        'SIN SEQUIA': '#f0f0f0'
    }

    fig = px.choropleth_mapbox(
        df,
        geojson=df.__geo_interface__,
        locations=df.index,  # You can use index if each row is unique
        color="value",  # Use categorical value, not raw hex codes
        hover_name="NOMBRE_MUN",
        hover_data=["DATE", "DESC"],
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": 19.33, "lon": -99.13},
        opacity=0.8,
        color_discrete_map=color_discrete_map
    )


    fig.update_layout(
        margin={"r":0, "t":30, "l":0, "b":0},
        title=title,
        width=1000,    # width in pixels
        height=700,    # height in pixels
        showlegend=False
    )

    return fig
    
def plot_animated_map(df, title, show=True, write=False, file_name=None) : 
    # Convert DATE to string if it's datetime (required by Plotly animation)
    # df["DATE"] = df["DATE"].astype(str)

    # Define category → color mapping
    color_discrete_map = {
        'SIN SEQUIA': '#f0f0f0',
        'PRE-ALERTA': '#d9d9d9',
        'VERDE': '#a6d96a',
        'AMARILLO': '#ffffbf',
        'NARANJA': '#fdae61',
        'ROJO': '#d73027'
    }
    
    color_map = {
    "1": '#f0f0f0',     # Very light gray / near white
    "2": '#1a9850',     # Light gray
    "3": '#a6d96a',          # Soft green
    "4": '#ffe066',       # Yellow
    "5": '#fdae61',        # Orange
    "6": '#d73027'            # Red
    }
    
    mxc_drought_t = df[['DATE', 'geometry', 'NOMBRE_MUN', 'VALUE', 'color']]
    
    vmin = np.log10(mxc_drought_t["VALUE"].min())
    vmax = np.log10(mxc_drought_t["VALUE"].max())

    def normalize(val):
        return (val - 1) / (6 - 1)

    custom_scale = [
        (normalize(1), "#f0f0f0"),
        (normalize(2), "#1a9850"),
        (normalize(3), "#a6d96a"),
        (normalize(4), "#ffe066"),
        (normalize(5), "#fdae61"),
        (normalize(6), "#d73027"),
    ]    

    fig = px.choropleth_mapbox(mxc_drought_t,
                        geojson=mxc_drought_t.__geo_interface__,
                        locations="NOMBRE_MUN",
                        color=np.log10(mxc_drought_t["VALUE"]),
                        hover_name="NOMBRE_MUN",
                        hover_data=["VALUE"],
                        animation_frame='DATE',
                        featureidkey='properties.NOMBRE_MUN',  
                        # color_continuous_midpoint = 1,
                        color_continuous_scale=custom_scale,
                        range_color=[0,1],
                        # color_discrete_map=color_map,
                        mapbox_style="carto-positron",
                        center={"lat": 19.33, "lon": -99.1332}, 
                        zoom=9,)

    fig.update_layout(margin=dict(l=20,r=0,b=0,t=70,pad=0),
                    paper_bgcolor="white",
                    width = 1000,
                    height= 700,
                    title_text = 'Evolución de la Sequía en la Ciudad de México 2003-2023',
                    font_size=18,
                    )

    return fig
    
def normalize(val):
    return (val - 1) / (6 - 1)

custom_scale = [
        (normalize(1), "#f0f0f0"),
        (normalize(2), "#1a9850"),
        (normalize(3), "#a6d96a"),
        (normalize(4), "#ffe066"),
        (normalize(5), "#fdae61"),
        (normalize(6), "#d73027"),
    ] 

# ------------------------------------------------------------------------------
# LOADING DATA
# ------------------------------------------------------------------------------

dataDrought = load_data("../data/droughtMexCity.csv", "csv")

# Data Drought adjustments for a geopandas df
dataDrought["geometry"] = gpd.GeoSeries.from_wkt(dataDrought["geometry"])
dataDrought = gpd.GeoDataFrame(dataDrought, geometry="geometry")
dataDrought = dataDrought.set_crs(epsg=4326, inplace=True)

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
st.markdown("# Evolución de la Sequía en la Ciudad de México")
st.sidebar.markdown("# Time series y Mapas de Sequía/Escasez")
        
selected_range = st.slider(
"Selecciona un rango de años",
min_value=2003,
max_value=2003,
value=(2003, 2023)  # Initial lower and upper bounds
)

# Aggregate data
t = dataDrought.groupby(by=['DATE',
                            'MONTH',
                            'YEAR'])['VALUE'].mean().reset_index()
        
t['DATE'] = pd.to_datetime(t['DATE'])        
t_filtered = t[(t['YEAR']>=selected_range[0])&(t['YEAR'] <= selected_range[1])]

# Create Plotly line plot
fig1 = px.line(
    t_filtered,
    x='DATE',
    y='VALUE',
    markers=True,
    #labels={'VALUE': 'Drought Category', 'DATE': 'Date'},
    title='Niveles de Sequía Promedio en Ciudad de México'
)

# Set y-axis ticks manually
fig1.update_yaxes(tickmode='array', tickvals=[1, 2, 3, 4, 5, 6])

# Format x-axis range and tick labels
fig1.update_xaxes(
    range=[t_filtered['DATE'].min(), t_filtered['DATE'].max()],
    #tickformat="%Y",
    dtick="M12",  # One tick every 12 months
    tickangle=45
)

legend_text = """
    <b>Categorías de Escasez:</b><br>
    6 - Sequía crítica<br>
    5 - Sequía severa<br>
    4 - Sequía moderada<br>
    3 - Sequía mínima<br>
    2 - Anormalmente seco<br>
    1 - Sin sequía
"""

fig1.add_annotation(
    text=legend_text,
    xref="paper", yref="paper",
    x=0.72, y=0.95,  # position at the right side
    showarrow=False,
    align="left",
    bordercolor="lightgray",
    borderwidth=1,
    bgcolor="white",
    opacity=1
)
    
fig1.update_layout(
    width=2400,
    height=500,
    template='plotly_white'
)

# WRITING FIRST PLOT
st.write(fig1)
st.markdown(
    """
    <p  style='color:grey; font-size:13px;margin-bottom:0px;'>
        Fuente:
        <a href="https://historico.datos.gob.mx/busca/dataset/municipios-con-sequia" target="_blank">
            CONAGUA
        </a>
    </p>
    <p style='color:grey; font-size:13px;'>
        Metodología : Promedio mensual de la Ciudad de México calculado con los 
        valores de sequía por alcaldía.
    </p>
    """,
    unsafe_allow_html=True
)  

# ---------------------------
#        Observations
# ---------------------------
st.markdown("---")
st.markdown(
    """
    **Observaciones**
    - En 2009, una intensa sequía afectó a la Ciudad de México, 
    causando graves problemas de suministro de agua, además de pérdidas
    millonarias reportadas. Todo debido a la falta de lluvias y gestión
    inadecuada de los recursos hídricos. 
    - Actualmente el monitor de sequía a Julio 2025 se encuentra 
    sanamente en *Sin Sequía*.
    """
)

# ---------------------------
#        Observations
# ---------------------------

# Single value slider
value = st.slider(
    "Selecciona un año",
    min_value=2003,
    max_value=2023,
    value=2023  # default starting point
)

dataDroughtJan = dataDrought[(dataDrought['YEAR'] == value)
                            & (dataDrought['MONTH'] == "January")]
dataDroughtApril = dataDrought[(dataDrought['YEAR'] == value) 
                            & (dataDrought['MONTH'] == "April")]
dataDroughtJuly = dataDrought[(dataDrought['YEAR'] == value) 
                            & (dataDrought['MONTH'] == "July")]
dataDroughtOct = dataDrought[(dataDrought['YEAR'] == value) 
                            & (dataDrought['MONTH'] == "October")]

col1,col2,col3,col4 = st.columns([1, 1, 1 , 1])  # adjust ratio for width

with col1 : 
    map1 = plot_static_map(dataDroughtJan, "Escasez en Enero")
    st.write(map1)
    
with col2 : 
    map2 = plot_static_map(dataDroughtApril, "Escasez en Abril")
    st.write(map2)

with col3 : 
    map3 = plot_static_map(dataDroughtJuly, "Escasez en Julio")
    st.write(map3)
    
with col4 : 
    map4 = plot_static_map(dataDroughtOct, "Escasez en Octubre")
    st.write(map4)

# WRITING FIRST PLOT
st.markdown(
    """
    <p  style='color:grey; font-size:13px;margin-bottom:0px;'>
        Fuente:
        <a href="https://historico.datos.gob.mx/busca/dataset/municipios-con-sequia" target="_blank">
            CONAGUA
        </a>
    </p>
    <p style='color:grey; font-size:13px;'>
        Metodología : Rangos determinados por CONAGUA.
    </p>
    """,
    unsafe_allow_html=True
)  