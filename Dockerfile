# Usamos la imagen ligera compatible con Pi Zero
FROM balenalib/raspberry-pi-python:3.9-buster

# Instalamos fswebcam (herramienta ligera para cámaras USB)
RUN apt-get update && apt-get install -y \
    fswebcam \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Actualizamos pip e instalamos SOLO Flask y MySQL
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
