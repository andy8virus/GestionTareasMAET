# Depuración de pantalla en blanco

Si el .exe muestra pantallas en blanco al iniciar sesión:

## 1. Ejecutar con consola para ver errores

Edita `build_exe.spec` y cambia:
```python
console=False,
```
por:
```python
console=True,
```

Luego ejecuta: `pyinstaller build_exe.spec`

Al ejecutar el .exe se abrirá una ventana de consola con los errores de Python.

## 2. Probar sin compilar

Ejecuta directamente:
```
python gestion_tareas.py
```

Si funciona con `python` pero no con el .exe, el problema está en el empaquetado.

## 3. Verificar rutas en ejecutable

El .exe debe estar en la misma carpeta que:
- `customtkinter/` (carpeta incluida por PyInstaller)
- `procesos.db` (se crea automáticamente al iniciar)
- `assets/` (para imágenes de fondo, si las usas)

La base de datos y assets se crean junto al .exe en la carpeta `dist/GestionProcesos/`.
