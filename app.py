"""
=============================================================================
DASHBOARD - COLOMBIANOS EN EL EXTERIOR: ANÁLISIS DE FUGA DE CEREBROS
=============================================================================
Aplicación Streamlit con visualizaciones interactivas sobre el fenómeno
migratorio colombiano, organizada en 4 ejes temáticos.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Colombianos en el Exterior - Fuga de Cerebros",
    page_icon="🇨🇴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CARGA DE DATOS
# ============================================================================
@st.cache_data
def cargar_datos():
    """Carga los datos limpios generados por el preprocesamiento."""
    data_path = "data/datos_limpios.csv"
    if not os.path.exists(data_path):
        st.error("⚠️ No se encontró el archivo de datos limpios. Ejecuta primero: python preprocessing.py")
        st.stop()
    df = pd.read_csv(data_path, low_memory=False)
    return df

df = cargar_datos()

# ============================================================================
# SIDEBAR - NAVEGACIÓN
# ============================================================================
st.sidebar.title("🇨🇴 Navegación")
st.sidebar.markdown("---")

eje = st.sidebar.radio(
    "Selecciona un eje temático:",
    [
        "🏠 Inicio",
        "🎓 Eje 1: Fuga de Cerebros",
        "👥 Eje 2: Demografía y Dinámicas Sociales",
        "🏛️ Eje 3: Servicios Consulares",
        "🗺️ Eje 4: Rutas Migratorias y Tiempo"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Total registros:** {len(df):,}")
st.sidebar.markdown(f"**Países destino:** {df['pais'].nunique()}")
st.sidebar.markdown(f"**Fuente:** datos.gov.co")


# ============================================================================
# PÁGINA DE INICIO
# ============================================================================
if eje == "🏠 Inicio":
    st.title("🇨🇴 Colombianos en el Exterior")
    st.subheader("Análisis Exploratorio del Fenómeno Migratorio y la Fuga de Cerebros")

    st.markdown("""
    Este dashboard analiza los datos del **Registro Ciudadano en Línea** del Ministerio de 
    Relaciones Exteriores de Colombia, con enfoque en la **fuga de cerebros** y las dinámicas 
    migratorias de los colombianos en el exterior.

    ### 📊 Ejes de Análisis

    | Eje | Enfoque | Preguntas |
    |-----|---------|-----------|
    | 🎓 Fuga de Cerebros | Talento altamente calificado | 4 visualizaciones |
    | 👥 Demografía | Perfil del migrante | 4 visualizaciones |
    | 🏛️ Consulados | Servicios y cobertura | 3 visualizaciones |
    | 🗺️ Rutas y Tiempo | Flujos migratorios | 4 visualizaciones |
    """)

    # KPIs principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total = len(df)
        st.metric("Total Migrantes", f"{total:,}")
    with col2:
        posgrado = df[df["nivel_academico_agrupado"] == "Posgrado"].shape[0]
        st.metric("Con Posgrado", f"{posgrado:,}")
    with col3:
        paises = df["pais"].nunique()
        st.metric("Países Destino", f"{paises}")
    with col4:
        edad_prom = df["edad"].mean()
        st.metric("Edad Promedio", f"{edad_prom:.0f} años")

    # Perfil promedio
    st.markdown("---")
    st.subheader("📋 Perfil Promedio del Migrante Colombiano")

    col1, col2, col3 = st.columns(3)
    with col1:
        sexo_moda = df["sexo"].mode().iloc[0] if df["sexo"].notna().any() else "N/A"
        st.info(f"**Sexo predominante:** {sexo_moda}")
        estado_moda = df["estado_civil"].mode().iloc[0] if df["estado_civil"].notna().any() else "N/A"
        st.info(f"**Estado civil más común:** {estado_moda}")
    with col2:
        pais_top = df["pais"].mode().iloc[0] if df["pais"].notna().any() else "N/A"
        st.info(f"**País destino #1:** {pais_top}")
        nivel_moda = df["nivel_academico"].mode().iloc[0] if df["nivel_academico"].notna().any() else "N/A"
        st.info(f"**Nivel académico más común:** {nivel_moda}")
    with col3:
        area_top = df[df["area_conocimiento"].notna()]["area_conocimiento"].mode()
        area_moda = area_top.iloc[0] if len(area_top) > 0 else "N/A"
        st.info(f"**Área de conocimiento #1:** {area_moda}")
        edad_mediana = df["edad"].median()
        st.info(f"**Edad mediana:** {edad_mediana:.0f} años")


# ============================================================================
# EJE 1: FUGA DE CEREBROS
# ============================================================================
elif eje == "🎓 Eje 1: Fuga de Cerebros":
    st.title("🎓 Eje 1: Fuga de Cerebros")
    st.markdown("Análisis del talento altamente calificado que emigra de Colombia.")

    # ------------------------------------------------------------------
    # PREGUNTA 1.1: Países destino del talento más calificado
    # ------------------------------------------------------------------
    st.header("1.1 ¿A qué países se va el talento más calificado?")
    st.markdown("Filtrado por personas con **Maestría** y **Doctorado**.")

    df_alta = df[df["nivel_academico"].isin(["MAESTRÍA", "DOCTORADO"])]

    if not df_alta.empty:
        pais_alta = df_alta.groupby(["pais", "codigo_iso_pais"]).size().reset_index(name="cantidad")
        pais_alta = pais_alta.sort_values("cantidad", ascending=False)

        # Mapa coroplético
        fig_mapa = px.choropleth(
            pais_alta,
            locations="codigo_iso_pais",
            color="cantidad",
            hover_name="pais",
            color_continuous_scale="YlOrRd",
            title="Distribución Global del Talento Altamente Calificado (Maestría + Doctorado)",
            labels={"cantidad": "Personas", "codigo_iso_pais": "ISO"},
        )
        fig_mapa.update_layout(height=500, geo=dict(showframe=False))
        st.plotly_chart(fig_mapa, use_container_width=True)

        # Top 15 países
        st.subheader("Top 15 países destino")
        fig_bar = px.bar(
            pais_alta.head(15),
            x="cantidad",
            y="pais",
            orientation="h",
            color="cantidad",
            color_continuous_scale="YlOrRd",
            title="Top 15 Países con Mayor Recepción de Talento Calificado",
        )
        fig_bar.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No hay datos de Maestría/Doctorado disponibles.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 1.2: Áreas de conocimiento y regiones destino
    # ------------------------------------------------------------------
    st.header("1.2 ¿Cuáles áreas de conocimiento migran más y hacia dónde?")

    df_con_area = df[df["area_conocimiento"].notna() & df["continente"].notna()]

    if not df_con_area.empty:
        # Top 10 áreas
        top_areas = df_con_area["area_conocimiento"].value_counts().head(10).index.tolist()
        df_areas = df_con_area[df_con_area["area_conocimiento"].isin(top_areas)]

        area_cont = df_areas.groupby(["area_conocimiento", "continente"]).size().reset_index(name="cantidad")

        fig_barras = px.bar(
            area_cont,
            y="area_conocimiento",
            x="cantidad",
            color="continente",
            orientation="h",
            title="Áreas de Conocimiento por Continente de Destino",
            labels={"cantidad": "Personas", "area_conocimiento": "Área", "continente": "Continente"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_barras.update_layout(height=600, barmode="stack")
        st.plotly_chart(fig_barras, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para esta visualización.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 1.3: Relación edad vs nivel académico
    # ------------------------------------------------------------------
    st.header("1.3 ¿Existe relación entre edad y nivel académico al migrar?")

    df_edad_nivel = df[df["edad"].notna() & df["nivel_academico"].notna()].copy()

    if not df_edad_nivel.empty:
        # Agrupar para scatter con burbujas
        scatter_data = df_edad_nivel.groupby(["rango_edad", "nivel_academico"]).size().reset_index(name="cantidad")

        fig_scatter = px.scatter(
            scatter_data,
            x="rango_edad",
            y="nivel_academico",
            size="cantidad",
            color="nivel_academico",
            title="Relación Edad vs Nivel Académico (tamaño = cantidad de personas)",
            labels={"rango_edad": "Rango de Edad", "nivel_academico": "Nivel Académico", "cantidad": "Personas"},
            size_max=60,
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para esta visualización.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 1.4: Proporción educación básica y destinos
    # ------------------------------------------------------------------
    st.header("1.4 ¿Qué proporción tiene solo educación básica y dónde residen?")

    niveles_basicos = ["PRIMARIA", "BACHILLERATO"]
    df_basica = df[df["nivel_academico"].isin(niveles_basicos)]
    df_no_basica = df[~df["nivel_academico"].isin(niveles_basicos) & df["nivel_academico"].notna()]

    col1, col2 = st.columns(2)

    with col1:
        # Donut chart
        labels_donut = ["Educación Básica", "Otros niveles"]
        values_donut = [len(df_basica), len(df_no_basica)]

        fig_donut = go.Figure(data=[go.Pie(
            labels=labels_donut,
            values=values_donut,
            hole=0.5,
            marker_colors=["#FF6B6B", "#4ECDC4"]
        )])
        fig_donut.update_layout(
            title="Proporción de Migrantes con Educación Básica",
            height=400
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        # Barras horizontales - destinos de educación básica
        if not df_basica.empty:
            destinos_basica = df_basica["pais"].value_counts().head(15).reset_index()
            destinos_basica.columns = ["pais", "cantidad"]

            fig_dest = px.bar(
                destinos_basica,
                x="cantidad",
                y="pais",
                orientation="h",
                title="Top 15 Destinos - Educación Básica",
                color="cantidad",
                color_continuous_scale="Teal",
            )
            fig_dest.update_layout(height=400, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_dest, use_container_width=True)


# ============================================================================
# EJE 2: DEMOGRAFÍA Y DINÁMICAS SOCIALES
# ============================================================================
elif eje == "👥 Eje 2: Demografía y Dinámicas Sociales":
    st.title("👥 Eje 2: Demografía y Dinámicas Sociales")
    st.markdown("Análisis de quiénes son los colombianos en el exterior.")

    # ------------------------------------------------------------------
    # PREGUNTA 2.1: Destinos por género
    # ------------------------------------------------------------------
    st.header("2.1 ¿Hay destinos preferidos por mujeres vs hombres?")

    df_genero = df[df["sexo"].isin(["FEMENINO", "MASCULINO"])]

    if not df_genero.empty:
        top_paises = df_genero["pais"].value_counts().head(15).index.tolist()
        df_gen_pais = df_genero[df_genero["pais"].isin(top_paises)]

        gen_pais = df_gen_pais.groupby(["pais", "sexo"]).size().reset_index(name="cantidad")

        fig_gen = px.bar(
            gen_pais,
            x="pais",
            y="cantidad",
            color="sexo",
            barmode="group",
            title="Distribución por Género en los Top 15 Países Destino",
            labels={"pais": "País", "cantidad": "Personas", "sexo": "Sexo"},
            color_discrete_map={"FEMENINO": "#E91E63", "MASCULINO": "#2196F3"},
        )
        fig_gen.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_gen, use_container_width=True)

        # Ratio F/M
        st.subheader("Ratio Femenino/Masculino por país")
        pivot_gen = gen_pais.pivot(index="pais", columns="sexo", values="cantidad").fillna(0)
        if "FEMENINO" in pivot_gen.columns and "MASCULINO" in pivot_gen.columns:
            pivot_gen["ratio_FM"] = pivot_gen["FEMENINO"] / pivot_gen["MASCULINO"].replace(0, 1)
            pivot_gen = pivot_gen.sort_values("ratio_FM", ascending=False).reset_index()

            fig_ratio = px.bar(
                pivot_gen,
                x="ratio_FM",
                y="pais",
                orientation="h",
                title="Ratio Mujeres/Hombres por País (>1 = más mujeres)",
                color="ratio_FM",
                color_continuous_scale="RdBu",
                color_continuous_midpoint=1,
            )
            fig_ratio.update_layout(height=500, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_ratio, use_container_width=True)
    else:
        st.warning("No hay datos de género disponibles.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 2.2: Estado civil por edad y sexo
    # ------------------------------------------------------------------
    st.header("2.2 ¿Cómo se distribuye el estado civil según edad y sexo?")

    df_civil = df[df["estado_civil"].notna() & df["rango_edad"].notna()]

    if not df_civil.empty:
        civil_edad = df_civil.groupby(["rango_edad", "estado_civil"]).size().reset_index(name="cantidad")

        # Calcular porcentajes
        total_por_rango = civil_edad.groupby("rango_edad")["cantidad"].transform("sum")
        civil_edad["porcentaje"] = civil_edad["cantidad"] / total_por_rango * 100

        fig_civil = px.bar(
            civil_edad,
            x="rango_edad",
            y="porcentaje",
            color="estado_civil",
            title="Distribución del Estado Civil por Rango de Edad (100% apilado)",
            labels={"rango_edad": "Rango de Edad", "porcentaje": "Porcentaje (%)", "estado_civil": "Estado Civil"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_civil.update_layout(height=500, barmode="stack")
        st.plotly_chart(fig_civil, use_container_width=True)
    else:
        st.warning("No hay datos suficientes.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 2.3: Grupos étnicos y ciudades
    # ------------------------------------------------------------------
    st.header("2.3 ¿Qué grupos étnicos tienen mayor representación?")

    df_etnia = df[df["etnia"].notna()]

    if not df_etnia.empty:
        # Treemap: etnia → ciudad de residencia
        etnia_ciudad = df_etnia.groupby(["etnia", "pais"]).size().reset_index(name="cantidad")
        etnia_ciudad = etnia_ciudad.sort_values("cantidad", ascending=False)

        # Top combinaciones para treemap
        top_etnias = df_etnia["etnia"].value_counts().head(6).index.tolist()
        df_tree = etnia_ciudad[etnia_ciudad["etnia"].isin(top_etnias)]

        # Top 5 países por etnia
        df_tree_top = df_tree.groupby("etnia").apply(
            lambda x: x.nlargest(5, "cantidad"), include_groups=False
        ).reset_index(drop=True)

        if not df_tree_top.empty:
            fig_tree = px.treemap(
                df_tree_top,
                path=["etnia", "pais"],
                values="cantidad",
                title="Grupos Étnicos y sus Principales Países de Residencia",
                color="cantidad",
                color_continuous_scale="Viridis",
            )
            fig_tree.update_layout(height=600)
            st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.warning("No hay datos de etnia disponibles.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 2.4: Perfil promedio
    # ------------------------------------------------------------------
    st.header("2.4 Perfil Promedio del Migrante Colombiano")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        edad_prom = df["edad"].mean()
        st.metric("📅 Edad Promedio", f"{edad_prom:.0f} años")
    with col2:
        sexo_top = df["sexo"].mode().iloc[0] if df["sexo"].notna().any() else "N/A"
        st.metric("👤 Sexo Predominante", sexo_top)
    with col3:
        civil_top = df["estado_civil"].mode().iloc[0] if df["estado_civil"].notna().any() else "N/A"
        st.metric("💍 Estado Civil", civil_top)
    with col4:
        nivel_top = df["nivel_academico"].mode().iloc[0] if df["nivel_academico"].notna().any() else "N/A"
        st.metric("🎓 Nivel Académico", nivel_top)

    # Narrativa automática
    st.markdown("---")
    pais_1 = df["pais"].mode().iloc[0] if df["pais"].notna().any() else "desconocido"
    area_1 = df[df["area_conocimiento"].notna()]["area_conocimiento"].mode()
    area_txt = area_1.iloc[0] if len(area_1) > 0 else "no especificada"

    st.info(f"""
    **📝 Narrativa Resumen:**  
    El migrante colombiano promedio tiene **{edad_prom:.0f} años**, es de sexo **{sexo_top.lower()}**, 
    con estado civil **{civil_top.lower()}**. Su nivel académico más frecuente es **{nivel_top.lower()}** 
    y su área de conocimiento predominante es **{area_txt.lower()}**. 
    El destino más popular es **{pais_1}**.
    """)


# ============================================================================
# EJE 3: OPTIMIZACIÓN DE SERVICIOS Y CONSULADOS
# ============================================================================
elif eje == "🏛️ Eje 3: Servicios Consulares":
    st.title("🏛️ Eje 3: Optimización de Servicios y Consulados")
    st.markdown("Análisis operativo de la cobertura consular colombiana.")

    # ------------------------------------------------------------------
    # PREGUNTA 3.1: Consulados con mayor carga
    # ------------------------------------------------------------------
    st.header("3.1 ¿Cuáles consulados tienen mayor carga poblacional?")

    df_consul = df[df["oficina_consular"].notna()]

    if not df_consul.empty:
        carga_consul = df_consul["oficina_consular"].value_counts().head(25).reset_index()
        carga_consul.columns = ["consulado", "personas"]

        fig_funnel = px.funnel(
            carga_consul.head(15),
            x="personas",
            y="consulado",
            title="Top 15 Oficinas Consulares por Carga Poblacional",
            color="personas",
            color_continuous_scale="Reds",
        )
        fig_funnel.update_layout(height=600)
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Tabla completa
        with st.expander("Ver tabla completa (Top 25)"):
            st.dataframe(carga_consul, use_container_width=True)
    else:
        st.warning("No hay datos de oficinas consulares.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 3.2: Ciudades vs oficinas consulares
    # ------------------------------------------------------------------
    st.header("3.2 ¿Hay ciudades con alta densidad que dependen de consulados lejanos?")

    if "ciudad_residencia_limpia" in df.columns and "oficina_consular" in df.columns:
        df_mapa = df[df["ciudad_residencia_limpia"].notna() & df["oficina_consular"].notna()]

        # Top ciudades de residencia
        top_ciudades = df_mapa["ciudad_residencia_limpia"].value_counts().head(20).reset_index()
        top_ciudades.columns = ["ciudad", "personas"]

        # Consulado asignado a cada ciudad
        ciudad_consul = df_mapa.groupby("ciudad_residencia_limpia")["oficina_consular"].agg(
            lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "N/A"
        ).reset_index()
        ciudad_consul.columns = ["ciudad", "consulado_asignado"]

        merged = top_ciudades.merge(ciudad_consul, on="ciudad", how="left")

        fig_bubble = px.scatter(
            merged,
            x="ciudad",
            y="consulado_asignado",
            size="personas",
            color="personas",
            title="Ciudades de Residencia vs Consulado Asignado (tamaño = población)",
            labels={"ciudad": "Ciudad de Residencia", "consulado_asignado": "Consulado"},
            color_continuous_scale="Turbo",
            size_max=50,
        )
        fig_bubble.update_layout(height=600, xaxis_tickangle=-45)
        st.plotly_chart(fig_bubble, use_container_width=True)
    else:
        st.warning("No hay datos geográficos suficientes.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 3.3: Migrantes en edad de pensión
    # ------------------------------------------------------------------
    st.header("3.3 ¿Cuántos migrantes están en edad de pensión (>60 años)?")

    df_edad_valid = df[df["edad"].notna()]
    total_con_edad = len(df_edad_valid)
    mayores_60 = df_edad_valid[df_edad_valid["edad"] >= 60]
    n_mayores = len(mayores_60)
    pct_mayores = (n_mayores / total_con_edad * 100) if total_con_edad > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("👴 Adultos Mayores (60+)", f"{n_mayores:,}")
    with col2:
        st.metric("📊 Porcentaje del Total", f"{pct_mayores:.1f}%")
    with col3:
        st.metric("🎯 Total con Edad Registrada", f"{total_con_edad:,}")

    # Gauge chart
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct_mayores,
        title={"text": "Porcentaje de Adultos Mayores (60+)"},
        delta={"reference": 15, "suffix": "%"},
        gauge={
            "axis": {"range": [0, 30]},
            "bar": {"color": "#FF6B6B"},
            "steps": [
                {"range": [0, 10], "color": "#E8F5E9"},
                {"range": [10, 20], "color": "#FFF3E0"},
                {"range": [20, 30], "color": "#FFEBEE"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 15,
            },
        },
    ))
    fig_gauge.update_layout(height=350)
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Distribución por país
    if not mayores_60.empty:
        paises_mayores = mayores_60["pais"].value_counts().head(10).reset_index()
        paises_mayores.columns = ["pais", "cantidad"]

        fig_may = px.bar(
            paises_mayores,
            x="cantidad",
            y="pais",
            orientation="h",
            title="Top 10 Países con Mayor Población de Adultos Mayores Colombianos",
            color="cantidad",
            color_continuous_scale="Oranges",
        )
        fig_may.update_layout(height=400, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_may, use_container_width=True)


# ============================================================================
# EJE 4: RUTAS MIGRATORIAS Y TIEMPO
# ============================================================================
elif eje == "🗺️ Eje 4: Rutas Migratorias y Tiempo":
    st.title("🗺️ Eje 4: Rutas Migratorias y Tiempo")
    st.markdown("Análisis de flujos migratorios y comportamiento temporal.")

    # ------------------------------------------------------------------
    # PREGUNTA 4.1: Ciudades de origen → Países destino (Sankey)
    # ------------------------------------------------------------------
    st.header("4.1 ¿De qué ciudades de Colombia provienen y a dónde llegan?")

    if "depto_nacimiento" in df.columns:
        df_sankey = df[df["depto_nacimiento"].notna() & df["pais"].notna()]

        # Top 10 departamentos y top 8 países
        top_deptos = df_sankey["depto_nacimiento"].value_counts().head(10).index.tolist()
        top_paises = df_sankey["pais"].value_counts().head(8).index.tolist()

        df_sankey_f = df_sankey[
            df_sankey["depto_nacimiento"].isin(top_deptos) &
            df_sankey["pais"].isin(top_paises)
        ]

        flujos = df_sankey_f.groupby(["depto_nacimiento", "pais"]).size().reset_index(name="cantidad")
        flujos = flujos[flujos["cantidad"] > 100]  # Filtrar flujos pequeños

        if not flujos.empty:
            # Crear nodos
            all_nodes = list(set(flujos["depto_nacimiento"].tolist() + flujos["pais"].tolist()))
            node_indices = {node: i for i, node in enumerate(all_nodes)}

            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=all_nodes,
                    color=["#2196F3" if n in top_deptos else "#FF9800" for n in all_nodes]
                ),
                link=dict(
                    source=[node_indices[d] for d in flujos["depto_nacimiento"]],
                    target=[node_indices[p] for p in flujos["pais"]],
                    value=flujos["cantidad"].tolist(),
                    color="rgba(100,100,100,0.2)"
                )
            )])
            fig_sankey.update_layout(
                title="Flujos Migratorios: Departamento de Origen → País Destino",
                height=600
            )
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.warning("No hay flujos significativos para mostrar.")
    else:
        st.warning("No hay datos de ciudad de nacimiento.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 4.2: Evolución temporal de registros
    # ------------------------------------------------------------------
    st.header("4.2 ¿Cómo ha evolucionado la cantidad de registros en el tiempo?")

    if "anio_registro" in df.columns:
        df_tiempo = df[df["anio_registro"].notna()].copy()
        df_tiempo["anio_registro"] = df_tiempo["anio_registro"].astype(int)

        evolucion = df_tiempo.groupby("anio_registro").size().reset_index(name="registros")
        evolucion = evolucion[evolucion["anio_registro"] >= 2005]

        fig_linea = px.area(
            evolucion,
            x="anio_registro",
            y="registros",
            title="Evolución Anual de Registros de Colombianos en el Exterior",
            labels={"anio_registro": "Año", "registros": "Registros"},
            color_discrete_sequence=["#1976D2"],
        )
        fig_linea.update_layout(height=400)
        st.plotly_chart(fig_linea, use_container_width=True)

        # Por mes (último año disponible)
        ultimo_anio = df_tiempo["anio_registro"].max()
        df_ultimo = df_tiempo[df_tiempo["anio_registro"] == ultimo_anio]

        if "mes_registro" in df_ultimo.columns:
            mensual = df_ultimo.groupby("mes_registro").size().reset_index(name="registros")
            fig_mes = px.bar(
                mensual,
                x="mes_registro",
                y="registros",
                title=f"Registros Mensuales en {ultimo_anio}",
                labels={"mes_registro": "Mes", "registros": "Registros"},
                color="registros",
                color_continuous_scale="Blues",
            )
            fig_mes.update_layout(height=350)
            st.plotly_chart(fig_mes, use_container_width=True)
    else:
        st.warning("No hay datos de fecha de registro.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 4.3: Picos estacionales por área de conocimiento
    # ------------------------------------------------------------------
    st.header("4.3 ¿Existen picos estacionales en la salida de profesionales?")

    if "anio_registro" in df.columns and "area_conocimiento" in df.columns:
        df_estacional = df[
            df["anio_registro"].notna() &
            df["area_conocimiento"].notna()
        ].copy()
        df_estacional["anio_registro"] = df_estacional["anio_registro"].astype(int)

        # Top 5 áreas de conocimiento
        top_5_areas = df_estacional["area_conocimiento"].value_counts().head(5).index.tolist()
        df_est_f = df_estacional[
            df_estacional["area_conocimiento"].isin(top_5_areas) &
            (df_estacional["anio_registro"] >= 2010)
        ]

        area_anio = df_est_f.groupby(["anio_registro", "area_conocimiento"]).size().reset_index(name="cantidad")

        fig_areas_t = px.area(
            area_anio,
            x="anio_registro",
            y="cantidad",
            color="area_conocimiento",
            title="Evolución Temporal por Área de Conocimiento (Top 5)",
            labels={"anio_registro": "Año", "cantidad": "Registros", "area_conocimiento": "Área"},
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        fig_areas_t.update_layout(height=500)
        st.plotly_chart(fig_areas_t, use_container_width=True)
    else:
        st.warning("No hay datos suficientes.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PREGUNTA 4.4: Preferencias regionales (Costa vs Interior)
    # ------------------------------------------------------------------
    st.header("4.4 ¿Las regiones de Colombia tienen preferencias distintas de destino?")

    if "depto_nacimiento" in df.columns:
        # Clasificar departamentos en regiones
        costa = ["ATLANTICO", "BOLIVAR", "CESAR", "CORDOBA", "LA GUAJIRA",
                 "MAGDALENA", "SUCRE", "SAN ANDRES"]
        interior = ["CUNDINAMARCA", "BOYACA", "SANTANDER", "NORTE DE SANTANDER",
                    "TOLIMA", "HUILA", "META"]
        eje_cafetero = ["ANTIOQUIA", "CALDAS", "RISARALDA", "QUINDIO"]
        pacifico = ["VALLE DEL CAUCA", "CAUCA", "NARINO", "CHOCO"]

        def clasificar_region(depto):
            if depto in costa:
                return "Costa Caribe"
            elif depto in interior:
                return "Interior/Andina"
            elif depto in eje_cafetero:
                return "Eje Cafetero"
            elif depto in pacifico:
                return "Pacífico"
            else:
                return "Otra"

        df_reg = df[df["depto_nacimiento"].notna()].copy()
        df_reg["region_origen"] = df_reg["depto_nacimiento"].apply(clasificar_region)
        df_reg = df_reg[df_reg["region_origen"] != "Otra"]

        # Top 8 países
        top_paises_r = df_reg["pais"].value_counts().head(8).index.tolist()
        df_reg_f = df_reg[df_reg["pais"].isin(top_paises_r)]

        matriz = df_reg_f.groupby(["region_origen", "pais"]).size().reset_index(name="cantidad")

        # Crear tabla pivote para el heatmap
        pivot = matriz.pivot_table(index="region_origen", columns="pais", values="cantidad", aggfunc="sum").fillna(0)

        # Heatmap con go.Heatmap (datos pre-agregados)
        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale="YlOrRd",
            text=pivot.values.astype(int),
            texttemplate="%{text:,}",
            hovertemplate="Región: %{y}<br>País: %{x}<br>Personas: %{z:,}<extra></extra>",
        ))
        fig_heat.update_layout(
            title="Preferencias de Destino por Región de Origen",
            xaxis_title="País Destino",
            yaxis_title="Región de Origen",
            height=450,
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Tabla cruzada
        with st.expander("Ver tabla cruzada completa"):
            pivot_display = pivot.astype(int)
            st.dataframe(pivot_display.style.background_gradient(cmap="YlOrRd", axis=None), use_container_width=True)
    else:
        st.warning("No hay datos de departamento de nacimiento.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    📊 Dashboard de Visualización de Datos | Colombianos en el Exterior<br>
    Fuente: Ministerio de Relaciones Exteriores - datos.gov.co<br>
    Dataset: Connacionales inscritos en el Registro Ciudadano en Línea (y399-rzwf)
</div>
""", unsafe_allow_html=True)
