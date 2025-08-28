"""
Page 3 for Dashboard: Reportes de Fugas
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
import textwrap
import matplotlib.colors as mcolors

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
@st.cache_data(ttl=6*3600, show_spinner="Cargando datos de consumo y demanda…")
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
        
# Helper: tidy/wrap long labels so they don't overflow tiles
def wrap_label(s, width=18):
    if pd.isna(s):
        return s
    return "<br>".join(textwrap.fill(str(s), width=width).split("\n"))

# ------------------------------------------------------------------------------
# LOADING DATA
# ------------------------------------------------------------------------------

reportes = load_datasets(
    repo_id="danielmlvz/water-dashboard",
    filename="reportes/part-0.parquet",
    revision="main",
)

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
st.markdown("# Reportes de Agua en la Ciudad de México")
st.markdown(
    """
    <p  style='color:grey; font-size:13px;margin-bottom:0px;'>
        Información disponible de 2018 al 2024.
    </p>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("# Reportes de Agua en la Ciudad de México")

st.write("WIP")