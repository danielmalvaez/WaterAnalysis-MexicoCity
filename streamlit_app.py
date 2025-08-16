"""
Dashboard: Análisis de la disponibilidad del agua en la Ciudad de México.

Author: Daniel Malváez
"""

from __future__ import annotations

# Standard library imports.
import json
import unicodedata
import warnings

# Third-party imports.
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import squarify
import streamlit as st
from scipy.spatial import cKDTree
from shapely.geometry import Point
from tqdm import tqdm

# Configure warnings to keep the output clean.
warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

APP_TITLE = (
    "Escasez de Agua 💧 y cómo impacta las decisiones al momento de "
    "adquirir/rentar una propiedad en Ciudad de México 🏙️"
)
APP_VERSION = "v0.1.0"

# WATER DATASETS

# Data consumption during the whole 2019 by neighborhood
watConsPath = "data/water/consumo/consumo_agua_historico_2019.csv"
# Municipalities with drought data and higher/lower probability of drought
droughtPath = "data/water/sequia/Municipios_con_ sequia.xlsx"
# Water Reports in Mexico City by neighborhood.
reports2224Path = "data/water/reportes/reportes_agua_2024_01.csv"
reportsHistory = "data/water/reportes/reportes_agua_hist.csv"
# Hidric feasibility
hidFeasPath = "data/water/factibilidad/factibilidad-hdrica.json"
# Consumption every two months by neighborhood
habPath = ("data/water/consumo/consumo-habitacional-promedio-"
           "bimestral-de-agua-por-colonia-m3.json")    

# PROPERTY DATASETS

# Index SHF for housing price in the area
indexSHFPath = "data/property-population/SHF/indice_SHF.csv"
# Population Growth Rate
growthRateAlcPath = ("data/property-population/CrecimientoPoblacional/"
                     "poblacion_total_tasa_crecimiento_alcaldia_1.2.csv3")
# Density
housesColPath = ("data/property-population/"
                "Hogares por colonia/hogares_colonia.shp")
# Concentración habitacional
densityPath = "data/property-population/alta_concentracion/zonas_vivienda.shp"

# ------------------------------------------------------------------------------
# Reading & Preprocessing Data
# ------------------------------------------------------------------------------

@st.cache_data
def load_data(path, ext = 'csv', sheet_name = ''):
    if ext == 'csv':
        return pd.read_csv(path)
    elif ext == 'xlsx' : 
        return pd.read_excel(path, sheet_name=sheet_name)
    elif ext == 'json' : 
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

# ---------------------
# WATER DATA
# ---------------------

# Water Consumption 2019
watCons19 = load_data(watConsPath,'csv')
watCons19.drop_duplicates(inplace=True)

# Drought MEX CITY
drought = load_data(droughtPath, ext='xlsx',
                    sheet_name='MONITOR - SEMAFORO - USO EFIC')
cldCols = drought.columns.to_series().where(
    ~drought.columns.str.contains('^Unnamed'), '')
drought.columns = [x + '/' + y if x != '' else y 
                    for x, y in zip(cldCols, drought.iloc[0].astype(str))]
drought = drought.iloc[1:].reset_index().iloc[:,1:]

# Water Reports in Mexico City by neighborhood.
reports2224 = load_data(reports2224Path, ext='csv')
reportsHist = load_data(reportsHistory,ext='csv')

# Hidric feasibility
factFeats = load_data(hidFeasPath, ext='json')
fact = gpd.GeoDataFrame.from_features(factFeats["features"])

# Consumption every two months by neighborhood
habConsFeats = load_data(habPath, ext='json')
habCons = gpd.GeoDataFrame.from_features(habConsFeats['features'])

# ---------------------
# PROPERTY DATA
# ---------------------

indexSHF = pd.read_csv(indexSHFPath, encoding='iso-8859-1', delimiter=';')
data_tasa_crecimiento_alcaldia = pd.read_csv(growthRateAlcPath,encoding='utf-8')
data_hogares_col = gpd.read_file(housesColPath)
data_concentracion = gpd.read_file(densityPath)

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# App
# ------------------------------------------------------------------------------

def main() -> None:
    """Run the Streamlit dashboard."""
    st.set_page_config(layout="wide")
    st.title(APP_TITLE)
    st.markdown(f"_{APP_VERSION}_")        
    
    
    
if __name__ == "__main__":
    main()