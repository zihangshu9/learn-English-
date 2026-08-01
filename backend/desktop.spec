from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


backend_dir = Path(SPECPATH)
frontend_dist = backend_dir.parent / "frontend" / "dist"

analysis = Analysis(
    [str(backend_dir / "run_desktop.py")],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[(str(frontend_dist), "frontend_dist")],
    hiddenimports=collect_submodules("uvicorn"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="拾词学习系统",
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

bundle = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="拾词学习系统",
)
