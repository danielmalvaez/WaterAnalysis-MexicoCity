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
    "Futuro del Agua en Ciudad de México🚰 🇲🇽"
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
#        Helpers
# ------------------------------------------------------------------------------
IDU_ORDER = ["Bajo", "Popular", "Medio", "Alto"]
IDU_COLOR = {
    "Bajo": "#9CA3AF",
    "Popular": "#60A5FA",
    "Medio": "#34D399",
    "Alto": "#F59E0B",
}

FACT_HIDR_COLOR = {
    "ROJO": "#ef4444",
    "NARANJA": "#f97316",
    "AMARILLO": "#f59e0b",
    "VERDE": "#10b981",
}

@st.cache_data(show_spinner=False)
def order_categorical(df: pd.DataFrame, col: str, order: list):
    if col in df.columns:
        df[col] = pd.Categorical(df[col], categories=order, ordered=True)
    return df


# ------------------------------------------------------------------------------
# LOADING DATA
# ------------------------------------------------------------------------------
dataConsumo19 = load_data("../data/consumoAgua19.csv", "csv")
dataFeasibility = load_data("../data/feasibilityMexCity.csv", "csv")
dataHogaresCol = load_data("../data/hogaresCol.csv", "csv")

# Consumption every two months by neighborhood
consPath = '../data/consumo-hab-promedio-bimestral-agua-por-colonia-m3.json'
dataCons = load_data(consPath, 'json')
habCons = gpd.GeoDataFrame.from_features(dataCons['features'])

dataIndexSHF = pd.read_csv("../data/indexSHF.csv")
dataReports = pd.read_csv("../data/reportsAllHist.csv")
density = pd.read_csv("../data/density.csv")

# ------------------------------------------------------------------------------
# App
# ------------------------------------------------------------------------------

def main() -> None:
    """Run the Streamlit dashboard."""

    # --------------------------------------------------------------------------
    # CONFIGURATION AND INTRODUCTION
    # --------------------------------------------------------------------------
    
    st.set_page_config(
        layout="wide",
        page_title="Dashboard : Futuro del Agua en CDMX",
        page_icon="🚰",  
        initial_sidebar_state="expanded"
    )
    
    # ---------------------------
    #        Styling
    # ---------------------------
    CUSTOM_CSS = """
        <style>
        /* Slimmer sidebar */
        section[data-testid="stSidebar"] {width: 320px !important;}
        /* Tighter headers */
        h1, h2, h3 { margin-bottom: 0.4rem; }
        /* Caption styling */
        .small {font-size: 0.85rem; color: #6b7280;}
        /* Card-style containers */
        .block-container {padding-top: 1.2rem;}
        </style>
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # ---------------------------
    #     TITLE AND HEADERS
    # ---------------------------
    st.title(APP_TITLE)
    
    col1desc, col2desc = st.columns([1, 4])  # adjust ratio for width
    with col1desc:
        st.markdown(
            f"""
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

    with st.expander("**¿Y las gráficas?**"): 
        st.write("""
                 - Arriba (esquina superior izquierda) hay dos flechas >> que te
                 mostraran las diversas páginas del proyecto y que se
                 categorizan por el tipo de información y dataset utilizado.
                 """)

    st.write("## Acerca del Proyecto")            
    st.markdown(
    """
    El objetivo de este proyecto comenzó con un análisis de la situación 
    del agua en la Ciudad de México y poder tomar una decisión más 
    informada en cuando a dónde comprar/rentar una casa o departamento. 
    Sin embargo, conforme fui realizando el análisis me di cuenta que 
    el dashboard también funciona como una fuente para generar 
    conciencia y ver como al paso de los años la creciente 
    incertidumbre de si habrá agua disponible o no es cada vez más relevante.
    """
    )
    
    st.write("## Breve Historia de la Ciudad de México")            
    st.markdown(
    """
    La Ciudad de México fue fundada como un asentamiento lacustre en un pequeño
    islote, con registro en 1325. El mito dice que Huitzilopochtli profetizó
    a los aztecas o mexicas, durante su migración desde Aztlán y que debían
    buscar en un lago un águila posada sobre un nopal con una serpiente entre
    sus garras. Luego de un arduo recorrido (de aproximadamente 210 años) llegaron a lo que 
    se conocía como el Lago de Texcoco, que es donde se fundó la ciudad de
    Tenochtitlán (actualmente la Ciudad de México) en 1325. 
    
    Con el paso del tiempo, la ciudad se convirtió en un centro de poder
    importante en Mesoamérica, siendo el imperio mexica el que tenía el poder.
    
    Fue en 1521 que sucedió la caída de este imperio, luego de una larga batalla
     para conquistar la ciudad de Tenochtitlán por parte de los españoles
    encabezados por Hernán Cortés (apoyado por clanes locales y divisiones
    enemigas de los Aztecas).    
    """
    )
    
    st.write("## Sequías crecientes")
    st.markdown(
        """
        En Mayo de 2024, el sistema Cutzamala el cuál es el que abastece a una
        gran parte de la Ciudad de México registró un nivel del 28% de
        capacidad, alcanzando un mínimo histórico. Aunque actualmente en Agosto
        2025, el nivel ya supera el 64% de capacidad, es importante destacar
        que estos niveles tan bajos cada vez son más frecuentes.    
        """
    )

    
    st.write("## ¿Y las lluvias intensas?")
    st.markdown(
        """
        Es verdad que en 2024 atravesamos una de las más intensas sequías que
        jamás hayamos visto, pero a fecha en la que estoy publicando este
        dashboard (Agosto 2025), se han registrado lluvias caóticas que han
        dejado a la Ciudad en jaque, colapsando la infraestructura de servicios
        de transporte público y vialidades importantes.
        
        Y aunque los niveles del Cutzamala parecen haberse incrementado, eso
        no significa que a futuro los meses de sequía vs los meses de lluvia
        no vayan a cambiar repentinamente.
        """
        )
    
if __name__ == "__main__":
    main()