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
@st.cache_data(ttl=6*3600, show_spinner="Cargando datos de reportes de agua...")
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

def idw_interpolation(xy_known, values_known, xy_grid, power=2, k=3):
    """
    xy_known: (N, 2) array of known [lon, lat]
    values_known: (N,) array of known values
    xy_grid: (M, 2) array of grid [lon, lat]
    power: IDW power (2 is common)
    k: number of nearest neighbors to use
    """
    tree = cKDTree(xy_known)
    dists, idxs = tree.query(xy_grid, k=k)
    
    dists[dists == 0] = 1e-10  # avoid division by zero
    weights = 1 / dists**power
    weights /= weights.sum(axis=1, keepdims=True)

    interpolated = np.sum(values_known[idxs] * weights, axis=1)
    return interpolated

# ------------------------------------------------------------------------------
# LOADING DATA
# ------------------------------------------------------------------------------

reportes = load_datasets(
    repo_id="danielmlvz/water-dashboard",
    filename="reportes/part-0.parquet",
    revision="main",
)

habCons = load_datasets(
    repo_id="danielmlvz/water-dashboard",
    filename="habCons/part-0.parquet",
    revision="main",
)
habCons["geometry"] = gpd.GeoSeries.from_wkt(habCons["geometry"])
habCons = gpd.GeoDataFrame(habCons, geometry="geometry")
habCons = habCons.set_crs(epsg=4326, inplace=True)

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
        El raster map fue creado utilizando Inverse Distance Weighting, el cual 
        es un método determinista que ayuda a estimar valores desconocidos en 
        un grid, asignándole mayor influencia a aquellos puntos conocidos 
        más cercanos.
    </p>
    <p style='color:black; font-size:13px;margin-bottom:0px;'>
    Heads up, tarda ~1 min en cargar los mapas.
    </p>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("# Reportes de Agua en la Ciudad de México")


reports_count_p_y_m = reportes.groupby(by=['year', 'alcaldia', 'colonia', 'latitud', 'longitud', 'reporte']).size().reset_index(name='report_count')
pivot_all = reports_count_p_y_m.pivot_table(index=['year', 'alcaldia', 'colonia', 'latitud', 'longitud'], columns='reporte', values='report_count')

df_all = pivot_all.copy()
keep = ['Fuga', 'Falta de agua']
df_all['Otro'] = df_all.drop(columns=keep).sum(axis=1)

df_all = df_all[keep + ['Otro']]

df_all.reset_index(inplace=True)
df_all.fillna(0, inplace=True)

# Rename for clarity
df_all = df_all.rename(columns={
    'latitud': 'latitude',
    'longitud': 'longitude',
    'Falta de agua': 'falta_agua_count',
    'Fuga': 'fuga_count',
    'Otro': 'otro_count'    
})

# Data Set creation
df_falta_agua_2022 = df_all[(df_all['year'] == 2022)] 
df_falta_agua_2024 = df_all[(df_all['year'] == 2024)] 

# For mexico city map (neighborhoods included)
temp_copy = habCons[['geometry', 'alcaldia', 'colonia']]
minx, miny, maxx, maxy = temp_copy.total_bounds

# General Grid to interpolate over
grid_lon = np.linspace(minx, maxx, 200)
grid_lat = np.linspace(miny, maxy, 200)

grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
grid_points = np.c_[grid_lon_mesh.ravel(), grid_lat_mesh.ravel()]

col1Reportes, col2Reportes = st.columns([2,2])

# ------------------------------
#        MAPA DE FUGAS
# ------------------------------
with col1Reportes :     
    df_to_use = df_falta_agua_2022
    value_to_use = 'falta_agua_count'

    # Known points
    xy_known = df_to_use[['longitude', 'latitude']].values
    z_known = df_to_use[value_to_use].values 

    # Grid Already Created, then we go to interpolation directly
    z_idw_flat = idw_interpolation(xy_known, z_known, grid_points, power=0.7, k=200)
    z_idw = z_idw_flat.reshape(grid_lat_mesh.shape)
    
    # Ensure same CRS
    if getattr(habCons, "crs", None) != "EPSG:4326":
        habCons = habCons.to_crs("EPSG:4326")
    if getattr(temp_copy, "crs", None) != "EPSG:4326":
        temp_copy = temp_copy.to_crs("EPSG:4326")

    # --- your existing interpolation result: z_idw, grid_lon_mesh, grid_lat_mesh ---

    # Flatten the grid for plotting points (we’ll mask outside polygon early for speed)
    grid_df = pd.DataFrame({
        'lon': grid_lon_mesh.ravel(),
        'lat': grid_lat_mesh.ravel(),
        'value': z_idw.ravel()
    })

    # Build GeoDataFrame & spatial mask using unary_union
    cdmx_union = habCons.unary_union  # Polygon/MultiPolygon of CDMX
    grid_gdf = gpd.GeoDataFrame(
        grid_df,
        geometry=gpd.points_from_xy(grid_df['lon'], grid_df['lat']),
        crs="EPSG:4326"
    )

    # Efficient spatial mask (predicates need shapely>=2)
    mask_inside = grid_gdf.geometry.within(cdmx_union)
    grid_inside = grid_df[mask_inside].copy()

    # Optional: smooth colorbar range with robust min/max (ignore outliers)
    vmin = np.nanpercentile(grid_inside['value'], 2)
    vmax = np.nanpercentile(grid_inside['value'], 98)

    # --- figure ---
    fig = go.Figure()

    # 1) Raster points (use Scattergl for speed with many points)
    fig.add_trace(go.Scattergl(
        x=grid_inside['lon'],
        y=grid_inside['lat'],
        mode='markers',
        marker=dict(
            size=4,
            opacity=0.9,
            color=np.clip(grid_inside['value'], vmin, vmax),
            colorscale='Viridis',  # perceptually uniform
            cmin=vmin,
            cmax=vmax,
            colorbar=dict(
                title='Interpolated intensity',
                titleside='right',
                thickness=14,
                len=0.8,
                ticks='outside'
            )
        ),
        hovertemplate=(
            "Value: %{marker.color:.2f}<br>"
            "Lon: %{x:.5f}<br>"
            "Lat: %{y:.5f}<extra></extra>"
        ),
        showlegend=False,
        name='IDW'
    ))

    # 2) Add CDMX boundary (stroke)
    def _add_poly_outline(geometry, line_color='black', line_width=0.8):
        if isinstance(geometry, Polygon):
            x, y = geometry.exterior.xy
            fig.add_trace(go.Scatter(
                x=list(x), y=list(y),
                mode='lines',
                line=dict(color=line_color, width=line_width),
                showlegend=False,
                hoverinfo='skip'
            ))
        elif isinstance(geometry, MultiPolygon):
            for poly in geometry.geoms:
                _add_poly_outline(poly, line_color=line_color, line_width=line_width)

    # Outlines from your temp_copy geometries (alcaldías/colonias)
    for geom in temp_copy['geometry']:
        if geom is not None:
            _add_poly_outline(geom, line_color='rgba(0,0,0,0.5)', line_width=0.6)

    # 3) Soft fill for the whole CDMX union (nice focus effect)
    def _add_poly_fill(geometry, fillcolor='rgba(0,0,0,0.05)'):
        if isinstance(geometry, Polygon):
            x, y = geometry.exterior.xy
            fig.add_trace(go.Scatter(
                x=list(x), y=list(y),
                mode='lines',
                fill='toself',
                fillcolor=fillcolor,
                line=dict(color='rgba(0,0,0,0.75)', width=1),
                hoverinfo='skip',
                showlegend=False
            ))
        elif isinstance(geometry, MultiPolygon):
            for poly in geometry.geoms:
                _add_poly_fill(poly, fillcolor=fillcolor)

    _add_poly_fill(cdmx_union, fillcolor='rgba(0,0,0,0.04)')

    # 4) Layout tweaks: equal aspect, subtle grid, margins, title
    fig.update_layout(
        title=dict(
            text="Zonas con más reportes de falta de agua - 2022",
            x=0.02, xanchor='left', y=0.98
        ),
        width=900, height=1000,
        margin=dict(l=10, r=10, t=50, b=10),
    )

    # Equal aspect so geography isn’t distorted
    fig.update_xaxes(
        title_text='Longitude',
        showgrid=True, gridcolor='rgba(0,0,0,0.08)',
        zeroline=False
    )
    fig.update_yaxes(
        title_text='Latitude',
        showgrid=True, gridcolor='rgba(0,0,0,0.08)',
        scaleanchor='x', scaleratio=1,
        zeroline=False
    )

    # In Streamlit
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
#        MAPA DE FUGAS
# ------------------------------

with col2Reportes : 
    df_to_use = df_falta_agua_2024
    value_to_use = 'falta_agua_count'

    # Known points
    xy_known = df_to_use[['longitude', 'latitude']].values
    z_known = df_to_use[value_to_use].values  # or 'falta de agua'

    # Grid Already Created, then we go to interpolation directly
    z_idw_flat = idw_interpolation(xy_known, z_known, grid_points, power=0.8, k=40)
    z_idw = z_idw_flat.reshape(grid_lat_mesh.shape)

    # Ensure same CRS
    if getattr(habCons, "crs", None) != "EPSG:4326":
        habCons = habCons.to_crs("EPSG:4326")
    if getattr(temp_copy, "crs", None) != "EPSG:4326":
        temp_copy = temp_copy.to_crs("EPSG:4326")

    # --- your existing interpolation result: z_idw, grid_lon_mesh, grid_lat_mesh ---

    # Flatten the grid for plotting points (we’ll mask outside polygon early for speed)
    grid_df = pd.DataFrame({
        'lon': grid_lon_mesh.ravel(),
        'lat': grid_lat_mesh.ravel(),
        'value': z_idw.ravel()
    })

    # Build GeoDataFrame & spatial mask using unary_union
    cdmx_union = habCons.unary_union  # Polygon/MultiPolygon of CDMX
    grid_gdf = gpd.GeoDataFrame(
        grid_df,
        geometry=gpd.points_from_xy(grid_df['lon'], grid_df['lat']),
        crs="EPSG:4326"
    )

    # Efficient spatial mask (predicates need shapely>=2)
    mask_inside = grid_gdf.geometry.within(cdmx_union)
    grid_inside = grid_df[mask_inside].copy()

    # Optional: smooth colorbar range with robust min/max (ignore outliers)
    vmin = np.nanpercentile(grid_inside['value'], 2)
    vmax = np.nanpercentile(grid_inside['value'], 98)

    # --- figure ---
    fig = go.Figure()

    # 1) Raster points (use Scattergl for speed with many points)
    fig.add_trace(go.Scattergl(
        x=grid_inside['lon'],
        y=grid_inside['lat'],
        mode='markers',
        marker=dict(
            size=4,
            opacity=0.9,
            color=np.clip(grid_inside['value'], vmin, vmax),
            colorscale='Viridis',  # perceptually uniform
            cmin=vmin,
            cmax=vmax,
            colorbar=dict(
                title='Interpolated intensity',
                titleside='right',
                thickness=14,
                len=0.8,
                ticks='outside'
            )
        ),
        hovertemplate=(
            "Value: %{marker.color:.2f}<br>"
            "Lon: %{x:.5f}<br>"
            "Lat: %{y:.5f}<extra></extra>"
        ),
        showlegend=False,
        name='IDW'
    ))

    # 2) Add CDMX boundary (stroke)
    def _add_poly_outline(geometry, line_color='black', line_width=0.8):
        if isinstance(geometry, Polygon):
            x, y = geometry.exterior.xy
            fig.add_trace(go.Scatter(
                x=list(x), y=list(y),
                mode='lines',
                line=dict(color=line_color, width=line_width),
                showlegend=False,
                hoverinfo='skip'
            ))
        elif isinstance(geometry, MultiPolygon):
            for poly in geometry.geoms:
                _add_poly_outline(poly, line_color=line_color, line_width=line_width)

    # Outlines from your temp_copy geometries (alcaldías/colonias)
    for geom in temp_copy['geometry']:
        if geom is not None:
            _add_poly_outline(geom, line_color='rgba(0,0,0,0.5)', line_width=0.6)

    # 3) Soft fill for the whole CDMX union (nice focus effect)
    def _add_poly_fill(geometry, fillcolor='rgba(0,0,0,0.05)'):
        if isinstance(geometry, Polygon):
            x, y = geometry.exterior.xy
            fig.add_trace(go.Scatter(
                x=list(x), y=list(y),
                mode='lines',
                fill='toself',
                fillcolor=fillcolor,
                line=dict(color='rgba(0,0,0,0.75)', width=1),
                hoverinfo='skip',
                showlegend=False
            ))
        elif isinstance(geometry, MultiPolygon):
            for poly in geometry.geoms:
                _add_poly_fill(poly, fillcolor=fillcolor)

    _add_poly_fill(cdmx_union, fillcolor='rgba(0,0,0,0.04)')

    # 4) Layout tweaks: equal aspect, subtle grid, margins, title
    fig.update_layout(
        title=dict(
            text="Zonas con más reportes de falta de agua - 2024",
            x=0.02, xanchor='left', y=0.98
        ),
        width=900, height=1000,
        margin=dict(l=10, r=10, t=50, b=10),
    )

    # Equal aspect so geography isn’t distorted
    fig.update_xaxes(
        title_text='Longitude',
        showgrid=True, gridcolor='rgba(0,0,0,0.08)',
        zeroline=False
    )
    fig.update_yaxes(
        title_text='Latitude',
        showgrid=True, gridcolor='rgba(0,0,0,0.08)',
        scaleanchor='x', scaleratio=1,
        zeroline=False
    )

    # In Streamlit
    st.plotly_chart(fig, use_container_width=True)   

# -----------------------------------------
#               REFERENCES
# -----------------------------------------
st.markdown("---")
st.markdown(
    """
    <p  style='color:grey; font-size:15px;margin-bottom:0px;'>
        Fuentes : 
    </p>
    <p style='color:grey; font-size:15px;margin-bottom:0px;'>
        <a href="https://datos.cdmx.gob.mx/sv/dataset/reportes-de-agua" target="_blank">
            · SACMEX
        </a>
    </p>
    """,
    unsafe_allow_html=True
)