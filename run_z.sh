#!/bin/bash

# ==============================================
# Script para ejecutar PixivUtil2 con opción z
# Descarga automáticamente páginas 1-4 de tus bookmarks de artistas
# Uso: ./run_z.sh [NÚMERO_DE_PÁGINAS_DE_BOOKMARKS]
# Ejemplo: ./run_z.sh 10 → Descarga páginas 1-10 de bookmarks + páginas 1-4
# ==============================================

BOOKMARK_PAGES=${1:-5} # Cantidad de páginas de bookmarks (artistas)
DOWNLOAD_PAGES=${2:-4} # Páginas a descargar de cada artista

echo "Activando entorno virtual..."
source env/bin/activate

echo "Ejecutando PixivUtil2 con opción z → 📌 últimas $BOOKMARK_PAGES páginas de bookmarks + 📥 (páginas 1-$DOWNLOAD_PAGES) por artista..."
echo "El progreso se guardará en: run_z.log"

python PixivUtil2.py -s z --b=$BOOKMARK_PAGES --sp=1 --ep=$DOWNLOAD_PAGES >> run_z.log 2>&1

deactivate

echo ""
echo "✅ Proceso finalizado. Log guardado en run_z.log"