# MO2 Keyword Tagger

A Mod Organizer 2 plugin that manages the keyword tags in mod names from one toolbar button and one dialog:
`[NoDelete]` with a number in list order (Wabbajack's convention for a user's own mods), the plugin-type tags
`[ESM]` `[ESP]` `[ESL]`, and `[Patch]` for every mod that is a patch. One rename pass on disk, one MO2 refresh.

It is the successor of two plugins by the same author, *MO2 [NoDelete] Tag Generator* and *MO2 Patch Tagger*, folded
into one tool (2026-09-23).

## The tag chain

A name carries its keywords as a chain in front of the mod's own name:

```
[NoDelete] 0001 Name [ESM] [Patch]      a NoDelete mod: the tag and number in front, the other keywords after the name
Name [ESP] [Patch]                      any other mod: plugin type, then Patch, after the name
```

`[NoDelete]` and its number are the only prefix; every other keyword is a suffix. Each keyword is independent of
the others - the dialog has a *Keep / Add-update / Remove* row for each, and each row acts on every mod in the list.
Removing a keyword removes only that link; the mod's own name is never touched.

## What the button does

Press it and one window opens:

* **Keyword tags** (top right) - a *Keep / Add-update / Remove* row for each keyword, each independent of the others:
  * `[NoDelete]` and its number: *Add / renumber* covers whatever is selected in the mod list **and every mod under a
    separator named NoDelete** (spelled "NoDelete", "No Delete", "[NoDelete]" - any case), and renumbers every
    already-tagged mod so the numbers follow the list; *Remove* covers the selected tagged mods, or every tagged mod
    with one tick. A separator is never renamed.
  * plugin type: `[ESM]` `[ESP]` `[ESL]` `[ESP+ESL]` ... read from the plugin files, for every mod in the list;
  * `[Patch]`, for every mod in the list: *Add / update* tags a mod when a plugin's header
    description says patch, a plugin's file name does, the mod's own name does, or its MO2 category is Patches;
    existing tags stay. *Remove* strips `[Patch]` everywhere.
* **Separators** - move tagged mods back under the separator they were tagged under; save the current separators as
  their home.
* **Preview** - every rename, *Now → After*, updated as you change the options. Apply is disabled when there is
  nothing to do.
* **Apply** - the result appears in the same window.

## How it renames

Not one MO2 rename call per mod (that times MO2 out on a long list). The mod folders are renamed on disk, every
profile's `modlist.txt` is rewritten to match, and MO2 is refreshed once. Every profile list is backed up first to
`plugins\data\MO2KeywordTagger\backups\<stamp>\<profile>\modlist.txt`. Each mod keeps its priority; the log says so.

## Installation

Copy `plugins\MO2KeywordTagger.py` and `plugins\MO2KeywordTagger.png` into your MO2 instance's `plugins` folder and
restart MO2. The button appears on the toolbar (before Settings). Remove the two files to uninstall. If you had
MO2 [NoDelete] Tag Generator or MO2 Patch Tagger installed, delete their `.py` and `.png` from `plugins` - this one
replaces both.

## Files it writes

* `Documents\MO2 Keyword Tagger\separator-map.json` - the separator each tagged mod calls home (copied from
  `Documents\MO2 NoDelete Tag Generator\` on first run when that folder exists);
* `Documents\MO2 Keyword Tagger\log.txt` - everything it did;
* `plugins\data\MO2KeywordTagger\backups\` - the profile lists before each rename pass;
* `plugins\data\faults.log` - Python's fault handler is armed on start, so a native crash names the plugin and line.

## Requirements

Mod Organizer 2 2.5.x (tested on 2.5.2). PyQt5 fallback for 2.4 exists but is untested. It is not a mod: do not
install it through the mod manager.

## Credits

Inspired by [Wabbajack NoDelete Automatic Indexer plugin for MO2](https://www.nexusmods.com/site/mods/669) by
Alfthebigheaded - the [NoDelete]-plus-index idea. No code is shared. Built on the Mod Organizer 2 plugin API.

## Licence

GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See `LICENSE`, `NOTICE.md` and `THIRD_PARTY_NOTICES.md`.
