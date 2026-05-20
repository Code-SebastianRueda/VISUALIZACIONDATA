"""Script para generar el notebook de preprocesamiento."""
import json

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "cells": []
}

def md(source):
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [source]
    })

def code(source):
    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [source],
        "outputs": [],
        "execution_count": None
    })

# ============ CELDAS DEL NOTEBOOK ============

md("""# 🇨🇴 Preprocesamiento de Datos - Colombianos en el Exterior

## Análisis Exploratorio del Fenómeno Migratorio y Fuga de Cerebros

**Fuente:** Ministerio de Relaciones Exteriores - datos.gov.co  
**Dataset:** Connacionales inscritos en el Registro Ciudadano en Línea (y399-rzwf)  
**Registros:** ~1.8 millones

### Objetivo
Este cuaderno realiza el preprocesamiento completo de los datos del Registro Ciudadano en Línea, 
generando un archivo de data limpia (`datos_limpios.csv`) que alimentará el dashboard de Streamlit.

### Variables Clave
- **Nivel Académico:** Para identificar fuga de cerebros
- **Área de Conocimiento:** Para detectar disciplinas con mayor migración
- **País de Residencia:** Para mapear destinos del talento colombiano
""")

code("""# Importar librerías necesarias
import pandas as pd
import numpy as np
import requests
import time
import os
from io import StringIO

# Configuración de visualización
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 50)
pd.set_option('display.float_format', '{:.2f}'.format)

print("✅ Librerías cargadas correctamente")
""")

md("""## 1. Descarga de Datos desde la API

Los datos se descargan desde la API SODA (Socrata Open Data API) de datos.gov.co.
El dataset tiene ~1.8 millones de registros, por lo que se usa paginación con bloques de 50,000.

**Cambio realizado:** Se implementa descarga incremental con manejo de errores y rate limiting 
para respetar los límites de la API.
""")

code("""# Configuración de descarga
DATA_DIR = "data"
RAW_FILE = os.path.join(DATA_DIR, "datos_crudos.csv")
DATASET_ID = "y399-rzwf"
BASE_URL = f"https://www.datos.gov.co/resource/{DATASET_ID}.csv"
LIMIT = 50000

os.makedirs(DATA_DIR, exist_ok=True)

# Descargar datos (o cargar si ya existen)
if os.path.exists(RAW_FILE):
    print(f"📂 Cargando datos existentes desde {RAW_FILE}...")
    df = pd.read_csv(RAW_FILE, low_memory=False)
    print(f"✅ {len(df):,} registros cargados")
else:
    print(f"⬇️ Descargando datos desde datos.gov.co...")
    all_data = []
    offset = 0
    batch = 1
    
    while True:
        url = f"{BASE_URL}?$limit={LIMIT}&$offset={offset}&$order=:id"
        print(f"  Bloque {batch}: offset={offset:,}...", end=" ")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            chunk = pd.read_csv(StringIO(response.text), low_memory=False)
            
            if chunk.empty:
                print("✅ Descarga completa.")
                break
            
            all_data.append(chunk)
            print(f"OK ({len(chunk):,} registros)")
            offset += LIMIT
            batch += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Error: {e}. Reintentando...")
            time.sleep(5)
            continue
    
    df = pd.concat(all_data, ignore_index=True)
    df.to_csv(RAW_FILE, index=False)
    print(f"\\n✅ Total: {len(df):,} registros guardados en {RAW_FILE}")
""")

md("""## 2. Exploración Inicial de los Datos

Antes de limpiar, exploramos la estructura y calidad de los datos crudos.
""")

code("""# Dimensiones del dataset
print(f"Dimensiones: {df.shape[0]:,} filas x {df.shape[1]} columnas")
print(f"\\nColumnas disponibles:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col} ({df[col].dtype})")
""")

code("""# Primeras filas
df.head(10)
""")

code("""# Información general
df.info()
""")

code("""# Estadísticas descriptivas
df.describe(include='all').T
""")

code("""# Valores nulos por columna
nulos = df.isnull().sum()
nulos_pct = (nulos / len(df) * 100).round(1)
resumen_nulos = pd.DataFrame({'Nulos': nulos, 'Porcentaje (%)': nulos_pct})
resumen_nulos[resumen_nulos['Nulos'] > 0].sort_values('Porcentaje (%)', ascending=False)
""")

md("""## 3. Renombrado de Columnas

**Cambio realizado:** Las columnas de la API tienen nombres técnicos con caracteres especiales 
(acentos codificados, guiones bajos). Se renombran a nombres legibles y consistentes en español.
""")

code("""# Mapeo de nombres técnicos a nombres legibles
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
    # Alternativas
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

columnas_existentes = {k: v for k, v in mapeo_columnas.items() if k in df.columns}
df = df.rename(columns=columnas_existentes)

print(f"✅ {len(columnas_existentes)} columnas renombradas")
print(f"Columnas finales: {list(df.columns)}")
""")

md("""## 4. Limpieza de Valores Nulos y No Registrados

**Cambio realizado:** El dataset usa múltiples convenciones para datos faltantes:
- `(NO REGISTRA)`, `NO REGISTRA`
- `SIN INFORMACIÓN`, `DESCONOCIDO`
- `NO INDICA`, `NINGUNA`, `NINGUNO`
- Edad = -1 (valor centinela)
- Edad > 120 (valores imposibles)

Todos se unifican como `NaN` para tratamiento consistente.
""")

code("""# Valores que representan datos faltantes
valores_nulos = [
    "(NO REGISTRA)", "NO REGISTRA", "SIN INFORMACIÓN",
    "DESCONOCIDO", "NO INDICA", "NINGUNA", "NINGUNO",
    "SIN ETNIA REGISTRADA"
]

nulos_antes = df.isnull().sum().sum()

# Reemplazar en columnas de texto
for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].replace(valores_nulos, np.nan)

# Limpiar edad
if "edad" in df.columns:
    df["edad"] = pd.to_numeric(df["edad"], errors="coerce")
    df.loc[df["edad"] < 0, "edad"] = np.nan
    df.loc[df["edad"] > 120, "edad"] = np.nan

nulos_despues = df.isnull().sum().sum()

print(f"Valores nulos antes: {nulos_antes:,}")
print(f"Valores nulos después: {nulos_despues:,}")
print(f"Valores convertidos a NaN: {nulos_despues - nulos_antes:,}")
print(f"\\nResumen de nulos por columna:")
for col in df.columns:
    n = df[col].isnull().sum()
    if n > 0:
        print(f"  {col}: {n:,} ({n/len(df)*100:.1f}%)")
""")

md("""## 5. Normalización de Nivel Académico

**Cambio realizado:** Se crea una columna `nivel_academico_agrupado` que clasifica los 
niveles en 4 categorías para facilitar el análisis de fuga de cerebros:

| Categoría | Niveles Incluidos |
|-----------|-------------------|
| Educación Básica | Primaria, Bachillerato |
| Técnica/Tecnológica | Técnica Profesional, Tecnológica |
| Profesional | Profesional, Universitaria |
| Posgrado | Especialización, Maestría, Doctorado |
""")

code("""# Normalizar texto
if "nivel_academico" in df.columns:
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

print("Distribución de Nivel Académico (original):")
print(df["nivel_academico"].value_counts(dropna=False).to_string())
print(f"\\nDistribución Agrupada:")
print(df["nivel_academico_agrupado"].value_counts(dropna=False).to_string())
""")

md("""## 6. Creación de Rangos de Edad

**Cambio realizado:** Se discretiza la variable continua de edad en rangos 
para facilitar análisis demográficos y visualizaciones agrupadas.
""")

code("""# Crear rangos de edad
bins = [0, 17, 25, 35, 45, 55, 65, 120]
labels = ["0-17", "18-25", "26-35", "36-45", "46-55", "56-65", "65+"]

df["rango_edad"] = pd.cut(df["edad"], bins=bins, labels=labels, right=True)

print("Distribución por rango de edad:")
print(df["rango_edad"].value_counts(dropna=False).sort_index().to_string())
""")

md("""## 7. Extracción de Componentes Geográficos

**Cambio realizado:** Los campos geográficos vienen en formato compuesto:
- `ciudad_residencia`: "ESTADO/CIUDAD" → se separa en `estado_residencia` y `ciudad_residencia_limpia`
- `ciudad_nacimiento`: "PAIS/DEPTO/CIUDAD" → se separa en `pais_nacimiento`, `depto_nacimiento`, `ciudad_nacimiento_limpia`

Esto permite análisis por departamento de origen y ciudad específica.
""")

code("""# Descomponer ciudad de residencia
if "ciudad_residencia" in df.columns:
    split_res = df["ciudad_residencia"].str.split("/", n=1, expand=True)
    df["estado_residencia"] = split_res[0] if 0 in split_res.columns else np.nan
    df["ciudad_residencia_limpia"] = split_res[1] if 1 in split_res.columns else np.nan
    print("✅ Ciudad de residencia descompuesta")

# Descomponer ciudad de nacimiento
if "ciudad_nacimiento" in df.columns:
    split_nac = df["ciudad_nacimiento"].str.split("/", n=2, expand=True)
    df["pais_nacimiento"] = split_nac[0] if 0 in split_nac.columns else np.nan
    df["depto_nacimiento"] = split_nac[1] if 1 in split_nac.columns else np.nan
    df["ciudad_nacimiento_limpia"] = split_nac[2] if 2 in split_nac.columns else np.nan
    print("✅ Ciudad de nacimiento descompuesta")

print(f"\\nTop 10 departamentos de nacimiento:")
print(df["depto_nacimiento"].value_counts().head(10).to_string())
""")

md("""## 8. Mapeo de Países a Continentes

**Cambio realizado:** Se asigna un continente a cada país de residencia mediante un 
diccionario manual que cubre los principales destinos migratorios colombianos.
Esto permite análisis regionales y visualizaciones por continente.
""")

code("""# Mapeo de países a continentes
continentes = {
    "ESTADOS UNIDOS": "América del Norte", "CANADA": "América del Norte",
    "MEXICO": "América del Norte",
    "ESPAÑA": "Europa", "FRANCIA": "Europa", "REINO UNIDO": "Europa",
    "ITALIA": "Europa", "ALEMANIA": "Europa", "SUIZA": "Europa",
    "PAISES BAJOS": "Europa", "BELGICA": "Europa", "PORTUGAL": "Europa",
    "SUECIA": "Europa", "NORUEGA": "Europa", "IRLANDA": "Europa",
    "AUSTRIA": "Europa", "DINAMARCA": "Europa", "FINLANDIA": "Europa",
    "REPUBLICA CHECA": "Europa", "POLONIA": "Europa",
    "VENEZUELA": "América del Sur", "ECUADOR": "América del Sur",
    "CHILE": "América del Sur", "ARGENTINA": "América del Sur",
    "BRASIL": "América del Sur", "PERU": "América del Sur",
    "URUGUAY": "América del Sur", "BOLIVIA": "América del Sur",
    "PANAMA": "América Central y Caribe", "COSTA RICA": "América Central y Caribe",
    "REPUBLICA DOMINICANA": "América Central y Caribe",
    "GUATEMALA": "América Central y Caribe", "ARUBA": "América Central y Caribe",
    "CURACAO": "América Central y Caribe",
    "AUSTRALIA": "Oceanía", "NUEVA ZELANDA": "Oceanía",
    "JAPON": "Asia", "CHINA": "Asia", "COREA DEL SUR": "Asia",
    "ISRAEL": "Asia", "EMIRATOS ARABES UNIDOS": "Asia",
    "SUDAFRICA": "África", "EGIPTO": "África",
}

df["continente"] = df["pais"].map(continentes).fillna("Otro")

print("Distribución por continente:")
print(df["continente"].value_counts().to_string())
""")

md("""## 9. Procesamiento de Fecha de Registro

**Cambio realizado:** La fecha viene en formato "YYYY-MM" (texto). Se extraen 
componentes de año y mes como columnas numéricas, filtrando fechas inválidas 
(anteriores a 2000 o futuras).
""")

code("""# Procesar fecha de registro
if "fecha_registro" in df.columns:
    df["fecha_registro"] = df["fecha_registro"].astype(str)
    split_fecha = df["fecha_registro"].str.split("-", expand=True)
    
    if 0 in split_fecha.columns:
        df["anio_registro"] = pd.to_numeric(split_fecha[0], errors="coerce")
    if 1 in split_fecha.columns:
        df["mes_registro"] = pd.to_numeric(split_fecha[1], errors="coerce")
    
    # Filtrar fechas inválidas
    df.loc[df["anio_registro"] < 2000, "anio_registro"] = np.nan
    df.loc[df["anio_registro"] > 2026, "anio_registro"] = np.nan
    
    print(f"Rango de años: {df['anio_registro'].min():.0f} - {df['anio_registro'].max():.0f}")
    print(f"Registros con fecha válida: {df['anio_registro'].notna().sum():,}")
    print(f"\\nDistribución por año (top 10):")
    print(df["anio_registro"].value_counts().head(10).sort_index().to_string())
""")

md("""## 10. Eliminación de Columnas Irrelevantes

**Cambio realizado:** Se eliminan columnas que están 100% vacías según los metadatos 
del dataset (localización address, city, state, zip) y la columna de punto geográfico 
que no se usa en el análisis tabular.
""")

code("""# Columnas a eliminar
cols_eliminar = [
    "localizaci_n_address", "localizaci_n_city",
    "localizaci_n_state", "localizaci_n_zip",
    "localizaci_n", "Localización (address)",
    "Localización (city)", "Localización (state)",
    "Localización (zip)", "Localización",
]

eliminadas = [col for col in cols_eliminar if col in df.columns]
df = df.drop(columns=eliminadas, errors='ignore')

# Eliminar columnas 100% nulas
cols_nulas = df.columns[df.isnull().all()].tolist()
if cols_nulas:
    df = df.drop(columns=cols_nulas)
    eliminadas.extend(cols_nulas)

print(f"✅ Columnas eliminadas ({len(eliminadas)}): {eliminadas}")
print(f"\\nColumnas finales ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")
""")

md("""## 11. Exportación de Datos Limpios

Se exporta el DataFrame procesado a CSV para uso en el dashboard de Streamlit.
""")

code("""# Exportar datos limpios
CLEAN_FILE = os.path.join(DATA_DIR, "datos_limpios.csv")
df.to_csv(CLEAN_FILE, index=False)

size_mb = os.path.getsize(CLEAN_FILE) / (1024 * 1024)
print(f"✅ Archivo exportado: {CLEAN_FILE}")
print(f"   Tamaño: {size_mb:.1f} MB")
print(f"   Registros: {len(df):,}")
print(f"   Columnas: {len(df.columns)}")
""")

md("""## 12. Resumen Final del Preprocesamiento

### Transformaciones Aplicadas:

| # | Transformación | Descripción |
|---|---------------|-------------|
| 1 | Descarga API | Paginación SODA, 50K registros/bloque |
| 2 | Renombrado | Nombres técnicos → legibles |
| 3 | Limpieza nulos | Unificación de valores faltantes |
| 4 | Nivel académico | Agrupación en 4 categorías |
| 5 | Rangos de edad | Discretización en 7 rangos |
| 6 | Geografía | Descomposición de campos compuestos |
| 7 | Continentes | Mapeo país → continente |
| 8 | Fechas | Extracción año/mes |
| 9 | Eliminación | Columnas vacías removidas |
| 10 | Exportación | CSV limpio para dashboard |

### Archivo de Salida
El archivo `data/datos_limpios.csv` está listo para ser consumido por el dashboard 
de Streamlit (`app.py`) que genera las 15 visualizaciones interactivas.
""")

code("""# Resumen final
print("=" * 60)
print("  RESUMEN FINAL DEL PREPROCESAMIENTO")
print("=" * 60)
print(f"  Registros totales: {len(df):,}")
print(f"  Columnas: {len(df.columns)}")
print(f"  Memoria: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
print(f"  Archivo: {CLEAN_FILE}")
print("=" * 60)
print(f"\\n📊 Datos listos para el dashboard de Streamlit")
""")

# Guardar notebook
with open("notebook_preprocesamiento.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print("✅ Notebook creado: notebook_preprocesamiento.ipynb")
