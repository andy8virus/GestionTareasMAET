# Compilar .exe x64 en máquina virtual Windows (desde Mac)

Guía para crear un ejecutable **Windows x64** usando una VM Windows en tu Mac (Parallels, VMware Fusion o VirtualBox).

**Si tu Mac es M1/M2/M3/M4 (Apple Silicon):** La VM Windows será ARM64 y no generará .exe x64. Usa **GitHub Actions** (ver INSTRUCCIONES_BUILD.md) para compilar x64 en la nube.

---

## 1. Configurar la máquina virtual

- **Parallels**, **VMware Fusion** o **VirtualBox** con **Windows 11** (o Windows 10).
- La arquitectura del .exe coincide con la VM: Windows x64 produce .exe x64; Windows ARM produce .exe ARM64. Para .exe x64: usa VM Windows x64 (Mac Intel) o GitHub Actions.

> **Mac Apple Silicon (M1/M2/M3/M4):** Parallels/VMware usan Windows ARM64, que genera .exe ARM64 (no x64). Para .exe x64: **GitHub Actions** (sube el proyecto y ejecuta el workflow) o usa un PC Windows físico.

---

## 2. Instalar Python 64-bit en la VM

1. Ve a [python.org/downloads](https://www.python.org/downloads/) y descarga **Windows installer (64-bit)**.
2. Durante la instalación:
   - Marca **"Add python.exe to PATH"**.
   - Elige **"Customize installation"** si quieres controlar la ruta.
3. Verifica en CMD o PowerShell:

```cmd
python --version
```

- Si aparece algo como `Python 3.12.x` en un Windows de 64 bits, estás usando Python 64-bit.

---

## 3. Copiar el proyecto a la VM

- Comparte la carpeta entre Mac y VM (carpetas compartidas de Parallels/VMware).
- O copia la carpeta `Aplicacion_gestion` completa dentro de la VM.

---

## 4. Compilar el ejecutable x64

1. Abre **CMD** o **PowerShell** en la carpeta del proyecto.
2. Instala dependencias y PyInstaller:

```cmd
pip install -r requirements.txt
pip install pyinstaller
```

3. Compila:

```cmd
pyinstaller build_exe.spec
```

4. El resultado estará en:
   ```
   dist\GestionTareasMAET\GestionTareasMAET.exe
   ```

5. Para distribuir, comprime **toda la carpeta** `dist\GestionTareasMAET` (incluye el .exe, `customtkinter`, etc.).

---

## 5. Verificar que el .exe es x64

En PowerShell (como administrador opcional):

```powershell
[System.Reflection.Assembly]::LoadFile("ruta_completa\GestionTareasMAET.exe").GetName().ProcessorArchitecture
```

O usa herramientas como **Dependencies** o **PEview** para revisar el ejecutable.

---

## Resumen rápido

| Paso | Acción |
|------|--------|
| 1 | Crear/abrir VM Windows x64 |
| 2 | Instalar Python 64-bit desde python.org |
| 3 | Copiar carpeta `Aplicacion_gestion` a la VM |
| 4 | `pip install -r requirements.txt` y `pip install pyinstaller` |
| 5 | `pyinstaller build_exe.spec` |
| 6 | Usar la carpeta `dist\GestionTareasMAET` como distribución |
