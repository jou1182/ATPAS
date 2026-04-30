# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — ATPAS Key Generator (Developer Tool)
# Run: cd tools && pyinstaller key_gen.spec --noconfirm --clean

import os
from pathlib import Path

ROOT = Path(SPECPATH).parent.resolve()   # tools/../ = project root

block_cipher = None

a = Analysis(
    [str(ROOT / "tools" / "key_gen_app.py")],
    pathex=[str(ROOT), str(ROOT / "tools")],
    binaries=[],
    datas=[
        # Tajawal fonts
        (str(ROOT / "assets" / "fonts" / "Tajawal-Regular.ttf"), "."),
        (str(ROOT / "assets" / "fonts" / "Tajawal Bold.ttf"),    "."),
        # Icon
        (str(ROOT / "assets" / "atpas.ico"),                     "."),
    ],
    hiddenimports=[
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "hashlib",
        "hmac",
        "json",
        "csv",
        "webbrowser",
        "urllib.parse",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "IPython",
        "jupyter",
        "docx",
        "openpyxl",
        "PIL",
        "lxml",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_dpi_manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"
          xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
  <asmv3:application>
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2, PerMonitor</dpiAwareness>
    </asmv3:windowsSettings>
  </asmv3:application>
</assembly>"""

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ATPAS-KeyGen",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT / "assets" / "atpas.ico"),
    manifest=_dpi_manifest,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ATPAS-KeyGen",
)
