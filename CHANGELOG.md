# Changelog - MO2 [NoDelete] Tag Generator

Versions are issued by the project's version gate. Written as the change happens (rule 61).

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
