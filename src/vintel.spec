# -*- mode: python -*-

block_cipher = None


a = Analysis(['vintel.py'],
             pathex=['z:\\mark\\code\\vintel\\src'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             cipher=block_cipher)

for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break

a.datas += [('vi/ui/MainWindow.ui', 'vi/ui/MainWindow.ui', 'DATA'),
            ('vi/ui/SystemChat.ui', 'vi/ui/SystemChat.ui', 'DATA'),
            ('vi/ui/ChatEntry.ui', 'vi/ui/ChatEntry.ui', 'DATA'),
            ('vi/ui/Info.ui', 'vi/ui/Info.ui', 'DATA'),
            ('vi/ui/ChatroomsChooser.ui', 'vi/ui/ChatroomsChooser.ui', 'DATA'),
            ('vi/ui/RegionChooser.ui', 'vi/ui/RegionChooser.ui', 'DATA'),
            ('vi/ui/SoundSetup.ui', 'vi/ui/SoundSetup.ui', 'DATA'),
            ('vi/ui/res/qmark.png', 'vi/ui/res/qmark.png', 'DATA'),
            ('vi/ui/res/logo.png', 'vi/ui/res/logo.png', 'DATA'),
            ('vi/ui/res/logo_small.png', 'vi/ui/res/logo_small.png', 'DATA'),
            ('vi/ui/res/logo_small_green.png', 'vi/ui/res/logo_small_green.png', 'DATA'),
            ('vi/ui/res/178028__zimbot__bosun-whistle-sttos-recreated.wav',
             'vi/ui/res/178028__zimbot__bosun-whistle-sttos-recreated.wav', 'DATA'
            ),
            ('vi/ui/res/178031__zimbot__transporterstartbeep0-sttos-recreated.wav',
             'vi/ui/res/178031__zimbot__transporterstartbeep0-sttos-recreated.wav', 'DATA'
            ),
            ('vi/ui/res/178032__zimbot__redalert-klaxon-sttos-recreated.wav',
             'vi/ui/res/178032__zimbot__redalert-klaxon-sttos-recreated.wav', 'DATA'
            ),
            ('vi/ui/res/mapdata/Providencecatch.svg',
             'vi/ui/res/mapdata/Providencecatch.svg', 'DATA'),
            ('docs/jumpbridgeformat.txt', 'docs/jumpbridgeformat.txt', 'DATA'),
            ('vi/ui/JumpbridgeChooser.ui', 'vi/ui/JumpbridgeChooser.ui', 'DATA'),
            ]

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='vintel-1.1.0.exe',
          debug=False,
          strip=None,
          upx=True,
          icon="icon.ico",
          console=False )
