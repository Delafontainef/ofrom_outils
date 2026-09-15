import os
from PyInstaller.utils.hooks import collect_submodules

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_DIR = os.path.abspath(os.path.join(SPEC_DIR, ".."))
MAIN = os.path.join(PROJECT_DIR, "ofrom.pyw")

hiddenimports = collect_submodules("ofrom_outils")

a = Analysis(
    [MAIN],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name="ofrom",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)