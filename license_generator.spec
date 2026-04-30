# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec لأداة توليد كودات الترخيص
# تشغيل: pyinstaller license_generator.spec

block_cipher = None

a = Analysis(
    ['tools/generate_license.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/fonts', 'assets/fonts'),   # خطوط Tajawal
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'utils.license_manager',
        'winreg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy',
        'docx', 'lxml', 'openpyxl', 'PIL',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ATPAS_LicenseGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,           # بدون نافذة سوداء
    onefile=True,            # ملف EXE واحد فقط
    icon='assets/atpas.ico',
)
