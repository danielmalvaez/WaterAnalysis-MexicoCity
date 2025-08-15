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