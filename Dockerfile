FROM python:3.13-slim

# Evitar buffering de salida de Python (útil para logs en producción)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# (Opcional) Instalar dependencias del sistema necesarias para compilar
RUN apt update && apt-get clean
RUN pip install --upgrade pip
# Copia y instala dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . .

# Nota: El comando se define en docker-compose, así que no es necesario CMD en el Dockerfile
