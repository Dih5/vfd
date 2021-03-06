# -*- mode: python -*-

block_cipher = None


a = Analysis(['launchgui.py'],
             pathex=['.'],
             binaries=[],
             datas=[('.\\vfd\\img\\*.png', 'vfd\\img'),],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='vfdgui',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon='vfd\\img\\vfdlogo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='vfdwin')
