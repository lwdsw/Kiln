# Make a MacOS DMG

TODO: switch to this. Seems even better: https://github.com/sindresorhus/create-dmg
It's still blocked on that one bug though: https://github.com/sindresorhus/create-dmg/issues/243

- One time: `npm install -g appdmg`
- Copy appdmg.json and the two PNGs to the folder with the Kiln.app
- `appdmg appdmg.json Kiln.dmg`
