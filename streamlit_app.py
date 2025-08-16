"""
Dashboard: Análisis de la disponibilidad del agua en la Ciudad de México.

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

APP_TITLE = (
    "El Futuro del Agua 💧 en la Ciudad de México 🇲🇽"
)
APP_VERSION = "v0.1.0"
AUTHOR = "Daniel Malváez"
URL = "https://www.linkedin.com/in/daniel-malvaez/"

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
# App
# ------------------------------------------------------------------------------

def main() -> None:
    """Run the Streamlit dashboard."""

    st.set_page_config(
        layout="wide",
         page_title="Dashboard : Futuro del Agua en CDMX",
        page_icon="🧊",    
        initial_sidebar_state="expanded"
        )
    
    st.title(APP_TITLE)
    
    col1, col2 = st.columns([1, 4])  # adjust ratio for width

    with col1:
        st.markdown(
            f"""
            <p style="margin-bottom:0px;"><b>Info del proyecto</b></p>
            <p style="margin-bottom:0px;">Version: <i>{APP_VERSION}</i></p>
            <p style="margin-top:2px; margin-bottom:4px;">Author: <i>{AUTHOR}</i></p>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            [![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/daniel-malvaez/)
            [![GitHub](https://img.shields.io/badge/GitHub-Repo-black?logo=github)](https://github.com/danielmalvaez/WaterAnalysis-MexicoCity)
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            **Sobre el proyecto**  
            Este dashboard muestra la situación de la escasez y disponibilidad de agua en la Ciudad de México, 
            integrando datos de consumo, sequía, densidad poblacional y reportes como fugas.  
            \n
            El objetivo de este proyecto comenzó con un análisis de la situación 
            del agua en la Ciudad de México y poder tomar una decisión más 
            informada en cuando a dónde comprar/rentar una casa o departamento. 
            Sin embargo, conforme fui realizando el análisis me di cuenta que 
            el dashboard también funciona como una fuente para generar 
            conciencia y ver como al paso de los años la creciente 
            incertidumbre de si habrá agua disponible o no es cada vez más relevante.
            """
        )

    # --------------------------------------------------------------------------
    # LOADING DATA
    # --------------------------------------------------------------------------
    dataConsumo19 = load_data("../data/consumoAgua19.csv", "csv")
    dataDrought = load_data("../data/droughtMexCity.csv", "csv")
    dataFeasibility = load_data("../data/feasibilityMexCity.csv", "csv")
    dataHogaresCol = load_data("../data/hogaresCol.csv", "csv")

    # Consumption every two months by neighborhood
    consPath = '../data/consumo-hab-promedio-bimestral-agua-por-colonia-m3.json'
    dataCons = load_data(consPath, 'json')
    habCons = gpd.GeoDataFrame.from_features(dataCons['features'])

    dataIndexSHF = pd.read_csv("../data/indexSHF.csv")
    dataReports = pd.read_csv("../data/reportsAllHist.csv")
    density = pd.read_csv("../data/density.csv")
    
    # --------------------------------------------------------------------------
    # ESCASEZ DEL AGUA (INTRODUCTION)
    # --------------------------------------------------------------------------
    # Aggregate data
    t = dataDrought.groupby(by=['DATE',
                                'MONTH',
                                'YEAR'])['VALUE'].mean().reset_index()
    t['DATE'] = pd.to_datetime(t['DATE'])
    t_filtered = t[(t['DATE'] >= "2003-01-01") & (t['DATE'] <= "2023-12-31")]

    # Create Plotly line plot
    fig = px.line(
        t_filtered,
        x='DATE',
        y='VALUE',
        markers=True,
        #labels={'VALUE': 'Drought Category', 'DATE': 'Date'},
        title='Escasez del Agua en Ciudad de México'
    )

    # Set y-axis ticks manually
    fig.update_yaxes(tickmode='array', tickvals=[1, 2, 3, 4, 5, 6])

    # Format x-axis range and tick labels
    fig.update_xaxes(
        range=[t_filtered['DATE'].min(), t_filtered['DATE'].max()],
        #tickformat="%Y",
        dtick="M12",  # One tick every 12 months
        tickangle=45
    )
    
    legend_text = """
        <b>Categorías de Escasez:</b><br>
        6 - Alta escasez<br>
        5 - Sequía excepcional<br>
        4 - Sequía extrema<br>
        3 - Sequía severa<br>
        2 - Sequía moderada<br>
        1 - Anormalmente seco<br>
        0 - Sin escasez
    """

    fig.add_annotation(
        text=legend_text,
        xref="paper", yref="paper",
        x=0.02, y=0.5,  # position at the right side
        showarrow=False,
        align="left",
        bordercolor="black",
        borderwidth=1,
        bgcolor="white",
        opacity=0.8
    )

    fig.update_layout(
        width=2400,
        height=650,
        template='plotly_white'
    )    
    
    # FIRST PLOT
    st.write(fig)
    
    
if __name__ == "__main__":
    main()