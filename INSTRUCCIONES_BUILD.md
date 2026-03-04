# Instrucciones para Compilar Gestión de Tareas MAET

## Requisitos Previos

- **Python 3.12+** instalado
- **CustomTkinter** y **PyInstaller**

## Instalación de Dependencias (en Mac o Windows)

```bash
cd /ruta/a/Aplicacion_gestion
pip install -r requirements.txt
pip install pyinstaller
```

**En Mac:** Si usas Homebrew Python, crea un entorno virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Nota para Mac:** Python en macOS a veces no incluye Tcl/Tk. Para ejecutar la app necesitas `python-tk` (ej: `brew install python-tk@3.12`). En Windows, Python suele incluir todo por defecto.

## Ejecutar la Aplicación (Desarrollo)

```bash
python gestion_tareas.py
# o con venv activado:
# source .venv/bin/activate && python gestion_tareas.py
```

---

## Compilar como .exe para Windows 11

**Importante:** PyInstaller genera ejecutables solo para el sistema operativo donde se ejecuta. Es decir, **desde Mac no se puede generar un .exe directamente**. Opciones:

### Opción 1: Compilar en Windows (Recomendado)

Si tienes acceso a una máquina Windows (PC, portátil o VM):

1. Copia la carpeta `Aplicacion_gestion` al equipo Windows.
2. Instala **Python 3.12+ (64-bit)** desde [python.org](https://www.python.org/downloads/) para generar .exe x64.
3. Abre CMD o PowerShell en la carpeta del proyecto:

```cmd
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build_exe.spec
```

4. El ejecutable estará en: `dist/GestionTareasMAET/GestionTareasMAET.exe`

5. **Distribución:** Comprime toda la carpeta `dist/GestionTareasMAET` en un ZIP y compártela. El usuario debe extraerla y ejecutar `GestionTareasMAET.exe`. El archivo `tareas.db` se creará automáticamente en la misma carpeta donde se ejecute.

### Opción 2: Compilar desde Mac usando GitHub Actions

Crea un repositorio en GitHub y añade este archivo:

**.github/workflows/build-windows.yml**

```yaml
name: Build Windows EXE

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build EXE
        run: pyinstaller build_exe.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: GestionTareasMAET-Windows
          path: dist/GestionTareasMAET
```

Sube el proyecto, ejecuta el workflow y descarga el ZIP del artefacto.

### Opción 3: Usar una Máquina Virtual Windows (desde Mac)

- **Parallels**, **VMware Fusion** o **VirtualBox** con Windows 11
- Ver guía completa: **[BUILD_VM_WINDOWS.md](BUILD_VM_WINDOWS.md)** (x64, script COMPILAR_VM.bat)

### Opción 4: Comando PyInstaller Manual (Alternativa al .spec)

Si prefieres no usar el archivo `.spec`:

```cmd
pip show customtkinter
```

Copia la ruta mostrada (ej: `C:\Users\...\site-packages`) y ejecuta:

```cmd
pyinstaller --noconfirm --onedir --windowed --add-data "RUTA_CUSTOMTKINTER\customtkinter;customtkinter/" gestion_tareas.py
```

Reemplaza `RUTA_CUSTOMTKINTER` por la ruta completa a `site-packages`.

---

## Estructura del Proyecto

```
Aplicacion_gestion/
├── gestion_tareas.py      # Aplicación principal
├── requirements.txt       # Dependencias
├── build_exe.spec         # Configuración PyInstaller
├── INSTRUCCIONES_BUILD.md # Este archivo
└── tareas.db              # (se crea al ejecutar) Base de datos local
```

## Usuarios y Acceso

- **Admin:** Usuario `Andy` con clave `MAET2026` (acceso a Gestión de Usuarios).
- **Tareas:** Cada usuario debe ingresar con su propia clave para agregar o editar tareas.
- El admin puede agregar y eliminar usuarios desde la pestaña "Gestión de Usuarios".
