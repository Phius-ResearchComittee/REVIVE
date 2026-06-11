# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['.env\\Lib\\site-packages'],
    binaries=[],
    datas=[('json\\help_tree_content.json', '.'), ('help_tree_structure.txt', '.'), ('json\\phius_runlist_options.json', '.'), ('json\\required_columns.json', '.'), ('Phius-Logo-RGB__Color_Icon.ico', '.')],
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
    name='REVIVEcalc25-1-0',
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
    icon=['revive_phius_icon_v24.2.1.ico'],
)
