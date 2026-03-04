# Solución: "No se puede ejecutar esta aplicación en el equipo" (Windows 11)

Este error en Windows 11 Home suele deberse a **incompatibilidad de arquitectura** o a que el .exe se creó en otro sistema operativo.

## Causas frecuentes

### 1. El .exe se compiló en Mac o Linux
**Los ejecutables NO son compatibles entre sistemas.** Un .exe creado en Mac no funciona en Windows. La compilación debe hacerse **en un equipo Windows**.

### 2. Incompatibilidad x64 / ARM64
- **x64 (Intel/AMD)**: La mayoría de PCs con Windows 11.
- **ARM64**: Algunos dispositivos (Surface Pro X, Snapdragon).

Un .exe compilado para x64 no funciona en ARM64 y viceversa.

---

## Soluciones

### Opción A: Ejecutar con Python (la más sencilla)

En el equipo Windows 11:

1. Instala **Python 3.12** desde [python.org](https://www.python.org/downloads/) (marca "Add to PATH").
2. Copia la carpeta `Aplicacion_gestion` al PC.
3. Abre **CMD** o **PowerShell** en esa carpeta:

```cmd
pip install -r requirements.txt
python gestion_tareas.py
```

Con esto la aplicación se ejecuta directamente, sin crear .exe.

---

### Opción B: Compilar el .exe en Windows

**Debe hacerse en el propio equipo Windows donde quieres usarlo** (o en uno con la misma arquitectura).

1. Copia toda la carpeta `Aplicacion_gestion` al PC Windows.
2. Instala Python 3.12 desde [python.org](https://www.python.org/downloads/).
3. Abre CMD o PowerShell en la carpeta:

```cmd
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build_exe.spec
```

4. El .exe estará en: `dist\GestionTareasMAET\GestionTareasMAET.exe`
5. **Importante:** Copia toda la carpeta `dist\GestionTareasMAET`, no solo el .exe. Dentro deben estar también la subcarpeta `customtkinter` y los archivos de datos.

---

### Opción C: Si tu PC es ARM64

Para saber la arquitectura del PC:

1. Presiona **Windows + I** (Configuración).
2. Ve a **Sistema** → **Acerca de**.
3. En "Tipo de sistema" verás: "Equipo basado en x64" o "Equipo basado en ARM".

**Si es ARM64:**
- Compila el .exe en ese mismo equipo (pasos de la Opción B).
- O usa la Opción A (Python directo).

---

## Resumen

| Situación                          | Solución                                              |
|-----------------------------------|--------------------------------------------------------|
| Compilaste en Mac y llevas el .exe a Windows | Compila en Windows o ejecuta con Python en Windows     |
| PC x64, .exe compilado en x64     | Debe funcionar                                         |
| PC ARM64, .exe compilado en x64   | Compila en el PC ARM64 o ejecuta con Python            |
| No quieres compilar               | Usa `python gestion_tareas.py` en Windows              |
