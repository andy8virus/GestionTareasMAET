# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Gestión de Procesos - Windows x64
# EJECUTAR EN WINDOWS (VM o PC): pyinstaller build_exe.spec
# Usar Python 64-bit para generar .exe x64 compatible con Windows 11.
#
# CustomTkinter requiere --onedir (no --onefile) porque incluye assets (.json, .otf)

import os
import customtkinter

ctk_dir = os.path.dirname(customtkinter.__file__)

block_cipher = None

a = Analysis(
    ['gestion_tareas.py'],
    pathex=[],
    binaries=[],
    datas=[
        (ctk_dir, 'customtkinter'),
    ],
    hiddenimports=[
        'PIL',
        'PIL._tkinter_finder',
        'customtkinter',
        'darkdetect',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GestionProcesos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Cambiar a True para ver errores en consola
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GestionProcesos',
)
