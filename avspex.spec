# avspex.spec

block_cipher = None

a = Analysis(['gui_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/AV_Spex/config', 'AV_Spex/config'),
        ('src/AV_Spex/logo_image_files', 'AV_Spex/logo_image_files'),
        ('pyproject.toml', '.')
    ],
    hiddenimports=[
        'AV_Spex.processing',
        'AV_Spex.utils',
        'AV_Spex.checks'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6.QtDBus', 'PyQt6.QtPdf', 'PyQt6.QtSvg', 'PyQt6.QtNetwork',
        'pandas.io.clipboard', 'pandas.io.excel', 'pandas.io.html', 
        'pandas.io.json', 'pandas.io.sql',
        'plotly.validators', 'plotly.matplotlylib', 'plotly.figure_factory'
    ],
    noarchive=False,
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    runtime_tmpdir=None,
    console=False,
    icon='av_spex_the_logo.icns'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='avspex'
)

app = BUNDLE(coll,
    name='avspex.app',
    icon='av_spex_the_logo.icns',
    bundle_identifier='com.jpc.avspex'
)
