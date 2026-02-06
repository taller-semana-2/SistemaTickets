# --- Dockerfile para Assessment Service ---
FROM python:3.12-slim

# Evita buffers en la salida
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Copiar y actualizar pip
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . .

# Exponer puerto solo si quieres acceder al admin de Django (opcional)
EXPOSE 8001

# Comando por defecto: migrar la DB y correr worker de Celery
CMD sh -c "python manage.py migrate && celery -A assessment_service worker --loglevel=info"
