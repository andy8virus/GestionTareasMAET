@echo off
REM Script para ejecutar la app con Python en Windows (sin compilar .exe)
REM Doble clic o ejecutar desde CMD en esta carpeta

echo Verificando Python...
python --version 2>nul
if errorlevel 1 (
    echo.
    echo Python no esta instalado. Descargalo desde:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo Instalando dependencias...
pip install -r requirements.txt -q

echo.
echo Iniciando aplicacion...
python gestion_tareas.py

if errorlevel 1 (
    echo.
    echo Hubo un error. Asegurate de tener Python y las dependencias instaladas.
)
pause
