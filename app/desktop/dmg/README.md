# Make a MacOS DMG

Weird node 20 workaround for this: https://github.com/sindresorhus/create-dmg/issues/243

Each time it should just be:

```
create-dmg Kiln.app
# then rename the output dmg to Kiln.MacOS.Intel.dmg or Kiln.MacOS.AppleSilicon.M-Processor.dmg
```

Env Setup while node 20 is required:

- `brew unlink node@23`
- `brew link node@20`
- `npm install -g create-dmg`
- `create-dmg Kiln.app`
- rename the output dmg to Kiln.MacOS.Intel.dmg or Kiln.MacOS.AppleSilicon.M-Processor.dmg
- `brew link node@23`
