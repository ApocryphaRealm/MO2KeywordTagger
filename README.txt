MO2 [NoDelete] Tag Generator
============================
Version 1.0.1

A Mod Organizer 2 plugin: one toolbar button that gives mods Wabbajack's [NoDelete] tag with a
number in list order, and takes it away again. One dialog, one rename pass, one refresh.

THIS IS NOT A MOD. Do not install it with the mod manager.

REQUIREMENTS
------------
Mod Organizer 2 2.5.x (tested on 2.5.2).

INSTALLATION
------------
Copy plugins\MO2NoDeleteTagGenerator.py and plugins\MO2NoDeleteTagGenerator.png into your MO2 folder's
"plugins" folder, next to the other .py plugins, and restart MO2. The button appears on the
toolbar. To remove it, delete the two files.

USE
---
- Select mods and press the button, or put mods under a separator named "NoDelete" and press it
  with nothing selected: every untagged mod there gets the tag, and every tagged mod is renumbered
  in list order ([NoDelete] 0001 Name, 0002 ...).
- Remove tag and number: for the selected tagged mods, or tick "from every tagged mod".
- Plugin type tags ([ESM] [ESP] [ESL]): keep, add from the plugin files, or remove.
- Separators: move tagged mods back under the separator they were tagged under; save the current
  separators as their home.
- The preview lists every rename before Apply; the result shows in the same window.

HOW IT RENAMES
--------------
Folders on disk plus every profile's modlist.txt, then one MO2 refresh - not one MO2 rename per
mod. Every profile list is backed up first to plugins\data\MO2NoDeleteTagGenerator\backups\.

FILES IT WRITES
---------------
Documents\MO2 NoDelete Tag Generator\separator-map.json and log.txt; the backups above.

WHAT CHANGED
------------

Version 1.0.1
A separator is never renamed; 1.0.0 offered to renumber the NoDelete separator itself.

Version 1.0.1
First release.

CREDIT
------
Inspired by Wabbajack NoDelete Automatic Indexer plugin for MO2 by Alfthebigheaded -
https://www.nexusmods.com/site/mods/669 - the [NoDelete]-plus-index idea. No code is shared.

LICENCE
-------
GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See LICENSE, NOTICE.md and THIRD_PARTY_NOTICES.md.
Source: https://github.com/ApocryphaRealm/MO2NoDeleteTagGenerator
