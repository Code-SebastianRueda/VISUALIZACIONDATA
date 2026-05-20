"""
=============================================================================
PREPROCESAMIENTO DE DATOS - COLOMBIANOS EN EL EXTERIOR
=============================================================================
Fuente: Ministerio de Relaciones Exteriores - datos.gov.co
Dataset: Connacionales inscritos en el Registro Ciudadano en Línea (y399-rzwf)

Objetivo: Limpiar y transformar los datos crudos para generar un archivo de
data limpia que alimente las visualizaciones del dashboard de análisis
migratorio colombiano (fuga de cerebros).

Cambios realizados:
1. Descarga de datos via API SODA (Socrata Open Data API)
2. Renombrado de columnas a nombres legibles en español
3. Limpieza de valores nulos/no registrados
4. Normalización de categorías de Nivel Académico
5. Creación de rangos de edad
6. Extracción de departamento/ciudad desde campos compuestos
7. Mapeo de países a continentes
8. Conversión de fecha de registro a formato datetime
9. Eliminación de columnas vacías/irrelevantes
10. Exportación a CSV limpio
=============================================================================
"""

import pandas as pd
import numpy as np
import os
import requests
import time

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
DATA_DIR = "data"
RAW_FILE = os.path.join(DATA_DIR, "datos_crudos.csv")
CLEAN_FILE = os.path.join(DATA_DIR, "datos_limpios.csv")

# API Socrata - Dataset principal
DATASET_ID = "y399-rzwf"
BASE_URL = f"https://www.datos.gov.co/resource/{DATASET_ID}.csv"
LIMIT = 50000  # Registros por solicitud

# ============================================================================
# 1. DESCARGA DE DATOS
# ============================================================================
def descargar_datos():
    """
    Descarga los datos desde la API de datos.gov.co usando paginación.
    El dataset tiene ~1.8M registros, se descargan en bloques de 50,000.
    """
    print("=" * 60)
    print("PASO 1: DESCARGA DE DATOS DESDE datos.gov.co")
    print("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)

    # Si ya existe el archivo crudo, no volver a descargar
    if os.path.exists(RAW_FILE):
        print(f"  → Archivo crudo ya existe: {RAW_FILE}")
        print(f"  → Cargando datos existentes...")
        df = pd.read_csv(RAW_FILE, low_memory=False)
        print(f"  → Registros cargados: {len(df):,}")
        return df

    print(f"  → Descargando desde: {BASE_URL}")
    print(f"  → Bloques de {LIMIT:,} registros...")

    all_data = []
    offset = 0
    batch = 1

    while True:
        url = f"{BASE_URL}?$limit={LIMIT}&$offset={offset}&$order=:id"
        print(f"    Bloque {batch}: offset={offset:,}...", end=" ")

        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"\n  ⚠ Error en descarga: {e}")
            print(f"  → Reintentando en 5 segundos...")
            time.sleep(5)
            continue

        # Leer el bloque como DataFrame
        from io import StringIO
        chunk = pd.read_csv(StringIO(response.text), low_memory=False)

        if chunk.empty:
            print("vacío → Descarga completa.")
            break

        all_data.append(chunk)
        print(f"OK ({len(chunk):,} registros)")

        offset += LIMIT
        batch += 1
        time.sleep(0.5)  # Respetar rate limits

    if not all_data:
        raise RuntimeError("No se pudieron descargar datos.")

    df = pd.concat(all_data, ignore_index=True)
    print(f"\n  → Total registros descargados: {len(df):,}")

    # Guardar datos crudos
    df.to_csv(RAW_FILE, index=False)
    print(f"  → Guardado en: {RAW_FILE}")

    return df


# ============================================================================
# 2. RENOMBRADO DE COLUMNAS
# ============================================================================
def renombrar_columnas(df):
    """
    Renombra las columnas de la API (nombres técnicos) a nombres legibles.
    """
    print("\n" + "=" * 60)
    print("PASO 2: RENOMBRADO DE COLUMNAS")
    print("=" * 60)

    mapeo_columnas = {
        "pa_s": "pais",
        "c_digo_iso_pa_s": "codigo_iso_pais",
        "ciudad_de_residencia": "ciudad_residencia",
        "oficina_de_registro": "oficina_consular",
        "edad_a_os": "edad",
        "rea_conocimiento": "area_conocimiento",
        "nivel_acad_mico": "nivel_academico",
        "estado_civil": "estado_civil",
        "g_nero": "sexo",
        "etnia_de_la_persona": "etnia",
        "ciudad_de_nacimiento": "ciudad_nacimiento",
        "fecha_de_registro": "fecha_registro",
        "cantidad_de_personas": "cantidad_personas",
        # Alternativas por si la API devuelve nombres diferentes
        "País": "pais",
        "Código ISO país": "codigo_iso_pais",
        "Ciudad de Residencia": "ciudad_residencia",
        "Oficina de circunscripción consular": "oficina_consular",
        "Edad (años)": "edad",
        "Área Conocimiento": "area_conocimiento",
        "Nivel Académico": "nivel_academico",
        "Estado civil": "estado_civil",
        "Sexo": "sexo",
        "Pertenencia étnica": "etnia",
        "Ciudad de Nacimiento": "ciudad_nacimiento",
        "Fecha de Registro": "fecha_registro",
        "Cantidad de personas": "cantidad_personas",
    }

    # Renombrar solo columnas que existan
    columnas_existentes = {k: v for k, v in mapeo_columnas.items() if k in df.columns}
    df = df.rename(columns=columnas_existentes)

    print(f"  → Columnas renombradas: {len(columnas_existentes)}")
    print(f"  → Columnas finales: {list(df.columns)}")

    return df


# ============================================================================
# 3. LIMPIEZA DE VALORES NULOS Y NO REGISTRADOS
# ============================================================================
def limpiar_nulos(df):
    """
    Reemplaza valores como '(NO REGISTRA)', 'DESCONOCIDO', 'SIN INFORMACIÓN'
    por NaN para un tratamiento uniforme de datos faltantes.
    """
    print("\n" + "=" * 60)
    print("PASO 3: LIMPIEZA DE VALORES NULOS")
    print("=" * 60)

    valores_nulos = [
        "(NO REGISTRA)", "NO REGISTRA", "SIN INFORMACIÓN",
        "DESCONOCIDO", "NO INDICA", "NINGUNA", "NINGUNO",
        "SIN ETNIA REGISTRADA"
    ]

    # Conteo antes
    nulos_antes = df.isnull().sum().sum()

    # Reemplazar en columnas de texto
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].replace(valores_nulos, np.nan)

    # Edad -1 significa no registrada
    if "edad" in df.columns:
        df["edad"] = pd.to_numeric(df["edad"], errors="coerce")
        df.loc[df["edad"] < 0, "edad"] = np.nan
        df.loc[df["edad"] > 120, "edad"] = np.nan

    nulos_despues = df.isnull().sum().sum()

    print(f"  → Valores nulos antes: {nulos_antes:,}")
    print(f"  → Valores nulos después: {nulos_despues:,}")
    print(f"  → Valores convertidos a NaN: {nulos_despues - nulos_antes:,}")

    # Resumen de nulos por columna
    print("\n  Nulos por columna:")
    for col in df.columns:
        n = df[col].isnull().sum()
        pct = n / len(df) * 100
        if n > 0:
            print(f"    {col}: {n:,} ({pct:.1f}%)")

    return df


# ============================================================================
# 4. NORMALIZACIÓN DE NIVEL ACADÉMICO
# ============================================================================
def normalizar_nivel_academico(df):
    """
    Agrupa niveles académicos en categorías más amplias para facilitar
    el análisis de fuga de cerebros.

    Categorías resultantes:
    - Educación Básica: Primaria, Bachillerato
    - Técnica/Tecnológica: Técnica Profesional, Tecnológica
    - Profesional: Profesional, Universitaria
    - Posgrado: Especialización, Maestría, Doctorado
    """
    print("\n" + "=" * 60)
    print("PASO 4: NORMALIZACIÓN DE NIVEL ACADÉMICO")
    print("=" * 60)

    if "nivel_academico" not in df.columns:
        print("  ⚠ Columna 'nivel_academico' no encontrada")
        return df

    # Normalizar texto
    df["nivel_academico"] = df["nivel_academico"].str.strip().str.upper()

    # Mapeo a categorías agrupadas
    mapeo_nivel = {
        "PRIMARIA": "Educación Básica",
        "BACHILLERATO": "Educación Básica",
        "TÉCNICA PROFESIONAL": "Técnica/Tecnológica",
        "TECNOLÓGICA": "Técnica/Tecnológica",
        "PROFESIONAL": "Profesional",
        "UNIVERSITARIA": "Profesional",
        "ESPECIALIZACIÓN": "Posgrado",
        "MAESTRÍA": "Posgrado",
        "DOCTORADO": "Posgrado",
    }

    df["nivel_academico_agrupado"] = df["nivel_academico"].map(mapeo_nivel)

    # Estadísticas
    print("  → Distribución de niveles académicos (original):")
    dist = df["nivel_academico"].value_counts(dropna=False)
    for nivel, count in dist.head(12).items():
        print(f"    {nivel}: {count:,}")

    print("\n  → Distribución agrupada:")
    dist_agr = df["nivel_academico_agrupado"].value_counts(dropna=False)
    for nivel, count in dist_agr.items():
        print(f"    {nivel}: {count:,}")

    return df


# ============================================================================
# 5. CREACIÓN DE RANGOS DE EDAD
# ============================================================================
def crear_rangos_edad(df):
    """
    Crea una columna con rangos de edad para facilitar análisis demográficos.
    """
    print("\n" + "=" * 60)
    print("PASO 5: CREACIÓN DE RANGOS DE EDAD")
    print("=" * 60)

    if "edad" not in df.columns:
        print("  ⚠ Columna 'edad' no encontrada")
        return df

    bins = [0, 17, 25, 35, 45, 55, 65, 120]
    labels = ["0-17", "18-25", "26-35", "36-45", "46-55", "56-65", "65+"]

    df["rango_edad"] = pd.cut(df["edad"], bins=bins, labels=labels, right=True)

    print("  → Distribución por rango de edad:")
    dist = df["rango_edad"].value_counts(dropna=False).sort_index()
    for rango, count in dist.items():
        print(f"    {rango}: {count:,}")

    return df


# ============================================================================
# 6. EXTRACCIÓN DE COMPONENTES GEOGRÁFICOS
# ============================================================================
def extraer_geografia(df):
    """
    Extrae departamento y ciudad desde los campos compuestos:
    - ciudad_residencia: "ESTADO/CIUDAD" → estado_residencia, ciudad_residencia_limpia
    - ciudad_nacimiento: "PAIS/DEPTO/CIUDAD" → pais_nacimiento, depto_nacimiento, ciudad_nacimiento_limpia
    """
    print("\n" + "=" * 60)
    print("PASO 6: EXTRACCIÓN DE COMPONENTES GEOGRÁFICOS")
    print("=" * 60)

    # Ciudad de residencia: "ESTADO/CIUDAD"
    if "ciudad_residencia" in df.columns:
        split_res = df["ciudad_residencia"].str.split("/", n=1, expand=True)
        df["estado_residencia"] = split_res[0] if 0 in split_res.columns else np.nan
        df["ciudad_residencia_limpia"] = split_res[1] if 1 in split_res.columns else np.nan
        print(f"  → Ciudad de residencia descompuesta en estado + ciudad")

    # Ciudad de nacimiento: "PAIS/DEPTO/CIUDAD"
    if "ciudad_nacimiento" in df.columns:
        split_nac = df["ciudad_nacimiento"].str.split("/", n=2, expand=True)
        df["pais_nacimiento"] = split_nac[0] if 0 in split_nac.columns else np.nan
        df["depto_nacimiento"] = split_nac[1] if 1 in split_nac.columns else np.nan
        df["ciudad_nacimiento_limpia"] = split_nac[2] if 2 in split_nac.columns else np.nan
        print(f"  → Ciudad de nacimiento descompuesta en país + depto + ciudad")

    # Top ciudades de nacimiento
    if "depto_nacimiento" in df.columns:
        print("\n  → Top 10 departamentos de nacimiento:")
        top_deptos = df["depto_nacimiento"].value_counts().head(10)
        for depto, count in top_deptos.items():
            print(f"    {depto}: {count:,}")

    return df


# ============================================================================
# 7. MAPEO DE PAÍSES A CONTINENTES
# ============================================================================
def mapear_continentes(df):
    """
    Asigna un continente a cada país de residencia para análisis regional.
    """
    print("\n" + "=" * 60)
    print("PASO 7: MAPEO DE PAÍSES A CONTINENTES")
    print("=" * 60)

    if "pais" not in df.columns:
        print("  ⚠ Columna 'pais' no encontrada")
        return df

    # Mapeo manual de los principales países destino
    continentes = {
        "ESTADOS UNIDOS": "América del Norte",
        "CANADA": "América del Norte",
        "MEXICO": "América del Norte",
        "ESPAÑA": "Europa",
        "FRANCIA": "Europa",
        "REINO UNIDO": "Europa",
        "ITALIA": "Europa",
        "ALEMANIA": "Europa",
        "SUIZA": "Europa",
        "PAISES BAJOS": "Europa",
        "BELGICA": "Europa",
        "PORTUGAL": "Europa",
        "SUECIA": "Europa",
        "NORUEGA": "Europa",
        "IRLANDA": "Europa",
        "AUSTRIA": "Europa",
        "DINAMARCA": "Europa",
        "FINLANDIA": "Europa",
        "REPUBLICA CHECA": "Europa",
        "POLONIA": "Europa",
        "HUNGRIA": "Europa",
        "RUMANIA": "Europa",
        "GRECIA": "Europa",
        "RUSIA": "Europa",
        "VENEZUELA": "América del Sur",
        "ECUADOR": "América del Sur",
        "CHILE": "América del Sur",
        "ARGENTINA": "América del Sur",
        "BRASIL": "América del Sur",
        "PERU": "América del Sur",
        "URUGUAY": "América del Sur",
        "BOLIVIA": "América del Sur",
        "PARAGUAY": "América del Sur",
        "PANAMA": "América Central y Caribe",
        "COSTA RICA": "América Central y Caribe",
        "REPUBLICA DOMINICANA": "América Central y Caribe",
        "GUATEMALA": "América Central y Caribe",
        "HONDURAS": "América Central y Caribe",
        "EL SALVADOR": "América Central y Caribe",
        "NICARAGUA": "América Central y Caribe",
        "CUBA": "América Central y Caribe",
        "ARUBA": "América Central y Caribe",
        "CURACAO": "América Central y Caribe",
        "TRINIDAD Y TOBAGO": "América Central y Caribe",
        "JAMAICA": "América Central y Caribe",
        "AUSTRALIA": "Oceanía",
        "NUEVA ZELANDA": "Oceanía",
        "JAPON": "Asia",
        "CHINA": "Asia",
        "COREA DEL SUR": "Asia",
        "INDIA": "Asia",
        "ISRAEL": "Asia",
        "EMIRATOS ARABES UNIDOS": "Asia",
        "QATAR": "Asia",
        "ARABIA SAUDITA": "Asia",
        "TURQUIA": "Asia",
        "TAILANDIA": "Asia",
        "SINGAPUR": "Asia",
        "SUDAFRICA": "África",
        "EGIPTO": "África",
        "MARRUECOS": "África",
        "NIGERIA": "África",
        "KENIA": "África",
    }

    df["continente"] = df["pais"].map(continentes).fillna("Otro")

    print("  → Distribución por continente:")
    dist = df["continente"].value_counts()
    for cont, count in dist.items():
        print(f"    {cont}: {count:,}")

    return df


# ============================================================================
# 8. CONVERSIÓN DE FECHA DE REGISTRO
# ============================================================================
def procesar_fecha(df):
    """
    Convierte la fecha de registro (formato 'YYYY-MM') a columnas de año y mes.
    """
    print("\n" + "=" * 60)
    print("PASO 8: PROCESAMIENTO DE FECHA DE REGISTRO")
    print("=" * 60)

    if "fecha_registro" not in df.columns:
        print("  ⚠ Columna 'fecha_registro' no encontrada")
        return df

    # Extraer año y mes
    df["fecha_registro"] = df["fecha_registro"].astype(str)
    split_fecha = df["fecha_registro"].str.split("-", expand=True)

    if 0 in split_fecha.columns:
        df["anio_registro"] = pd.to_numeric(split_fecha[0], errors="coerce")
    if 1 in split_fecha.columns:
        df["mes_registro"] = pd.to_numeric(split_fecha[1], errors="coerce")

    # Filtrar fechas inválidas
    if "anio_registro" in df.columns:
        df.loc[df["anio_registro"] < 2000, "anio_registro"] = np.nan
        df.loc[df["anio_registro"] > 2026, "anio_registro"] = np.nan

    print(f"  → Rango de años: {df['anio_registro'].min():.0f} - {df['anio_registro'].max():.0f}")
    print(f"  → Registros con fecha válida: {df['anio_registro'].notna().sum():,}")

    return df


# ============================================================================
# 9. ELIMINACIÓN DE COLUMNAS IRRELEVANTES
# ============================================================================
def eliminar_columnas(df):
    """
    Elimina columnas vacías o que no aportan al análisis.
    """
    print("\n" + "=" * 60)
    print("PASO 9: ELIMINACIÓN DE COLUMNAS IRRELEVANTES")
    print("=" * 60)

    # Columnas a eliminar (vacías según metadatos)
    cols_eliminar = [
        "localizaci_n_address", "localizaci_n_city",
        "localizaci_n_state", "localizaci_n_zip",
        "localizaci_n", "Localización (address)",
        "Localización (city)", "Localización (state)",
        "Localización (zip)", "Localización",
    ]

    eliminadas = []
    for col in cols_eliminar:
        if col in df.columns:
            df = df.drop(columns=[col])
            eliminadas.append(col)

    # Eliminar columnas 100% nulas
    cols_nulas = df.columns[df.isnull().all()].tolist()
    if cols_nulas:
        df = df.drop(columns=cols_nulas)
        eliminadas.extend(cols_nulas)

    print(f"  → Columnas eliminadas ({len(eliminadas)}): {eliminadas}")
    print(f"  → Columnas restantes ({len(df.columns)}): {list(df.columns)}")

    return df


# ============================================================================
# 10. EXPORTACIÓN
# ============================================================================
def exportar_datos(df):
    """
    Exporta el DataFrame limpio a CSV.
    """
    print("\n" + "=" * 60)
    print("PASO 10: EXPORTACIÓN DE DATOS LIMPIOS")
    print("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CLEAN_FILE, index=False)

    size_mb = os.path.getsize(CLEAN_FILE) / (1024 * 1024)
    print(f"  → Archivo exportado: {CLEAN_FILE}")
    print(f"  → Tamaño: {size_mb:.1f} MB")
    print(f"  → Registros: {len(df):,}")
    print(f"  → Columnas: {len(df.columns)}")

    return df


# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================
def main():
    print("\n" + "█" * 60)
    print("  PREPROCESAMIENTO - COLOMBIANOS EN EL EXTERIOR")
    print("  Análisis de Fuga de Cerebros")
    print("█" * 60)

    # Pipeline de preprocesamiento
    df = descargar_datos()
    df = renombrar_columnas(df)
    df = limpiar_nulos(df)
    df = normalizar_nivel_academico(df)
    df = crear_rangos_edad(df)
    df = extraer_geografia(df)
    df = mapear_continentes(df)
    df = procesar_fecha(df)
    df = eliminar_columnas(df)
    df = exportar_datos(df)

    # Resumen final
    print("\n" + "█" * 60)
    print("  RESUMEN FINAL")
    print("█" * 60)
    print(f"  Registros totales: {len(df):,}")
    print(f"  Columnas: {len(df.columns)}")
    print(f"  Memoria: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print(f"  Archivo limpio: {CLEAN_FILE}")
    print("█" * 60 + "\n")

    return df


if __name__ == "__main__":
    main()
