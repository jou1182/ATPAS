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
        # PyArmor runtime — required by obfuscated modules (license_manager, activation_dialog, main)
        'pyarmor_runtime_000000',
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
    # PyArmor runtime — تشغيل الملفات المشفَّرة (license_manager, activation_dialog, main)
    ('pyarmor_runtime_000000', 'pyarmor_runtime_000000'),
]

a = Analysis(
    ['main.py'],
    pathex=['.', 'pyarmor_runtime_000000'],
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

# ── Windows DPI Manifest ──────────────────────────────────────────────────
# PerMonitorV2: الحل الصحيح لكل الشاشات — يمنع الضبابية والفيضان
_dpi_manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"
          xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
  <asmv3:application>
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2, PerMonitor</dpiAwareness>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
    </asmv3:windowsSettings>
  </asmv3:application>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
      <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
    </application>
  </compatibility>
</assembly>"""

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
    manifest=_dpi_manifest,  # PerMonitorV2 DPI awareness
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
