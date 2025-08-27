"""
Page 2 for Dashboard: Consumo y demanda de Agua
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

dataConsumo19 = load_datasets(
    repo_id="danielmlvz/water-dashboard",
    filename="consumo19/part-0.parquet",
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

# Last Value is a None value
habCons = habCons.iloc[:-1]

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
st.markdown(
    """
    <p  style='color:grey; font-size:13px;margin-bottom:0px;'>
        Información disponible a los primeros bimestres del 2019
    </p>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("# Consumo y Demanda de Agua en la CDMX")

# -------------------------------------------
#  DATA AGGREGATION THAT WORKS FOR ALL TABS
# -------------------------------------------

# Add filter
option = st.selectbox(
    "Selecciona un bimestre disponible :",
    ("Febrero", "Abril", "Junio"),
)

mappingDate = {"Febrero" : "2019-02-28", 
            "Abril" : "2019-04-30",
            "Junio" : "2019-06-30"}

# Filtering using the provided bimester and date by user
consF = dataConsumo19[dataConsumo19['fecha_referencia'] == mappingDate[option]]

# Neighborhood aggregation
consWatAgg = consF.groupby(['colonia', 'alcaldia']).agg({
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
shareIdxDev = consF.pivot_table(
    index=['colonia', 'alcaldia'],
    columns='indice_des',
    values='total_inmuebles',
    aggfunc='sum'
).reset_index()

allAgg = consWatAgg.merge(shareIdxDev, on=['colonia', 'alcaldia'], how='left')
allAgg.fillna(0, inplace=True)
allAgg = allAgg.sort_values(by="consumo_total", ascending=False)

# -----------------------------------------
# TABS
# -----------------------------------------

tab1, tab2, tab3 = st.tabs([
    "🏢 Top 20 Colonias Mayor Consumo",
    "📈 Relación # Inmuebles vs Consumo (m3)",
    "🔍 Encuentra tu colonia (mapa 🗺️)"
])

with tab1 : 

    # Keep only the global Top 20 by consumo_total 
    d_top = allAgg.nlargest(20, "consumo_total").copy()
    
    # Formatting the custom label
    d_top['label'] = d_top.apply(lambda row: f"{row['colonia']},<br>{row['alcaldia']}<br>({int(row['consumo_total'])} m³)", axis=1)
    
    # Wrap long colonia names for readability inside tiles
    d_top["colonia_wrapped"] = d_top["colonia"].apply(wrap_label)

    # -----------------------------------------
    #                  KPIs
    # -----------------------------------------

    colsKPI1, colsKPI2 = st.columns([1,1])
    
    with colsKPI1 : 
        total_consumo_top20 = d_top["consumo_total"].sum()

        # Wrap metric in a centered div
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h4 style="margin-bottom:0;">Consumo Total Bimestral de las 20 Colonias (m³)</h4>
                <h2 style="margin-top:0;">{total_consumo_top20:,.0f}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

    with colsKPI2:
        # Wrap metric in a centered div
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h4 style="margin-bottom:0;">Equivalente a llenar Estadios Aztecas (1.8 millones m³ c/u)</h4>
                <h2 style="margin-top:0;">{total_consumo_top20 / 1800000:.2f}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # -----------------------------------------
    #     TREE MAP : TOP 20 colonias
    # -----------------------------------------
    # Build figure
    fig = px.treemap(
        d_top,
        path=["alcaldia", "colonia_wrapped"],     # hierarchy
        values="consumo_total",
        color="consumo_total",
        color_continuous_scale="Blues",           # water vibe; try "PuBu" or "Teal"
        # range_color=(d_top["consumo_total"].min(), d_top["consumo_total"].max()),  # optional: lock scale
    )

    # Text & hover: label + value + % parent/root, nicely formatted
    fig.update_traces(
        textinfo="label+value+percent parent",
        texttemplate="<b>%{label}</b><br>%{value:,.0f} m³<br>%{percentParent:.1%} del nivel",
        hovertemplate=(
            "<b>%{label}</b><br>" +
            "Consumo: %{value:,.0f} m³<br>" +
            "Participación en su padre: %{percentParent:.1%}<br>" +
            "Participación total: %{percentRoot:.1%}<extra></extra>"
        ),
        marker=dict(
            line=dict(width=0.6, color="white")   # crisp tile borders
        ),
        tiling=dict(
            pad=2                                  # compact but not cramped
        ),
        maxdepth=3                                 # prevents over-drill if any
    )

    # Titles, margins, fonts, colorbar
    fig.update_layout(
        title=dict(
            text="Top 20 Colonias con Mayor Consumo Total de Agua (m³)",
            x=0.02, xanchor="left",
            font=dict(size=22, family="Inter, system-ui, sans-serif")
        ),
        margin=dict(t=60, r=20, b=20, l=20),
        coloraxis_colorbar=dict(
            title="Consumo (m³)",
            tickformat=",",
            len=0.8
        ),
        uniformtext=dict(minsize=12, mode="show"),  # ensure small tiles still show text
        hoverlabel=dict(font_size=12)
    )

    # Optional: show a breadcrumb/path bar for context
    fig.update_layout(
        treemapcolorway=None,
        # Pathbar at top with subtle styling
        # (Plotly auto-shows it; tweak font if you wish)
    )

    # Optional: make root tile a neutral color (less dominant)
    fig.update_traces(root_color="lightgray")

    # In Streamlit:
    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------
    #     PIE PLOTS : PROPORCIONES
    # -----------------------------------------
    
    col1, col2, col3 = st.columns([2,2,2])

    # ----------------------------
    #       IDX DESARROLLO
    # ----------------------------
    
    with col1 : 
        
        # --- Consistent color map with your other plots ---
        color_map = {
            "ALTO":   "#1f77b4",  # blue
            "MEDIO":  "#2ca02c",  # green
            "BAJO":   "#ff7f0e",  # orange
            "POPULAR":"#d62728",  # red
        }
        order_idx = ["ALTO", "MEDIO", "BAJO", "POPULAR"]

        # ----- Build the Top-20 slice sums from d_top -----
        # Make sure columns exist and are numeric
        cols_idu = ["ALTO", "BAJO", "MEDIO", "POPULAR"]
        d_top_num = d_top.copy()
        for c in cols_idu:
            d_top_num[c] = pd.to_numeric(d_top_num[c], errors="coerce").fillna(0)

        sizes = [d_top_num[c].sum() for c in cols_idu]
        labels = ["ALTO", "BAJO", "MEDIO", "POPULAR"]

        df_pie = pd.DataFrame({"IDU": labels, "Proporcion": sizes})
        # sort by fixed order for stable legend
        df_pie["IDU"] = pd.Categorical(df_pie["IDU"], categories=order_idx, ordered=True)
        df_pie = df_pie.sort_values("IDU")

        # ----- Donut chart -----
        fig_pie = px.pie(
            df_pie,
            names="IDU",
            values="Proporcion",
            color="IDU",
            color_discrete_map=color_map,
            hole=0.55,  # donut
        )

        fig_pie.update_traces(
            textinfo="percent+label",
            textposition="inside",
            insidetextorientation="horizontal",
            pull=[0.03 if v == df_pie["Proporcion"].max() else 0 for v in df_pie["Proporcion"]],  # slight emphasis on largest
            marker=dict(line=dict(width=1, color="white")),
            hovertemplate="<b>%{label}</b><br>Proporción: %{percent}<br>Valor: %{value:,.0f}<extra></extra>"
        )

        total_val = df_pie["Proporcion"].sum()
        fig_pie.update_layout(
            title=dict(
                text="Proporción de IDU en las Top 20 colonias más consumidoras",
                x=0.02, xanchor="left", font=dict(size=20)
            ),
            margin=dict(t=60, r=20, b=20, l=20),
            legend=dict(orientation="v", yanchor="bottom", y=0.80, xanchor="left", x=0, title="Índice de Desarrollo"),
            annotations=[
                dict(
                    text=f"Total Inmuebles<br><b>{total_val:,.0f}</b>",
                    showarrow=False, x=0.5, y=0.5, font=dict(size=14, color="gray")
                )
            ],
            height=520,
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    # ----------------------------
    #       IDX DESARROLLO
    # ----------------------------
    
    with col2 : 
        # ---------- Datos (a partir de d_top = d) ----------
        cols_inm = ["inmuebles_domesticos", "inmuebles_no_domesticos", "inmuebles_mixtos"]
        d_inm = d_top.copy()
        for c in cols_inm:
            d_inm[c] = pd.to_numeric(d_inm[c], errors="coerce").fillna(0)

        sizes = [
            d_inm["inmuebles_domesticos"].sum(),
            d_inm["inmuebles_no_domesticos"].sum(),
            d_inm["inmuebles_mixtos"].sum(),
        ]
        labels = ["Inmuebles Domésticos", "Inmuebles No Domésticos", "Inmuebles Mixtos"]

        df_pie = pd.DataFrame({"Tipo de Inmueble": labels, "Cantidad": sizes})

        # Orden fijo para una leyenda estable
        order_tipos = ["Inmuebles Domésticos", "Inmuebles No Domésticos", "Inmuebles Mixtos"]
        df_pie["Tipo de Inmueble"] = pd.Categorical(df_pie["Tipo de Inmueble"],
                                                    categories=order_tipos, ordered=True)
        df_pie = df_pie.sort_values("Tipo de Inmueble")

        # Paleta consistente (alta legibilidad)
        color_map = {
            "Inmuebles Domésticos": "#ff8c42",   # orange
            "Inmuebles No Domésticos": "#f6416c",# pink/red
            "Inmuebles Mixtos": "#6a4c93",       # deep purple
        }

        # ---------- Donut plot ----------
        fig_pie = px.pie(
            df_pie,
            names="Tipo de Inmueble",
            values="Cantidad",
            color="Tipo de Inmueble",
            color_discrete_map=color_map,
            hole=0.55,
        )

        fig_pie.update_traces(
            textinfo="percent+label",
            textposition="inside",
            insidetextorientation="horizontal",
            marker=dict(line=dict(width=1, color="white")),
            pull=[0.03 if v == df_pie["Cantidad"].max() else 0 for v in df_pie["Cantidad"]],
            hovertemplate="<b>%{label}</b><br>Porción: %{percent}<br>Cantidad: %{value:,.0f}<extra></extra>",
        )

        total_val = df_pie["Cantidad"].sum()
        fig_pie.update_layout(
            title=dict(
                text="Proporción del tipo de inmuebles en las Top 20 colonias más consumidoras",
                x=0.02, xanchor="left", font=dict(size=20)
            ),
            margin=dict(t=60, r=20, b=20, l=20),
            legend=dict(orientation="v", yanchor="bottom", y=0.85, xanchor="left", x=0,
                        title="Tipo de Inmueble"),
            annotations=[
                dict(text=f"Total Inmuebles<br><b>{total_val:,.0f}</b>", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=14, color="gray"))
            ],
            height=520,
        )

        # En Streamlit:
        st.plotly_chart(fig_pie, use_container_width=True)

    # ----------------------------
    #       RANKING & KPI
    # ----------------------------
    
    with col3 :     
        # Ordenar de menor a mayor para que las barras horizontales queden ordenadas
        d_rank = d_top.sort_values("consumo_total", ascending=True)

        fig_rank = px.bar(
            d_rank,
            x="consumo_total",
            y="colonia",
            orientation="h",
            color="consumo_total",
            color_continuous_scale="Blues",
            labels={"consumo_total": "Consumo de agua (m³)", "colonia": ""},
            title="Ranking de consumo de agua en las Top 20 colonias"
        )

        fig_rank.update_traces(
            hovertemplate="<b>%{y}</b><br>Consumo: %{x:,.0f} m³<extra></extra>"
        )

        fig_rank.update_layout(
            title_x=0.02,
            margin=dict(t=60, r=20, b=20, l=60),
            coloraxis_showscale=False,  # oculta la barra de color si no la quieres
            height=600
        )

        # En Streamlit:
        st.plotly_chart(fig_rank, use_container_width=True)


        # Calcular consumo total
        total_consumo_top20 = d_top["consumo_total"].sum()


    # --------------------
    # OBSERVATIONS
    # --------------------

    st.markdown("---")
    st.markdown(
        """
        **Observaciones**
        - El Índice de Desarrollo es una construcción estadística mediante
        variables de tipo socioeconómico derivadas de información oficial,
        permite diferenciar territorialmente a la población de la Ciudad de
        México de acuerdo a su nivel de desarrollo económico, agregando 
        la información a nivel manzana. 
        """
    )
    
    
# -----------------------------------------
#    Relación # Inmuebles vs Consumo (m3)
# -----------------------------------------
with tab2 : 
    color_map = {
        "ALTO": "#1f77b4",     # blue
        "MEDIO": "#2ca02c",    # green
        "BAJO": "#ff7f0e",     # orange
        "POPULAR": "#d62728",  # red
    }

    # ensure category is consistent & ordered in legend
    order_idx = ["ALTO", "MEDIO", "BAJO", "POPULAR"]
    allAgg["mayoria_idx"] = (
        allAgg[["ALTO", "BAJO", "MEDIO", "POPULAR"]].idxmax(axis=1).astype("category")
    )
    allAgg["mayoria_idx"] = allAgg["mayoria_idx"].cat.set_categories(order_idx, ordered=True)

    plot_df = allAgg

    # ---- build scatter ----
    fig = px.scatter(
        plot_df,
        x="total_inmuebles",
        y="consumo_total",
        color="mayoria_idx",
        color_discrete_map=color_map,
        category_orders={"mayoria_idx": order_idx},
        hover_data={
            "alcaldia": True,
            "colonia": True,
            "total_inmuebles": ":,",  # thousands format
            "consumo_total": ":,",    # thousands format
            "mayoria_idx": False,     # hidden (already in legend/color)
        },
        labels={
            "total_inmuebles": "Total de inmuebles",
            "consumo_total": "Consumo total de agua (m³)",
            "mayoria_idx": "Índice de desarrollo",
            "alcaldia": "Alcaldía",
            "colonia": "Colonia",
        },
        title="Relación entre total de inmuebles y consumo total de agua por colonia",
        opacity=0.75,
    )

    # marker styling + hovertemplate for clean units
    fig.update_traces(
        marker=dict(size=9, line=dict(width=0.6, color="white")),
        hovertemplate=(
            "<b>%{customdata[1]}</b> — %{customdata[0]}<br>"
            "Inmuebles: %{x:,.0f}<br>"
            "Consumo: %{y:,.0f} m³<extra></extra>"
        ),
    )

    # axes, grid, legend, size
    fig.update_layout(
        title_font_size=18,
        title_x=0.02,
        margin=dict(t=50, r=20, b=20, l=20),
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            ticks="outside",
            title_standoff=8
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=False,
            ticks="outside",
            title_standoff=8
        ),
        legend=dict(
            title="Índice de desarrollo",
            orientation="h",
            yanchor="bottom", y=0.90,
            xanchor="left", x=0
        ),
        hoverlabel=dict(font_size=12),
        uniformtext_minsize=12,
    )

    # --- toggle for OLS trend ---
    show_trend = st.toggle("Mostrar línea de tendencia (OLS)", value=False, key="trend_tab2")

    # trendline (requires statsmodels installed)
    if show_trend:
        # temporary figure with trendline, then merge trace for a clean legend
        fig_trend = px.scatter(
            plot_df,
            x="total_inmuebles",
            y="consumo_total",
            trendline="ols",
            trendline_color_override="grey",
        )
        # the OLS line is usually the second trace
        for tr in fig_trend.data:
            if tr.mode == "lines":
                tr.update(name="Tendencia OLS", showlegend=True)
                fig.add_trace(tr)

    # in Streamlit:
    st.plotly_chart(fig, use_container_width=True)

    # --------------------
    # OBSERVATIONS
    # --------------------

    st.markdown("---")
    st.markdown(
        """
        **Observaciones**
        - Línea de tendencia (método OLS) debe ser utilizada como referencia, 
        aún no se hacen las pruebas estadísticas suficientes para determinar
        si los datos cumplen con normalidad e independencia en los errores,
        homocedasticidad, ect.
        """
    )

# -----------------------------------------
#          ENCUENTRA TU COLONIA
# -----------------------------------------
with tab3 : 
    # ---- Sidebar or top filter ----
    colonias = sorted(habCons["colonia"].dropna().unique())
    colonia_sel = st.selectbox(
        "Selecciona una colonia:",
        options=["(Todas)"] + colonias,
        index=0,
        placeholder="Escribe para buscar…"
    )

    # ---- Filter dataset ----
    if colonia_sel != "(Todas)":
        hab_plot = habCons[habCons["colonia"] == colonia_sel]
    else:
        hab_plot = habCons

    hab_plot["C_PROMVIVC"] = pd.to_numeric(hab_plot["C_PROMVIVC"], errors="coerce").clip(1, 5).fillna(1).astype(int)

    label_map = {
        1: "1 · Muy Bajo",
        2: "2 · Bajo",
        3: "3 · Medio",
        4: "4 · Alto",
        5: "5 · Muy alto"
    }
    hab_plot["C_PROMVIVC_lbl"] = hab_plot["C_PROMVIVC"].map(label_map)

    # Orden fijo en la leyenda
    category_order = ["1 · Muy Bajo", "2 · Bajo", "3 · Medio", "4 · Alto", "5 · Muy alto"]

    # 2) Paleta discreta (inspirada en Viridis, de bajo→alto)
    color_map = {
        "1 · Muy Bajo":"#fde725",  # amarillo
        "2 · Bajo":    "#7ad151",
        "3 · Medio":   "#22a884",
        "4 · Alto"    :"#2a788e",
        "5 · Muy alto":"#440154",  # morado oscuro
    }
    
    color_map = {
        "1 · Muy Bajo": "#80deea",  # aqua claro
        "2 · Bajo":     "#26c6da",  # turquesa medio
        "3 · Medio":    "#00838f",  # teal profundo
        "4 · Alto":     "#004d40",  # verde azulado oscuro
        "5 · Muy alto": "#002633",  # azul marino casi negro
    }

    # 3) Construir el choropleth como categórico (mejor que continuo para 5 clases)
    fig = px.choropleth_mapbox(
        hab_plot,
        geojson=hab_plot.__geo_interface__,         # GeoJSON directo del GeoDataFrame
        locations=hab_plot.index,                   # índice como key
        featureidkey="id",                         # (Plotly usa 'id' por defecto en __geo_interface__)
        color="C_PROMVIVC_lbl",                    # columna categórica
        category_orders={"C_PROMVIVC_lbl": category_order},
        color_discrete_map=color_map,
        hover_name="colonia",
        hover_data={
            "alcaldia": True,
            "SUM_cons_t": ":,",                    # miles
            "C_PROMVIVC_lbl": False,               # ya está por color/leyenda
            "C_PROMVIVC": True                     # muestra la clase numérica base
        },
        mapbox_style="carto-positron",
        zoom=10,
        center={"lat": 19.3333, "lon": -99.1333},
        opacity=0.75,
        labels={
            "SUM_cons_t": "Consumo total (m³)",
            "C_PROMVIVC": "Clase (1–5)"
        },
        title="Consumo de Agua en Ciudad de México — C_PROMVIVC (cuantiles 1–5)"
    )

    # 4) Estilo fino: bordes, leyenda, márgenes
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
        height=700,
        legend=dict(
            title="C_PROMVIVC (1–5)",
            orientation="h",
            yanchor="bottom", y=0.92,
            xanchor="left", x=0
        )
    )

    # Hover limpio
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>"  # hover_name (colonia)
                    "Alcaldía: %{customdata[0]}<br>"
                    "Consumo total: %{customdata[1]:,.0f} m³<br>"
                    "Clase: %{customdata[3]}<extra></extra>"
    )

    # 5) Mostrar en Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # 6) Bloque explicativo (debajo del mapa)
    st.markdown(
        """
        <div style="background-color:#f8f9fa; padding:10px 12px; border-radius:10px; font-size:14px;">
        <b>C_PROMVIVC</b>: campo reclasificado en <i>cuantiles</i> (5 rangos) a partir de <b>PROMVIVCON</b>.<br>
        • Valor <b>5</b> → consumo de agua <b>muy alto</b><br>
        • Valor <b>1</b> → consumo de agua <b>bajo</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("WIP")
    
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
        <a href="https://datos.cdmx.gob.mx/ne/dataset/consumo-agua" target="_blank">
            · SACMEX
        </a>
    </p>
    <p style='color:grey; font-size:15px;margin-bottom:0px;'>
    <a href="https://datos.cdmx.gob.mx/dataset/consumo-habitacional-promedio-bimestral-de-agua-por-colonia-m3" target="_blank">
            · Instituto de Planeación Democrática y Prospectiva
    </a> 
    </p>
    """,
    unsafe_allow_html=True
)