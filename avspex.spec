# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Define source and destination paths for data files
added_files = [
    ('src/AV_Spex/config', 'config'),  # Config files
    ('logo_image_files', 'logo_image_files'),  # Logo files
    ('pyproject.toml', '.'),  # Add pyproject.toml to root of bundle
]

a = Analysis(
    ['gui_launcher.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'AV_Spex.av_spex_the_file',
        'AV_Spex.utils.config_manager',
        'AV_Spex.processing.run_tools',
        'AV_Spex.processing.processing_mgmt',
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('your_module')  # Ensure all dependencies are included

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='avspex',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  
    argv_emulation=True,  # Enables opening via Finder
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='avspex'
)

app = BUNDLE(
    coll,
    name='avspex.app',
    icon="av_spex_the_logo.icns",
    bundle_identifier="com.nmaahc.avspex",
    envvars={"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
)

