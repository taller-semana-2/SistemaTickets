# Dockerfile para users-service
FROM python:3.12-slim

# Variables de entorno Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt /app/

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . /app/

# Puerto del servicio (8001 para users-service)
EXPOSE 8001

# Comando por defecto
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
