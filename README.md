# MO2 [NoDelete] Tag Generator

A Mod Organizer 2 plugin for Wabbajack list users and authors. Wabbajack keeps any mod whose name starts with
`[NoDelete]` when a list updates; this button gives mods that tag, with a number that keeps them in list order, and
takes it away again - all in one dialog, all in one rename pass.

## What the button does

Press it and one window opens:

* **Action** - *Tag and renumber* or *Remove tag and number*. Tagging covers whatever is selected in the mod list
  **and every mod under a separator named NoDelete** (spelled "NoDelete", "No Delete", "[NoDelete]" - any case), and
  renumbers every already-tagged mod so the numbers follow the list: `[NoDelete] 0001 ...`, `0002`, ... Removing
  covers the selected tagged mods, or every tagged mod with one tick.
* **Plugin type tags** - keep, add from the plugin files (`[ESM]`, `[ESP]`, `[ESL]`, `[ESP+ESL]` ...), or remove.
* **Separators** - move tagged mods back under the separator they were tagged under, and save the current
  separators as their home.
* **Preview** - every rename, *Now → After*, updated as you change the options. Apply is disabled when there is
  nothing to do.
* **Apply** - the result appears in the same window.

## How it renames

Not one MO2 rename call per mod (that times MO2 out on a long list). The mod folders are renamed on disk, every
profile's `modlist.txt` is rewritten to match, and MO2 is refreshed once. Every profile list is backed up first to
`plugins\data\MO2NoDeleteTagGenerator\backups\<stamp>\<profile>\modlist.txt`. Each mod keeps its priority; the log says so.

## Installation

Copy `plugins\MO2NoDeleteTagGenerator.py` and `plugins\MO2NoDeleteTagGenerator.png` into your MO2 instance's `plugins` folder and restart MO2. The
button appears on the toolbar (before Settings). To remove it, delete the two files.

## Files it writes

* `Documents\MO2 NoDelete Tag Generator\separator-map.json` - which separator each tagged mod belongs under.
* `Documents\MO2 NoDelete Tag Generator\log.txt` - everything it did.
* `plugins\data\MO2NoDeleteTagGenerator\backups\` - the profile lists before each rename pass.

## Requirements

Mod Organizer 2 2.5.x (tested on 2.5.2). PyQt5 fallback for 2.4 exists but is untested.

## Credits

Inspired by [Wabbajack NoDelete Automatic Indexer plugin for MO2](https://www.nexusmods.com/site/mods/669) by
Alfthebigheaded - the [NoDelete]-plus-index idea. No code is shared. Built on the Mod Organizer 2 plugin API.

## Licence

GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See `LICENSE`, `NOTICE.md` and `THIRD_PARTY_NOTICES.md`.
