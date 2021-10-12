# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main_flask.py', 'constants.py', 'obj_loader.py', 'webcam.py'],
             pathex=['.'],
             binaries=[],
             datas=[('templates', 'templates'), ('webcam_calibration_ouput.npz', '.'), ('beerbottle_club11.mtl', '.'), ('beerbottle_club11.obj', '.'), 
                    ('club11_logo.jpg', '.'), ('Earth.jpg', '.'), ('Earth.mtl', '.'), ('Earth.obj', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='main_flask',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='main_flask')
