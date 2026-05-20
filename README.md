# 🇨🇴 Colombianos en el Exterior - Dashboard de Fuga de Cerebros

Dashboard interactivo de visualización de datos sobre el fenómeno migratorio colombiano, con enfoque en la fuga de cerebros.

## 📊 Ejes de Análisis

1. **Fuga de Cerebros** - Talento altamente calificado (Maestría/Doctorado)
2. **Demografía y Dinámicas Sociales** - Perfil del migrante
3. **Servicios Consulares** - Cobertura y carga operativa
4. **Rutas Migratorias y Tiempo** - Flujos y evolución temporal

## 🚀 Ejecución con Docker

```bash
docker-compose up --build
```

Accede al dashboard en: http://localhost:8501

## 🛠️ Ejecución Local (sin Docker)

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar preprocesamiento (descarga y limpia datos)
```bash
python preprocessing.py
```

### 3. Ejecutar dashboard
```bash
streamlit run app.py
```

## 📁 Estructura del Proyecto

```
VISUALIZACIONDATA/
├── app.py                 # Dashboard Streamlit (visualizaciones)
├── preprocessing.py       # Preprocesamiento y limpieza de datos
├── requirements.txt       # Dependencias Python
├── Dockerfile            # Imagen Docker
├── docker-compose.yml    # Orquestación Docker
├── .dockerignore         # Archivos excluidos de Docker
├── README.md             # Este archivo
└── data/                 # Datos (generados por preprocessing.py)
    ├── datos_crudos.csv  # Datos originales de la API
    └── datos_limpios.csv # Datos procesados para visualización
```

## 📋 Fuente de Datos

- **Dataset:** Connacionales inscritos en el Registro Ciudadano en Línea
- **Entidad:** Ministerio de Relaciones Exteriores de Colombia
- **URL:** https://www.datos.gov.co/d/y399-rzwf
- **Registros:** ~1.8 millones
- **Licencia:** CC BY-SA 4.0

## 🔧 Preprocesamiento Realizado

1. Descarga via API SODA con paginación
2. Renombrado de columnas técnicas a nombres legibles
3. Limpieza de valores nulos/no registrados
4. Normalización de niveles académicos (agrupación)
5. Creación de rangos de edad
6. Extracción de componentes geográficos (depto, ciudad)
7. Mapeo de países a continentes
8. Procesamiento de fechas (año/mes)
9. Eliminación de columnas vacías
10. Exportación a CSV limpio
