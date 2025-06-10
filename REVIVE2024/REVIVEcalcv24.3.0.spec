# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\amitc_crl\\OneDrive\\Documents\\GitHub\\REVIVE\\.venv\\Lib\\site-packages'],
    binaries=[],
    datas=[('help_tree_content.json', '.'), ('help_tree_structure.txt', '.'), ('phius_runlist_options.json', '.'), ('required_columns.json', '.'), ('Phius-Logo-RGB__Color_Icon.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='REVIVEcalcv24.3.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['revive_phius_icon_24.3.0.ico'],
)
