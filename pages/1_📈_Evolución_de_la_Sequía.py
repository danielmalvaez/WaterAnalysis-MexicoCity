"""
Page 1 for Dashboard: Evolución de la sequía en México
Author: Daniel Malváez
"""

from __future__ import annotations

# Standard library imports.
import json
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

import duckdb
from huggingface_hub import hf_hub_url
from shapely.geometry import Polygon, MultiPolygon

# Configure warnings to keep the output clean.
warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

# Cache the connection (resource-level)
@st.cache_resource
def get_con():
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    return con

# Cache the data (data-level)
@st.cache_data(ttl=6*3600, show_spinner="Cargando datos de sequía…")
def load_datasets(repo_id: str, filename: str, revision: str = "main"):
    # Build a stable CDN URL (supports HTTP range properly)
    url = hf_hub_url(
        repo_id=repo_id,
        filename=filename,
        repo_type="dataset",
        revision=revision,
    )
    con = get_con()
    # Use parameter binding so the SQL text stays stable for caching
    return con.execute("SELECT * FROM read_parquet($url)", {"url": url}).df()
        
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

# ------------------------------------------------------------------------------
# LOADING DATA
# ------------------------------------------------------------------------------

dataDrought = load_datasets(
    repo_id="danielmlvz/water-dashboard",
    filename="drought/part-0.parquet",
    revision="main",
)

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
st.markdown("# Sequía en la Ciudad de México")
st.sidebar.markdown("# Time series y Mapas de Sequía/Escasez")

t1, t2 = st.tabs([
    "🌵 Evolución Sequía",
    "🏞️ Niveles del Cutzamala"
    ])

# ----------------------------------------
#  TAB2 : Evolucion de Sequia
# ----------------------------------------

with t1 : 

    selected_range = st.slider(
    "Selecciona un rango de años",
    min_value=2003,
    max_value=2003,
    value=(2003, 2023)  # Initial lower and upper bounds
    )

    # Aggregate data
    t = dataDrought.groupby(by=['DATE',
                                'MONTH',
                                'YEAR'])['VALUE_1'].mean().reset_index()
            
    t['DATE'] = pd.to_datetime(t['DATE'])        
    t_filtered = t[(t['YEAR']>=selected_range[0])&(t['YEAR'] <= selected_range[1])]

    # Create Plotly line plot
    fig1 = px.line(
        t_filtered,
        x='DATE',
        y='VALUE_1',
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
        <b  style="color:black;">Categorías de Escasez:</b><br>
        <span style="color:red;">6 - Sequía crítica</span><br>
        <span style="color:darkorange;">5 - Sequía severa</span><br>
        <span style="color:orange">4 - Sequía moderada</span><br>
        <span style="color:#1a9850;">3 - Sequía mínima</span><br>
        <span style="color:#a6d96a;">2 - Anormalmente seco</span><br>
        <span style="color:black;">1 - Sin sequía</span>
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
        template='plotly_white',
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

    st.markdown("---")

    # ---------------------------
    #             MAPS
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

    # --------------------
    # OBSERVATIONS
    # --------------------

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
    
# ----------------------------------------
#  TAB1 : Prediccion niveles del Cutzamala
# ----------------------------------------

with t2 : 
    # plot something here
    st.write("Coming soon...")