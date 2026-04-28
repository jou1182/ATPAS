# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for ATPAS v2.0
# Run: pyinstaller atpas.spec

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

block_cipher = None

# Collect all PyQt5 plugins needed for Arabic text + Windows look
hiddenimports = (
    collect_submodules('PyQt5')
    + collect_submodules('docx')
    + collect_submodules('lxml')
    + collect_submodules('openpyxl')
    + [
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',
        'docx',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        'PIL',
        'openpyxl',
        'docx2pdf',
        'difflib',
    ]
)

# Data files bundled into the EXE folder
datas = [
    # Config & registry
    ('codes_registry.json',  '.'),
    ('master_config.json',   '.'),
    ('presets.json',         '.'),
    ('version.json',         '.'),   # build stamp — written by build_exe.bat
    # Owner spec JSON files
    ('metadata',             'metadata'),
    # Style templates + source document stubs
    ('templates',            'templates'),
    # Output folder skeleton (empty dirs preserved via .gitkeep)
    ('output',               'output'),
    # Generic assets (icons, fonts)
    ('assets',               'assets'),
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'IPython', 'jupyter'],
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
    name='ATPAS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no black terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/atpas.ico',
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ATPAS',           # → dist/ATPAS/ folder
)
