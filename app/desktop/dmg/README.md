# Make a MacOS DMG

TODO: Bring back the background once this is fixed: https://github.com/LinusU/node-appdmg/issues/243

- One time: `npm install -g appdmg`
- Copy appdmg.json and the two PNGs to the folder with the Kiln.app
- `appdmg appdmg.json Kiln.MacOS.Installer.AppleSilicon.M-Processor.dmg`
- `appdmg appdmg.json Kiln.MacOS.Installer.Intel.dmg`
