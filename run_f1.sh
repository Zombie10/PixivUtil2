#!/bin/bash

# ==============================================
# Script para ejecutar PixivUtil2 con opción f1
# Descarga desde tu lista de artistas que apoyas en FANBOX
# ==============================================

echo "Activando entorno virtual..."
source env/bin/activate

echo "Ejecutando PixivUtil2 con opción f1 (FANBOX - Supporting list)..."
echo "El progreso se guardará en: run_f.log"

python PixivUtil2.py -s f1 >> run_f1.log 2>&1

deactivate

echo ""
echo "✅ Proceso finalizado. Log guardado en run_f1.log"