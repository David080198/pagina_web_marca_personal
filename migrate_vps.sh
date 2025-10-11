#!/bin/bash
# Script para ejecutar migraciones en el VPS

echo "=== Ejecutando migraciones de Flask ==="

# Parar los contenedores
docker compose down

# Ejecutar migraciones dentro del contenedor web
docker compose run --rm web flask db upgrade

# Si no existe flask db, crear las migraciones
# docker compose run --rm web flask db init
# docker compose run --rm web flask db migrate -m "Initial migration"
# docker compose run --rm web flask db upgrade

# Levantar los contenedores
docker compose up -d

echo "=== Migraciones completadas ==="