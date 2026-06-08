# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files

# --- Pre-build step: Ensure required directories exist ---
for dir_name in ['policies', 'models', 'certs', 'data', 'transfers', 'import']:
    os.makedirs(dir_name, exist_ok=True)
# ---------------------------------------------------------

block_cipher = None

# Collect hidden imports
hidden_imports = (
    collect_submodules('pydantic') +
    collect_submodules('fastapi') +
    collect_submodules('uvicorn') +
    collect_submodules('cryptography') +
    collect_submodules('llama_cpp') + 
    ['pydantic.deprecated.decorator']
)

# CRITICAL FIX: Collect the C++ shared libraries (.so / .dll) required by llama-cpp
llama_binaries = collect_dynamic_libs('llama_cpp')
llama_datas = collect_data_files('llama_cpp')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=llama_binaries, # Instructs PyInstaller to bundle libllama.so / llama.dll
    datas=[
        ('policies', 'policies'),
        ('models', 'models'),
        ('certs', 'certs'),
    ] + llama_datas,
    hiddenimports=hidden_imports,
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
    name='AI_BOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI_BOS',
)