FROM python:3.11-slim

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Script de inicio: ejecuta preprocesamiento si no hay datos limpios, luego lanza Streamlit
CMD ["bash", "-c", "if [ ! -f data/datos_limpios.csv ]; then python preprocessing.py; fi && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
