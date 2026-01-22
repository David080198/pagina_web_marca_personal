#!/bin/bash
# Script para compilar traducciones dentro del contenedor Docker

echo "🌍 Compilando traducciones..."
pybabel compile -d translations

echo "✅ Traducciones compiladas exitosamente!"
echo "📋 Archivos generados:"
ls -la translations/*/LC_MESSAGES/*.mo
