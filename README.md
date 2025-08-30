# 💧 Escasez de Agua en CDMX 🏙️
*Impacto en decisiones al rentar o adquirir una propiedad*

----

## ✨ Motivación

Este proyecto nació como una petición personal de mis padres. Nos dimos cuenta 
que cada vez que buscábamos rentar o mudarnos de casa, además de considerar:
* Entorno social 🧑‍🤝‍🧑
* Seguridad 🛡️
* Cercanía a servicios 🏥🛒
* Proximidad con familia 👨‍👩‍👧‍👦

siempre surgía la pregunta: ¿cómo está el abastecimiento de agua en la colonia? 🚰
* tandeos
* cisterna
* tinaco

Con el objetivo de tener mayor visibilidad sobre este problema en Ciudad de México, desarrollé este proyecto para:
* Brindar una herramienta de apoyo 🧰 en cuanto a la disponibilidad de agua
port colonia.
* Permitir decisiones más informadas 📊 y preveer sobre el impacto de agua a 
futuro.
* Generar conciencia sobre el uso responsable del agua 🌎.


## 📊 Dashboard

🔗 Acceder al (Dashboard)[https://water-analysis-mexico-city.streamlit.app/]
📖 Descrito en detalle en este (artículo)[tbd] en Medium.

El dashboard permite:
* Explorar mapas interactivos de la disponibilidad y consumo de agua.
* Visualizar la factibilidad hídrica por colonia.
* Encontrar tu colonia y ver su situación de agua.

## ⚙️ Instalación Local

Clona este repositorio e instala las dependencias:

```python
git clone https://github.com/usuario/repo.git
cd repo
pip install -r requirements.txt
```

Ejecuta el dashboard en Streamlit:

```python
streamlit run app.py
```

## 📚 Fuentes de Datos
* Dataset limpio (Hugging Face): (Water Dashboard Dataset)[https://huggingface.co/datasets/danielmlvz/water-dashboard]
* Instituciones: CONAGUA, INEGI, SEDUVI, IPDP (2023).
* https://cuentame.inegi.org.mx/descubre/conoce_tu_estado/tarjeta.html?estado=09
* https://www.gob.mx/bancodelbienestar/articulos/693-aniversario-de-la-fundacion-de-mexico-tenochtitlan?idiom=es#:~:text=Sobre%20la%20fecha%20precisa%20de,que%20sucedi%C3%B3%20en%20el%201325.
* https://autoridadcentrohistorico.cdmx.gob.mx/centro-historico-de-la-ciudad-de-mexico/conoce-tu-centro-historico
* https://historico.datos.gob.mx/busca/dataset/municipios-con-sequia
* https://datos.cdmx.gob.mx/ne/dataset/consumo-agua
* https://datos.cdmx.gob.mx/dataset/consumo-habitacional-promedio-bimestral-de-agua-por-colonia-m3
* https://datos.cdmx.gob.mx/dataset/alta-concentracion-vivienda-cdmx
* https://datos.cdmx.gob.mx/sv/dataset/reportes-de-agua

## Links útiles:
* https://periodicocorreo.com.mx/nacional/2025/jul/01/sistema-cutzamala-supera-minimos-historicos-y-sale-de-crisis-hidrica-tras-intensas-lluvias-131693.html
* https://www.smithsonianmag.com/smart-news/mexico-citys-reservoirs-are-at-risk-of-running-out-of-water-180984433/?utm_source=chatgpt.com
* https://www.reuters.com/sustainability/boards-policy-regulation/mexicos-water-deficit-persists-even-after-torrential-summer-rains-2025-07-03/?utm_source=chatgpt.com
* https://www.economia.gob.mx/datamexico/es/profile/geo/ciudad-de-mexico-cx?redirect=true&yearCensus1=year2019
* https://www.economia.gob.mx/datamexico/es/profile/industry/real-estate-and-rental-and-leasing?yearEconomicCensus=option1&yearSelectorGdp=timeOption0#environment
* https://www.economia.gob.mx/datamexico/es/profile/industry/construction

## 🚀 Roadmap
* Agregar análisis predictivo de riesgo hídrico.
* Integrar precios de renta/venta en tiempo real.
* Extender dataset a otras ciudades mexicanas.
* Desplegar versión pública en Streamlit Cloud.

## 📂 Estructura del Repositorio

```python
.
├── data/                # Datasets brutos y procesados
├── notebooks/           # Jupyter notebooks de análisis exploratorio
├── src/                 # Código principal para ETL y visualizaciones
├── app.py               # Dashboard en Streamlit
├── requirements.txt     # Dependencias
└── README.md            # Este documento
```

## 🛡️ Licencia

Este proyecto está bajo la licencia MIT.