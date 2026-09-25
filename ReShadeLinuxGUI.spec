# PyInstaller's PySide6 hooks collect QtCore, QtGui, QtWidgets, and their runtime plugins.
a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[("scripts/reshade-steam-proton.sh", "scripts")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ReShadeLinuxGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ReShadeLinuxGUI",
)
