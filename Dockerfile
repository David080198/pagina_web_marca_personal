FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios para uploads
RUN mkdir -p app/static/uploads/blog app/static/uploads/courses app/static/uploads/projects app/static/uploads/avatars

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Exponer puerto
EXPOSE 5000

# Comando por defecto
CMD ["python", "app.py"]
