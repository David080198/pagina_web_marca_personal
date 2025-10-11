#!/bin/bash
# Script para recrear la base de datos desde cero

echo "=== Recreando base de datos ==="

# Parar y remover contenedores
docker compose down -v

# Remover volúmenes de la base de datos (esto borra todos los datos)
docker volume prune -f

# Levantar solo la base de datos primero
docker compose up -d db redis

# Esperar a que la BD esté lista
sleep 10

# Levantar la aplicación (esto creará las tablas automáticamente)
docker compose up -d web

# Ver logs para verificar
docker compose logs web

echo "=== Base de datos recreada ==="