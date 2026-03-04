@echo off
chcp 65001 >nul
REM Script para compilar GestionTareasMAET.exe (x64) en Windows
REM Ejecutar en VM Windows desde la carpeta del proyecto

echo ========================================
echo  Compilacion Windows x64 - MAET
echo ========================================
echo.

echo Verificando Python 64-bit...
python -c "import sys; exit(0 if sys.maxsize > 2**32 else 1)"
if errorlevel 1 (
    echo.
    echo ERROR: Se requiere Python 64-bit.
    echo Descarga desde: https://www.python.org/downloads/
    echo Elige "Windows installer (64-bit)"
    echo.
    pause
    exit /b 1
)
echo OK - Python 64-bit detectado
echo.

echo Instalando dependencias...
pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo Error al instalar dependencias.
    pause
    exit /b 1
)
echo.

echo Compilando con PyInstaller...
pyinstaller --noconfirm build_exe.spec
if errorlevel 1 (
    echo.
    echo Error en la compilacion.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Compilacion completada
echo ========================================
echo.
echo El .exe esta en: dist\GestionTareasMAET\GestionTareasMAET.exe
echo.
echo Para distribuir: comprime TODA la carpeta dist\GestionTareasMAET
echo.
pause
