# Changelog - MO2 Keyword Tagger (formerly MO2 [NoDelete] Tag Generator)

Versions are issued by the project's version gate. Written as the change happens (rule 61).

## 1.0.2 - 2026-09-23

* `[NoDelete]` is the only prefix; the plugin-type tag and `[Patch]` are suffixes after the mod's own name (the
  owner: "i want nodelete to be the only tag that is a prefix, the other tags are suffixes"): `Name [ESP] [Patch]`,
  `[NoDelete] 0001 Name [ESM] [Patch]`. Every keyword is recognised wherever it sits, so names in the older prefix
  form are read and rewritten.
* `[NoDelete]` is a row of the keyword group like the others - *Keep / Add-renumber / Remove* - so any one keyword
  can be chosen on its own (the owner: "add a nodelete tag option ... so you can choose to select only that tag").
  On *Keep*, tagged mods keep their number while the other keywords change.
* The plugin-type tags `[ESM]` `[ESP]` `[ESL]` are independent of `[NoDelete]`, like `[Patch]` (the owner: "it
  shouldn't require me to tag nodelete just to tag it as esm, esl, esp"): *Add / update* tags every mod that ships a
  plugin and *Remove* strips the tag from every mod, whatever its NoDelete state.

## 1.0.1 - 2026-09-23

* Renamed to **MO2 Keyword Tagger** and MO2 Patch Tagger folded in (the owner, 2026-09-23). `[Patch]` is a link of
  the keyword chain - `[NoDelete] 0001 [ESM] [Patch] Name` on a NoDelete mod, `[Patch] Name` on any other - with its
  own Keep / Add-update / Remove radios in the top-right group beside the plugin-type ones, acting on every mod in the
  list. Detection is the Patch Tagger's: a plugin header that says patch, a plugin file name, the mod name, or the MO2
  category Patches. The data folder moves to `Documents\MO2 Keyword Tagger` and carries the old separator map over.
* `version()` reports `__version__`, the number the version gate stamps.
* Arms Python's faulthandler on start (shared `plugins\data\faults.log`), the standing rule for every MO2 plugin of ours.
* A separator is never renamed. 1.0.0 counted the NoDelete separator itself (named `[NoDelete]`) as a tagged mod
  and offered to renumber it into `[NoDelete] 0001 _separator`, which would have broken the separator.

## 1.0.0 - 2026-09-22 - first release

* One toolbar button (the Wabbajack mark) and one dialog: action, plugin-type tags, separator options, a live
  preview of every rename, Apply, and the result in the same window.
* Tags whatever is selected plus every mod under a separator named NoDelete (any spelling of "no delete"), numbered
  in list order: `[NoDelete] 0007 Name`. Already-tagged mods are renumbered so the sequence follows the list.
* Remove Tag and Number - for the selected tagged mods or for every tagged mod - strips `[NoDelete]`, the number
  and any `[ESM] [ESP] [ESL]` tag.
* Renames go to the mod folders and every profile's modlist.txt at once, then one MO2 refresh; every profile list is
  backed up first to `plugins\data\MO2NoDeleteTagGenerator\backups\<stamp>`. No one-mod-at-a-time renames.
* Optional plugin-type tags read from the plugin files; tagged mods remember the separator they were tagged under
  (`Documents\MO2 NoDelete Tag Generator\separator-map.json`) and can be moved back under it.
* No stylesheet of its own: the button is drawn by MO2's theme like every other toolbar button.
