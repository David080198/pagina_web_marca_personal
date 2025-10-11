#!/bin/bash

# Script de inicialización completa para VPS
# Este script configura todo automáticamente

echo "🚀 INICIALIZANDO CODEXSOTO EN VPS"
echo "=================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Paso 1: Parando contenedores existentes...${NC}"
docker compose down

echo -e "${BLUE}📋 Paso 2: Construyendo imágenes...${NC}"
docker compose build

echo -e "${BLUE}📋 Paso 3: Iniciando base de datos...${NC}"
docker compose up -d db redis

echo -e "${YELLOW}⏳ Esperando a que la base de datos esté lista...${NC}"
sleep 15

echo -e "${BLUE}📋 Paso 4: Recreando tablas con estructura correcta...${NC}"
# Usar script especializado para recrear tablas
docker compose run --rm web python recreate_tables.py

echo -e "${BLUE}📋 Paso 5: Iniciando aplicación web...${NC}"
docker compose up -d web

echo -e "${BLUE}📋 Paso 6: Iniciando nginx...${NC}"
docker compose up -d nginx

echo -e "${YELLOW}⏳ Esperando a que la aplicación esté lista...${NC}"
sleep 10

echo ""
echo -e "${GREEN}🎉 ¡CODEXSOTO INICIALIZADO EXITOSAMENTE!${NC}"
echo "=========================================="
echo -e "${GREEN}📝 INFORMACIÓN DE ACCESO:${NC}"
echo -e "   🌐 URL del sitio: ${BLUE}http://tu-dominio.com${NC}"
echo -e "   🔧 Panel de admin: ${BLUE}http://tu-dominio.com/admin${NC}"
echo -e "   📧 Email admin: ${YELLOW}admin@codexsoto.com${NC}"
echo -e "   🔑 Contraseña: ${YELLOW}admin123${NC}"
echo ""
echo -e "${BLUE}📊 Para ver logs:${NC}"
echo "   docker compose logs -f web"
echo ""
echo -e "${BLUE}📈 Estado de contenedores:${NC}"
docker compose ps

echo ""
echo -e "${GREEN}✅ Inicialización completada${NC}"