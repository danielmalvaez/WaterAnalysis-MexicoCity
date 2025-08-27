"""
Dashboard: Análisis de la disponibilidad del agua en la Ciudad de México.

Author: Daniel Malváez
"""

from __future__ import annotations

# Standard library imports.
import warnings
import streamlit as st
import pandas as pd

# Configure warnings to keep the output clean.
warnings.filterwarnings("ignore")

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
    st.title("Futuro del Agua en Ciudad de México🚰 🇲🇽")
    
    col1desc, col2desc = st.columns([1, 4])  # adjust ratio for width
    with col1desc:
        st.markdown(
            """
            <p style="margin-bottom:0px;">Version: <i>v0.1.0"</i></p>
            <p style="margin-top:2px; margin-bottom:4px;">Author: <i>Daniel Malváez</i></p>
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
    Este proyecto comenzó con un único objetivo : analizar la situación del
    agua en la Ciudad de México para poder tomar una decisión más informada 
    sobre donde rentar/comprar una vivienda en la ciudad. La motivación surge 
    de preocupaciones personales respecto al contexto actual del abastecimiento 
    de agua en la capital.
    
    Sin embargo, conforme fui realizando el análisis, descubrí que el dashboard 
    también tiene otro objetivo. Más allá de ser una herramienta informativa, 
    también se converte en una fuente de información que muestra cómo, con el 
    paso de los años, la incertidumbre sobre la disponibilidad de agua se ha 
    vuelto un tema cada vez más relevante.
    """
    )
    
    st.write("## Breve Historia de la Ciudad de México")            
    st.markdown(
    """
    La Ciudad de México fue fundada como un asentamiento lacustre en un pequeño
    islote, con registro en 1325. El mito dice que Huitzilopochtli profetizó
    a los aztecas o mexicas, durante su migración desde Aztlán y que debían
    buscar en un lago un águila posada sobre un nopal con una serpiente entre
    sus garras. Luego de un arduo recorrido (de aproximadamente 210 años) 
    llegaron a lo que se conocía como el Lago de Texcoco, que es donde se 
    fundó la ciudad de Tenochtitlán (actualmente la Ciudad de México) en 1325. 
    
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