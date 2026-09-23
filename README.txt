MO2 Keyword Tagger
==================
Version 1.0.1

A Mod Organizer 2 plugin: one toolbar button and one dialog for the keyword tags in mod names -
[NoDelete] with a number in list order (Wabbajack's convention), the plugin-type tags [ESM] [ESP]
[ESL], and [Patch] for every mod that is a patch. One rename pass on disk, one MO2 refresh.
Successor of MO2 [NoDelete] Tag Generator and MO2 Patch Tagger, folded into one tool.

THIS IS NOT A MOD. Do not install it with the mod manager.

THE TAG CHAIN
-------------
[NoDelete] 0001 [ESM] [Patch] Name   a NoDelete mod: tag, number, plugin type, Patch, name
[Patch] Name                         any other mod that is a patch
Removing a keyword removes only that link; the mod's own name is never touched.

REQUIREMENTS
------------
Mod Organizer 2 2.5.x (tested on 2.5.2).

INSTALLATION
------------
Copy plugins\MO2KeywordTagger.py and plugins\MO2KeywordTagger.png into your MO2 folder's "plugins"
folder, next to the other .py plugins, and restart MO2. The button appears on the toolbar. To
remove it, delete the two files. If MO2 [NoDelete] Tag Generator or MO2 Patch Tagger is installed,
delete their .py and .png files - this plugin replaces both.

USE
---
- Action (left): Tag and renumber - select mods and press the button, or put mods under a
  separator named "NoDelete" and press it with nothing selected: every untagged mod there gets
  the tag, and every tagged mod is renumbered in list order. Remove tag and number: for the
  selected tagged mods, or tick "from every tagged mod". A separator is never renamed.
- Keyword tags (top right), two rows of Keep / Add-update / Remove:
  plugin type ([ESM] [ESP] [ESL]) read from the plugin files;
  [Patch] for every mod in the list - added when a plugin header says patch, a plugin file
  name does, the mod name does, or the MO2 category is Patches; existing tags are kept.
- Separators: move tagged mods back under the separator they were tagged under; save the
  current separators as their home.
- The preview lists every rename before Apply; the result shows in the same window.

HOW IT RENAMES
--------------
Folders on disk plus every profile's modlist.txt, then one MO2 refresh - not one MO2 rename per
mod. Every profile list is backed up first to plugins\data\MO2KeywordTagger\backups\.

FILES IT WRITES
---------------
Documents\MO2 Keyword Tagger\separator-map.json and log.txt (the map is copied from
Documents\MO2 NoDelete Tag Generator\ on first run when that exists); the backups above;
plugins\data\faults.log (Python's fault handler, so a crash names the plugin and line).

WHAT CHANGED
------------

Version 1.0.1
MO2 Patch Tagger folded in: [Patch] joins the keyword chain with its own Keep / Add / Remove
radios beside the plugin-type ones, for every mod in the list. Renamed to MO2 Keyword Tagger.
A separator is never renamed (1.0.0 offered to renumber the NoDelete separator itself).

Version 1.0.0
First release, as MO2 [NoDelete] Tag Generator.

CREDIT
------
Inspired by Wabbajack NoDelete Automatic Indexer plugin for MO2 by Alfthebigheaded -
https://www.nexusmods.com/site/mods/669 - the [NoDelete]-plus-index idea. No code is shared.

LICENCE
-------
GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See LICENSE, NOTICE.md and THIRD_PARTY_NOTICES.md.
Source: https://github.com/ApocryphaRealm/MO2KeywordTagger
