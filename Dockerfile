FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para WeasyPrint y otras librerías
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para comprobantes
RUN mkdir -p comprobantes

# Exponer puerto
EXPOSE 5000

# Variables de entorno por defecto
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
