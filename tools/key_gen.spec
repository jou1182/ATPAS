# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — ATPAS Key Generator (Developer Tool)
# Run: pyinstaller tools/key_gen.spec --noconfirm --clean

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent.resolve()   # tools/../ = project root

block_cipher = None

# All imports explicit — PyArmor hides them from PyInstaller static analysis
hiddenimports = (
    collect_submodules("PyQt5")
    + [
        "pyarmor_runtime_000000",
        "csv", "hashlib", "hmac", "json", "os", "sys", "uuid",
        "webbrowser", "datetime", "typing", "urllib", "urllib.parse",
        "pathlib", "platform", "winreg",
    ]
)

a = Analysis(
    [str(ROOT / "tools" / "key_gen_app.py")],
    pathex=[str(ROOT), str(ROOT / "tools")],
    binaries=[],
    datas=[
        (str(ROOT / "assets" / "fonts" / "Tajawal-Regular.ttf"), "."),
        (str(ROOT / "assets" / "fonts" / "Tajawal Bold.ttf"),    "."),
        (str(ROOT / "assets" / "atpas.ico"),                     "."),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "scipy",
        "IPython", "jupyter", "docx", "openpyxl", "PIL", "lxml",
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
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="ATPAS-KeyGen",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False, upx=True, console=False,
    icon=str(ROOT / "assets" / "atpas.ico"),
    manifest=_dpi_manifest,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[],
    name="ATPAS-KeyGen",
)
