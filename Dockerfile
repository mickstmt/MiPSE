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

# Crear directorios para persistencia de comprobantes y archivos SUNAT
RUN mkdir -p comprobantes xml_generados cdr_recibidos

# Exponer puerto estándar de producción
EXPOSE 80

# Variables de entorno por defecto
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación en el puerto 80
# Reducimos a 2 workers por si el VPS tiene poca RAM
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "--timeout", "300", "app:app"]
