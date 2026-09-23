"""MO2 Keyword Tagger - a Mod Organizer 2 plugin.

One toolbar button that gives mods the [NoDelete] tag Wabbajack keeps across list updates, numbered in list order:
whatever is selected, plus every mod under a separator named NoDelete. One dialog shows every rename before it
happens; renames go to the folders and every profile's modlist.txt at once, then one MO2 refresh. Remove the tag and
number the same way. Tagged mods remember the separator they were tagged under and can be moved back.

Copyright (C) 2026 ApocryphaRealm. GPL-3.0-or-later - see LICENSE and NOTICE.md.
"""
__version__ = "1.0.2"

import json
import os
import re
import struct
import threading
import time
from typing import List, Optional, Dict

import mobase

# Qt imports (same as before) Ã¢â‚¬Â¦
try:
    from PyQt6.QtCore import Qt, QTimer, QSize
    from PyQt6.QtGui import QAction, QIcon, QPainter, QColor, QPixmap, QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QToolBar,
        QMessageBox,
        QToolButton,
        QWidget,
        QTreeView,
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QRadioButton,
        QButtonGroup,
        QGroupBox,
        QCheckBox,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QHeaderView,
        QAbstractItemView,
    )
    QT6 = True
except Exception:
    from PyQt5.QtCore import Qt, QTimer, QSize  # type: ignore
    from PyQt5.QtGui import QAction, QIcon, QPainter, QColor, QPixmap, QFont  # type: ignore
    from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QToolBar,
        QMessageBox,
        QToolButton,
        QWidget,
        QTreeView,
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QRadioButton,
        QButtonGroup,
        QGroupBox,
        QCheckBox,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QHeaderView,
        QAbstractItemView,
    )  # type: ignore
    QT6 = False

TAG_PREFIX = "[NoDelete]"
# Match [NoDelete] with optional 4-digit number and optional plugin type tag
# Handles: "[NoDelete] 0055 [ESM] Name", "[NoDelete] 0055 Name", "[NoDelete] Name"
TAG_RE = re.compile(r'^\s*\[NoDelete\]\s*(\d{4}\s*)?(\*\s*)?', re.IGNORECASE)
# Match plugin type tags like [ESM], [ESP], [ESL], [ESM+ESP], [ESP+ESL], etc.
PLUGIN_TYPE_RE = re.compile(r'^\s*\[(ESM|ESP|ESL|ESM\+ESP|ESM\+ESL|ESP\+ESL|ESM\+ESP\+ESL)\]\s*', re.IGNORECASE)
PATCH_TAG = "[Patch]"
PATCH_TAG_RE = re.compile(r'^\s*\[Patch\]\s*', re.IGNORECASE)
_PATCH_WORD = re.compile(r"(?<![a-z])patch(?:es)?(?![a-z])", re.I)
LEADING_NUM_RE = re.compile(r'^\s*\d+\s*[-_ ]*\s*')
LEADING_PERIOD_RE = re.compile(r'^\.+\s*')

# Data folder in Documents (survives Wabbajack reinstalls)
def get_data_folder():
    """The plugin's own folder in Documents: the separator map and the log survive a Wabbajack reinstall there."""
    docs = os.path.expanduser("~/Documents")
    data_folder = os.path.join(docs, "MO2 Keyword Tagger")
    old_folder = os.path.join(docs, "MO2 NoDelete Tag Generator")
    if not os.path.exists(data_folder):
        if os.path.isdir(old_folder):
            import shutil
            shutil.copytree(old_folder, data_folder)          # the separator map carries over from the old name
        else:
            os.makedirs(data_folder)
    return data_folder

# Divider map file path (in Documents folder)
DIVIDER_MAP_FILE = os.path.join(get_data_folder(), "separator-map.json")
# Log file path (in Documents folder)
LOG_FILE = os.path.join(get_data_folder(), "log.txt")


def is_separator(mod_name: str) -> bool:
    """Check if a mod name is a separator/divider."""
    # MO2 separators typically end with _separator
    return mod_name.endswith("_separator")


# THE NODELETE SEPARATOR (the owner, 2026-09-22: "recognize a separator name and tag everything that doesn't already
# have the no delete tag with the no delete tag if it's in a separator called no delete"). A separator whose name,
# without "_separator", spaces, dashes or brackets, reads "nodelete" is the NoDelete separator; every mod between it
# and the next separator is tagged when the button is pressed, whether or not anything is selected.
NODELETE_SEPARATOR_RE = re.compile(r"^[\s\[\]\-_.]*no[\s\-_]*delete[\s\[\]\-_.]*$", re.IGNORECASE)


def is_nodelete_separator(mod_name: str) -> bool:
    if not is_separator(mod_name):
        return False
    base = mod_name[: -len("_separator")]
    return bool(NODELETE_SEPARATOR_RE.match(base))


def mods_under_nodelete_separators(full_order: List[str]) -> List[str]:
    """Every mod that sits under a NoDelete separator, in list order."""
    out: List[str] = []
    inside = False
    for nm in full_order:
        if is_separator(nm):
            inside = is_nodelete_separator(nm)
        elif inside:
            out.append(nm)
    return out


def load_divider_map() -> Dict[str, str]:
    """Load the divider map from JSON file."""
    if os.path.exists(DIVIDER_MAP_FILE):
        try:
            with open(DIVIDER_MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_divider_map(divider_map: Dict[str, str]) -> None:
    """Save the divider map to JSON file."""
    try:
        with open(DIVIDER_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(divider_map, f, indent=2, ensure_ascii=False)
    except:
        pass


def get_base_mod_name(mod_name: str) -> str:
    """Get the base mod name without the [NoDelete] tag, number, plugin type and [Patch] keyword."""
    name = strip_existing_tag(mod_name)
    name = strip_plugin_type_tag(name)
    name = strip_patch_tag(name)
    return strip_leading_numbers(name)


def strip_patch_tag(name: str) -> str:
    """Remove every [Patch] keyword, wherever an older tool put it (MO2 Patch Tagger prefixed it)."""
    out = re.sub(re.escape(PATCH_TAG), "", name, flags=re.I)
    return re.sub(r"\s{2,}", " ", out).strip()


def has_patch_tag(name: str) -> bool:
    return PATCH_TAG.lower() in name.lower()


def says_patch(text: str) -> bool:
    return bool(text) and _PATCH_WORD.search(text) is not None


def read_plugin_description(path: str) -> str:
    """The SNAM description text from a plugin's TES4 header ('' when unreadable) - patches say so there."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
            if len(head) < 24 or head[:4] != b"TES4":
                return ""
            size = struct.unpack("<I", head[4:8])[0]
            data = fh.read(min(size, 4 * 1024 * 1024))
    except OSError:
        return ""
    pos = 0
    while pos + 6 <= len(data):
        sig = data[pos:pos + 4]
        sub = struct.unpack("<H", data[pos + 4:pos + 6])[0]
        pos += 6
        if sig == b"XXXX" and sub == 4:
            real = struct.unpack("<I", data[pos:pos + 4])[0]
            pos += 4
            if pos + 6 > len(data):
                break
            sig = data[pos:pos + 4]
            pos += 6
            sub = real
        payload = data[pos:pos + sub]
        pos += sub
        if sig == b"SNAM":
            return payload.split(b"\x00", 1)[0].decode("cp1252", "replace")
    return ""


def patch_signals(name: str, mod_path: str, categories) -> List[str]:
    """Every reason a mod counts as a patch (from MO2 Patch Tagger): a plugin header that says patch, a plugin file
    name that does, the mod's own name, or the MO2 category Patches. [] when none."""
    reasons = []
    try:
        files = [f for f in os.listdir(mod_path) if f.lower().endswith((".esp", ".esm", ".esl")) and os.path.isfile(os.path.join(mod_path, f))]
    except OSError:
        files = []
    by_header = [f for f in files if says_patch(read_plugin_description(os.path.join(mod_path, f)))]
    by_file = [f for f in files if says_patch(os.path.splitext(f)[0])]
    if by_header:
        reasons.append("header says patch: " + ", ".join(by_header))
    if by_file:
        reasons.append("file name: " + ", ".join(by_file))
    if says_patch(get_base_mod_name(name)):
        reasons.append("mod name")
    try:
        if any(str(c).strip().lower() == "patches" for c in (categories or [])):
            reasons.append("category Patches")
    except Exception:  # noqa: BLE001
        pass
    return reasons


PLUGIN_TYPE_ANY_RE = re.compile(r'\[(ESM|ESP|ESL|ESM\+ESP|ESM\+ESL|ESP\+ESL|ESM\+ESP\+ESL)\]\s*', re.IGNORECASE)


def strip_plugin_type_tag(name: str) -> str:
    """Remove every plugin type tag ([ESM], [ESP], [ESL], combinations) wherever it sits."""
    return re.sub(r"\s{2,}", " ", PLUGIN_TYPE_ANY_RE.sub("", name)).strip()


def existing_plugin_type(name: str) -> str:
    m = PLUGIN_TYPE_ANY_RE.search(name)
    return m.group(1).upper() if m else ""


def get_plugin_flags(file_path: str) -> Dict[str, bool]:
    """
    Read plugin header and detect ESM/ESL flags.

    Plugin header structure:
    - Offset 8: Record flags (4 bytes)
      - Bit 0: Master (ESM) flag
      - Bit 9: ESL flag (0x200)
    """
    extension = os.path.splitext(file_path)[1].lower()
    fp = None
    try:
        fp = open(file_path, 'rb')
        signature = fp.read(4)
        if signature not in (b'TES4', b'TES3'):
            return {'valid': False, 'is_master': False, 'is_esl': False, 'extension': extension}

        fp.seek(8)
        rec_flags = int.from_bytes(fp.read(4), byteorder='little')

        return {
            'valid': True,
            'is_master': bool(rec_flags & 0x00000001),
            'is_esl': bool(rec_flags & 0x00000200),
            'extension': extension,
        }
    except Exception:
        return {'valid': False, 'is_master': False, 'is_esl': False, 'extension': extension}
    finally:
        # Explicitly close the file to release the handle immediately
        if fp is not None:
            try:
                fp.close()
            except:
                pass


def get_mod_plugin_types(mod_path: str) -> str:
    """
    Scan a mod folder for plugins and return a combined type tag.

    Returns empty string if no plugins found, or a tag like:
    - "ESM", "ESP", "ESL", "ESP-ESL"
    - "ESM+ESP", "ESM+ESL", etc. for multiple plugin types
    """
    if not os.path.isdir(mod_path):
        return ""

    plugin_types = set()

    try:
        for root, dirs, files in os.walk(mod_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in ('.esp', '.esm', '.esl'):
                    continue

                file_path = os.path.join(root, file)
                try:
                    info = get_plugin_flags(file_path)

                    is_valid = info.get('valid', False)
                    is_master = info.get('is_master', False)
                    is_esl = info.get('is_esl', False)

                    if ext == '.esl':
                        plugin_types.add('ESL')
                    elif not is_valid:
                        if ext == '.esm':
                            plugin_types.add('ESM')
                        else:
                            plugin_types.add('ESP')
                    elif is_master:
                        plugin_types.add('ESM')
                        if is_esl:
                            plugin_types.add('ESL')
                    else:
                        plugin_types.add('ESP')
                        if is_esl:
                            plugin_types.add('ESL')
                except Exception:
                    # Skip files that can't be read (might be locked or corrupted)
                    continue
    except Exception:
        # If we can't scan the directory at all, return empty string
        return ""

    if not plugin_types:
        return ""

    # Sort for consistent ordering: ESM, ESP, ESL
    order = ['ESM', 'ESP', 'ESL']
    sorted_types = sorted(plugin_types, key=lambda x: order.index(x) if x in order else 99)

    return '+'.join(sorted_types)


def strip_existing_tag(name: str) -> str:
    return TAG_RE.sub("", name).strip()


def strip_leading_numbers(name: str) -> str:
    # Remove leading numbers (e.g., "0042 " or "56 ")
    name = LEADING_NUM_RE.sub("", name).strip()
    # Remove leading periods (e.g., ".56 " -> "56 " or "..." -> "")
    name = LEADING_PERIOD_RE.sub("", name).strip()
    # If there are still leading numbers after removing periods, remove them again
    # This handles cases like ".56 run faster" -> "56 run faster" -> "run faster"
    name = LEADING_NUM_RE.sub("", name).strip()
    # Remove any remaining leading periods
    name = LEADING_PERIOD_RE.sub("", name).strip()
    return name


def format_tag(name: str, pos: int, plugin_type: str = "", patch: bool = False) -> str:
    """A NoDelete name: the tag, the number, then the keyword chain - plugin type first, [Patch] after it (the owner,
    2026-09-23: "the patch keyword added to the end like the esm, esl tags") - then the mod's own name."""
    seq = f"{pos:04d}"
    chain = (f"[{plugin_type}] " if plugin_type else "") + (f"{PATCH_TAG} " if patch else "")
    return f"{TAG_PREFIX} {seq} {chain}{name}"


def format_plain(name: str, patch: bool, plugin_type: str = "") -> str:
    """A name outside NoDelete: the keyword chain - plugin type, then [Patch] - then the mod's own name. The plugin
    type tags are independent of NoDelete (the owner, 2026-09-23), the same as [Patch]."""
    chain = (f"[{plugin_type}] " if plugin_type else "") + (f"{PATCH_TAG} " if patch else "")
    return f"{chain}{name}"


def make_fallback_icon() -> QIcon:
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor("#1b6ef3"))
    painter.setPen(QColor("#0d3a86"))
    painter.drawRoundedRect(1, 1, 30, 30, 6, 6)
    font = QFont()
    font.setBold(True)
    font.setPointSize(12)
    painter.setFont(font)
    painter.setPen(Qt.GlobalColor.white)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "ND")
    painter.end()
    return QIcon(pix)


class KeywordDialog(QDialog):
    """The one window (the owner, 2026-09-22: "make it use one main popup and not the successive windows popup").

    Everything the button used to ask in a chain of message boxes is on this dialog: the action, the plugin-type
    tags, the separator map, a live preview of every rename, and Apply. Results land in the status line of the
    same window."""

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self._p = plugin
        self.setWindowTitle("MO2 Keyword Tagger")
        self.resize(980, 680)
        self._build()
        self.refresh_state()

    # ---- layout -----------------------------------------------------------------------------------------------
    def _build(self):
        root = QVBoxLayout(self)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        row = QHBoxLayout()
        act = QGroupBox("Action")
        al = QVBoxLayout(act)
        self.r_tag = QRadioButton("Tag and renumber (selected mods, the NoDelete separator's contents, and every tagged mod's number)")
        self.r_remove = QRadioButton("Remove tag and number")
        self.r_tag.setChecked(True)
        al.addWidget(self.r_tag)
        al.addWidget(self.r_remove)
        self.c_remove_all = QCheckBox("from every tagged mod, not only the selected ones")
        al.addWidget(self.c_remove_all)
        row.addWidget(act, 3)

        pt = QGroupBox("Keyword tags ([ESM] [ESP] [ESL] and [Patch])")
        pl = QVBoxLayout(pt)
        pl.addWidget(QLabel("Plugin type ([ESM] [ESP] [ESL]) - every mod in the list, tagged or not:"))
        self.r_pt_keep = QRadioButton("Keep as they are")
        self.r_pt_add = QRadioButton("Add / update from the plugin files")
        self.r_pt_strip = QRadioButton("Remove")
        self.r_pt_keep.setChecked(True)
        pt_group = QButtonGroup(pt)
        for w in (self.r_pt_keep, self.r_pt_add, self.r_pt_strip):
            pt_group.addButton(w)
            pl.addWidget(w)
        pl.addWidget(QLabel("[Patch] - every mod in the list, tagged or not:"))
        self.r_patch_keep = QRadioButton("Keep as it is")
        self.r_patch_add = QRadioButton("Add / update where a header, file name, mod name or category says patch")
        self.r_patch_strip = QRadioButton("Remove")
        self.r_patch_keep.setChecked(True)
        patch_group = QButtonGroup(pt)
        for w in (self.r_patch_keep, self.r_patch_add, self.r_patch_strip):
            patch_group.addButton(w)
            pl.addWidget(w)
        row.addWidget(pt, 2)
        root.addLayout(row)

        sep = QGroupBox("Separators")
        sl = QVBoxLayout(sep)
        self.c_restore = QCheckBox()
        self.c_update_map = QCheckBox("Save every tagged mod's current separator as its home")
        sl.addWidget(self.c_restore)
        sl.addWidget(self.c_update_map)
        root.addWidget(sep)

        self.preview_label = QLabel()
        root.addWidget(self.preview_label)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Now", "After"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        self.status = QLabel()
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.b_apply = QPushButton("Apply")
        self.b_close = QPushButton("Close")
        buttons.addWidget(self.b_apply)
        buttons.addWidget(self.b_close)
        root.addLayout(buttons)

        for w in (self.r_tag, self.r_remove, self.c_remove_all, self.r_pt_keep, self.r_pt_add, self.r_pt_strip,
                  self.r_patch_keep, self.r_patch_add, self.r_patch_strip, self.c_restore, self.c_update_map):
            w.toggled.connect(self.refresh_preview)
        self.b_apply.clicked.connect(self.apply)
        self.b_close.clicked.connect(self.close)

    # ---- state ------------------------------------------------------------------------------------------------
    def refresh_state(self):
        """Read the list and the selection again (after an apply, too) and rebuild the preview."""
        st = self._p.read_state()
        self._st = st
        self.summary.setText(
            f"{len(st['full_order'])} entries in the list - {len(st['tagged'])} carry [NoDelete] - {len(st['patched'])} carry [Patch] - {len(st['typed'])} carry a plugin-type tag - "
            f"{len(st['sel'])} selected - {len(st['sep_all'])} under a NoDelete separator "
            f"({len(st['sep_untagged'])} of them untagged)"
            + ("" if st['sep_all'] or st['has_sep'] else " - no separator named NoDelete in the list"))
        n_out = len(st["out_of_place"])
        self.c_restore.setText(f"Move tagged mods back under their saved separators ({n_out} out of place)")
        self.c_restore.setEnabled(n_out > 0)
        if n_out == 0:
            self.c_restore.setChecked(False)
        self.refresh_preview()

    def options(self):
        pt = "add" if self.r_pt_add.isChecked() else "remove" if self.r_pt_strip.isChecked() else "keep"
        patch = "add" if self.r_patch_add.isChecked() else "remove" if self.r_patch_strip.isChecked() else "keep"
        return {
            "action": "remove" if self.r_remove.isChecked() else "tag",
            "remove_all": self.c_remove_all.isChecked(),
            "plugin_types": pt,
            "patch": patch,
            "restore": self.c_restore.isChecked(),
            "update_map": self.c_update_map.isChecked(),
        }

    def refresh_preview(self, *_):
        o = self.options()
        self.c_remove_all.setEnabled(o["action"] == "remove")
        for w in (self.r_pt_keep, self.r_pt_add, self.r_pt_strip):
            w.setEnabled(True)                       # independent of the NoDelete action, like [Patch] (2026-09-23)
        pairs = self._p.plan(self._st, o)
        self._pairs = pairs
        self.table.setRowCount(len(pairs))
        for i, (old, new) in enumerate(pairs):
            self.table.setItem(i, 0, QTableWidgetItem(old))
            self.table.setItem(i, 1, QTableWidgetItem(new))
        moves = len(self._st["out_of_place"]) if o["restore"] else 0
        what = []
        if pairs:
            what.append(f"{len(pairs)} rename(s)")
        if moves:
            what.append(f"{moves} move(s) back under saved separators")
        if o["update_map"]:
            what.append("separator map saved")
        self.preview_label.setText("Apply will do: " + (", ".join(what) if what else "nothing - the list is already as asked"))
        self.b_apply.setEnabled(bool(what))
        # the Action radios and the plugin-type radios concern NoDelete; the [Patch] radios work on every mod
        for w in (self.r_patch_keep, self.r_patch_add, self.r_patch_strip):
            w.setEnabled(True)

    def apply(self):
        o = self.options()
        pairs = list(self._pairs)
        self.b_apply.setEnabled(False)
        self.status.setText("Working...")
        QApplication.processEvents()
        try:
            lines = self._p.execute(self._st, o, pairs)
        except Exception as exc:  # noqa: BLE001
            self._p._log(f"apply failed: {exc!r}")
            lines = [f"Failed: {exc}"]
        self.refresh_state()
        self.status.setText("\n".join(lines))


class KeywordTagger(mobase.IPluginTool):
    def __init__(self):
        super().__init__()
        self._organizer: Optional[mobase.IOrganizer] = None
        self._parent_widget: Optional[QWidget] = None
        self._toolbar_action = None
        self._btn: Optional[QToolButton] = None
        self._main_window: Optional[QMainWindow] = None

        self._inject_timer = QTimer()
        self._inject_timer.setInterval(500)
        self._inject_timer.timeout.connect(self._attempt_toolbar_injection)
        self._inject_timer.start()


        self._log("Plugin __init__")

    def init(self, organizer: mobase.IOrganizer) -> bool:
        self._organizer = organizer
        self._log("init called")

        # DON'T register callbacks - only update when button is pressed
        # This prevents crashes when dragging mods

        return True

    def name(self) -> str:
        return "MO2 Keyword Tagger"

    def author(self) -> str:
        return "ApocryphaRealm"

    def description(self) -> str:
        return ("Keyword tags for mod names in one dialog: [NoDelete] with a number for the selected mods and everything under "
                "a separator named NoDelete, the plugin-type tags [ESM] [ESP] [ESL], and [Patch] for every mod that is a "
                "patch (header, file name, mod name or category). One on-disk rename pass, one refresh; removes them the same way.")

    def version(self) -> mobase.VersionInfo:
        major, minor, patch = (int(x) for x in __version__.split("."))
        return mobase.VersionInfo(major, minor, patch, mobase.ReleaseType.FINAL)

    def isActive(self) -> bool:
        return True

    def settings(self) -> List[mobase.PluginSetting]:
        return []

    def displayName(self) -> str:
        return "MO2 Keyword Tagger"

    def tooltip(self) -> str:
        return "Keyword tags: [NoDelete] and its number, [ESM] [ESP] [ESL], and [Patch] - add, update or remove"

    def icon(self) -> QIcon:
        here = os.path.dirname(__file__)
        p = os.path.join(here, "MO2KeywordTagger.png")
        if os.path.exists(p):
            return QIcon(p)
        return make_fallback_icon()

    def setParentWidget(self, widget: QWidget) -> None:
        self._parent_widget = widget

    def display(self) -> None:
        """The toolbar button: one dialog for everything (1.3)."""
        self._log("=" * 60)
        self._log("display() invoked")
        if not self._organizer:
            return
        try:
            dlg = KeywordDialog(self, self._parent_widget)
            dlg.exec()
        except Exception as e:
            import traceback
            self._log(f"Error in display: {e}\n{traceback.format_exc()}")
            QMessageBox.warning(self._parent_widget, "Keyword Tagger Error", f"Error: {e}")

    # ---- the facts the dialog works from ----------------------------------------------------------------------
    def read_state(self) -> dict:
        ml = self._organizer.modList()
        try:
            full_order = list(ml.allModsByProfilePriority())
        except Exception:
            full_order = list(ml.allMods())
        sel = self._get_selected_mods_from_ui()
        # A separator is never renamed: the NoDelete separator itself is named "[NoDelete]" and must stay exactly that
        # (1.0.1 - the 1.0.0 preview offered "[NoDelete]_separator -> [NoDelete] 0001 _separator").
        tagged = [nm for nm in full_order if nm.lower().startswith(TAG_PREFIX.lower()) and not is_separator(nm)]
        patched = [nm for nm in full_order if has_patch_tag(nm) and not is_separator(nm)]
        typed = [nm for nm in full_order if existing_plugin_type(nm) and not is_separator(nm)]
        sep_all = mods_under_nodelete_separators(full_order)
        sep_untagged = [nm for nm in sep_all if not nm.lower().startswith(TAG_PREFIX.lower())]
        has_sep = any(is_nodelete_separator(nm) for nm in full_order)
        # tagged mods that sit under a different separator than the one saved for them
        divider_map = load_divider_map()
        current = {}
        cur = None
        for nm in full_order:
            if is_separator(nm):
                cur = nm
            else:
                current[nm] = cur
        out_of_place = []
        for nm in tagged:
            home = divider_map.get(get_base_mod_name(nm))
            if home and home in full_order and current.get(nm) != home:
                out_of_place.append((nm, home))
        return {"full_order": full_order, "sel": sel, "tagged": tagged, "patched": patched, "typed": typed, "sep_all": sep_all,
                "sep_untagged": sep_untagged, "has_sep": has_sep, "out_of_place": out_of_place,
                "divider_map": divider_map}

    def plan(self, st: dict, o: dict) -> List[tuple]:
        """[(old name, new name)] for the chosen action - nothing is touched here."""
        full_order, tagged, sel = st["full_order"], st["tagged"], st["sel"]
        ml = self._organizer.modList()

        def ptype_for(nm: str) -> str:
            """The plugin-type tag nm carries after this run, under the plugin-type option."""
            mode = o.get("plugin_types", "keep")
            if mode == "remove":
                return ""
            if mode == "add":
                mod = ml.getMod(nm)
                try:
                    return get_mod_plugin_types(mod.absolutePath()) if mod else existing_plugin_type(nm)
                except Exception:  # noqa: BLE001
                    return existing_plugin_type(nm)
            return existing_plugin_type(nm)

        def patch_for(nm: str, current: bool) -> bool:
            """Whether nm carries [Patch] after this run, under the [Patch] option."""
            if o.get("patch", "keep") == "remove":
                return False
            if o.get("patch", "keep") == "add":
                if current:
                    return True
                mod = ml.getMod(nm)
                if mod is None:
                    return False
                try:
                    return bool(patch_signals(nm, mod.absolutePath(), mod.categories()))
                except Exception:  # noqa: BLE001
                    return False
            return current

        if o["action"] == "remove":
            chosen = [nm for nm in sel if nm in tagged]
            if o["remove_all"] or not chosen:
                chosen = list(tagged)
            pairs = []
            for nm in chosen:
                base = get_base_mod_name(nm)
                new = format_plain(base, patch_for(nm, has_patch_tag(nm)), ptype_for(nm))
                if base and new != nm:
                    pairs.append((nm, new))
            done = {old for old, _ in pairs}
            if o.get("patch", "keep") != "keep" or o.get("plugin_types", "keep") != "keep":
                for nm in full_order:
                    if is_separator(nm) or nm in done or nm.lower().startswith(TAG_PREFIX.lower()):
                        continue
                    new = format_plain(strip_patch_tag(strip_plugin_type_tag(nm)), patch_for(nm, has_patch_tag(nm)), ptype_for(nm))
                    if new != nm:
                        pairs.append((nm, new))
            return pairs
        newly = [nm for nm in full_order if (nm in sel or nm in st["sep_untagged"]) and nm not in tagged
                 and not is_separator(nm)]
        to_process = [nm for nm in full_order if nm in tagged or nm in newly]
        pairs = []
        for i, nm in enumerate(to_process, start=1):
            base = get_base_mod_name(nm)
            existing = ""
            m = re.match(r'^\[NoDelete\]\s*\d{4}\s+(?:\[(ESM|ESP|ESL|ESM\+ESP|ESM\+ESL|ESP\+ESL|ESM\+ESP\+ESL)\]\s+)?', nm, re.IGNORECASE)
            if m and m.group(1):
                existing = m.group(1)
            ptype = ptype_for(nm)
            new = format_tag(base, i, ptype, patch_for(nm, has_patch_tag(nm)))
            if new != nm:
                pairs.append((nm, new))
        # the plugin-type and [Patch] keywords on every other mod in the list, as a prefix chain
        if o.get("patch", "keep") != "keep" or o.get("plugin_types", "keep") != "keep":
            handled = set(to_process)
            for nm in full_order:
                if is_separator(nm) or nm in handled:
                    continue
                new = format_plain(strip_patch_tag(strip_plugin_type_tag(nm)), patch_for(nm, has_patch_tag(nm)), ptype_for(nm))
                if new != nm:
                    pairs.append((nm, new))
        return pairs

    def execute(self, st: dict, o: dict, pairs: List[tuple]) -> List[str]:
        """Do what the preview showed; returns the lines for the dialog's status."""
        lines = []
        ml = self._organizer.modList()
        # the separator each newly tagged mod sits under is remembered as its home (the old divider map)
        if o["action"] == "tag":
            dm = dict(st["divider_map"])
            cur = None
            added = 0
            for nm in st["full_order"]:
                if is_separator(nm):
                    cur = nm
                elif cur and any(nm == old for old, _ in pairs) and get_base_mod_name(nm) not in dm:
                    dm[get_base_mod_name(nm)] = cur
                    added += 1
            if added:
                save_divider_map(dm)
                lines.append(f"Remembered the separator of {added} newly tagged mod(s).")
        if pairs:
            lines.append(self.rename_on_disk(pairs).strip())
        if o["restore"] and st["out_of_place"]:
            lines.append(self.restore_positions(st["out_of_place"]))
        if o["update_map"]:
            lines.append(self.update_divider_map())
        if not lines:
            lines.append("Nothing to do.")
        return lines

    def restore_positions(self, out_of_place: List[tuple]) -> str:
        """Move each listed tagged mod to the end of its saved separator's block."""
        ml = self._organizer.modList()
        moved = failed = 0
        for nm, home in out_of_place:
            try:
                full_order = list(ml.allModsByProfilePriority())
            except Exception:
                full_order = list(ml.allMods())
            if nm not in full_order or home not in full_order:
                failed += 1
                continue
            start = full_order.index(home)
            target = start + 1
            for i in range(start + 1, len(full_order)):
                if is_separator(full_order[i]):
                    break
                target = i + 1
            try:
                ml.setPriority(nm, target)
                moved += 1
                self._log(f"restored {nm} under {home} (priority {target})")
            except Exception as exc:
                self._log(f"restore failed for {nm}: {exc}")
                failed += 1
            QApplication.processEvents()
        return f"Moved {moved} mod(s) back under their saved separators" + (f"; {failed} failed." if failed else ".")

    def update_divider_map(self) -> str:
        ml = self._organizer.modList()
        try:
            full_order = list(ml.allModsByProfilePriority())
        except Exception:
            full_order = list(ml.allMods())
        dm = {}
        cur = None
        for nm in full_order:
            if is_separator(nm):
                cur = nm
            elif cur and nm.lower().startswith(TAG_PREFIX.lower()):
                dm[get_base_mod_name(nm)] = cur
        save_divider_map(dm)
        return f"Separator map saved for {len(dm)} tagged mod(s)."

    def rename_on_disk(self, pairs: List[tuple]) -> str:
        """Rename mods the fast way (the owner, 2026-09-22: "add the tag and number in the file and auto refresh
        instead of going one at a time"): rename the folders, rewrite every profile's modlist.txt, then ONE MO2
        refresh - the method MO2 Patch Tagger uses, after 350 renameMod() calls timed MO2 out. pairs = [(old, new)]."""
        org = self._organizer
        ml = org.modList()
        mods_dir = org.modsPath()
        profiles_dir = os.path.join(org.basePath(), "profiles")
        before = {}
        for old, _new in pairs:
            try:
                before[old] = ml.priority(old)
            except Exception:
                before[old] = None
        org.refresh(True)   # let MO2 write anything pending first, so the lists on disk are current
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup_dir = os.path.join(org.basePath(), "plugins", "data", "MO2KeywordTagger", "backups", stamp)
        profiles = []
        for prof in sorted(os.listdir(profiles_dir)):
            lst = os.path.join(profiles_dir, prof, "modlist.txt")
            if os.path.isfile(lst):
                os.makedirs(os.path.join(backup_dir, prof), exist_ok=True)
                with open(lst, "rb") as src, open(os.path.join(backup_dir, prof, "modlist.txt"), "wb") as dst:
                    dst.write(src.read())
                profiles.append(lst)
        renamed, failed = [], []
        for old, new in pairs:
            if old == new:
                continue
            src, dst = os.path.join(mods_dir, old), os.path.join(mods_dir, new)
            try:
                if not os.path.isdir(src):
                    failed.append((old, "folder not found"))
                    continue
                if os.path.exists(dst) and src.lower() != dst.lower():
                    failed.append((old, "target name already exists"))
                    continue
                os.rename(src, dst)
                renamed.append((old, new))
            except OSError as exc:
                failed.append((old, str(exc)))
        by_lower = {old.lower(): new for old, new in renamed}
        touched = 0
        for lst in profiles:
            text = open(lst, "rb").read().decode("utf-8-sig")
            nl = "\r\n" if "\r\n" in text else "\n"
            out, changed = [], 0
            for line in text.split(nl):
                if line[:1] in "+-" and line[1:].lower() in by_lower:
                    out.append(line[0] + by_lower[line[1:].lower()])
                    changed += 1
                else:
                    out.append(line)
            if changed:
                open(lst, "wb").write(nl.join(out).encode("utf-8"))
                touched += 1
        org.refresh(True)   # one refresh: MO2 re-reads the mods folder and the profile lists from disk
        moved = []
        for old, new in renamed:
            try:
                after = ml.priority(new)
            except Exception:
                after = None
            if before.get(old) is not None and after != before[old]:
                moved.append(f"{new}: {before[old]} -> {after}")
        self._log(f"renamed {len(renamed)} of {len(pairs)} on disk, {touched} profile list(s) updated, backups in {backup_dir}"
                  + (f" | failed: {'; '.join(f'{n} ({e})' for n, e in failed)}" if failed else "")
                  + (f" | PRIORITY CHANGED: {'; '.join(moved)}" if moved else " | every renamed mod kept its priority"))
        return (f"Renamed {len(renamed)} of {len(pairs)} mod(s); {touched} profile list(s) updated.\n"
                + (f"{len(failed)} could not be renamed (see the log).\n" if failed else "")
                + (f"{len(moved)} changed priority - see the log and the backups in plugins\\data\\MO2KeywordTagger\\backups.\n"
                   if moved else "Every renamed mod kept its place in the list.\n"))

    def _get_selected_mods_from_ui(self) -> List[str]:
        sel: List[str] = []
        app = QApplication.instance()
        if not app:
            return sel
        if not self._main_window:
            for w in app.topLevelWidgets():
                if isinstance(w, QMainWindow):
                    self._main_window = w
                    break
        if not self._main_window:
            return sel

        # Get all mod names from MO2 API for validation
        if self._organizer:
            ml = self._organizer.modList()
            try:
                all_mod_names = set(ml.allMods())
            except:
                all_mod_names = set()
        else:
            all_mod_names = set()

        views = self._main_window.findChildren(QTreeView)
        self._log(f"Found {len(views)} TreeView widgets")

        for view in views:
            # Get the object name to identify the correct TreeView
            obj_name = view.objectName()
            self._log(f"  TreeView objectName: '{obj_name}'")

            # Skip if this is not the mod list view
            # The mod list TreeView typically has objectName "modList" or similar
            # We want to skip the downloads list and other views
            if obj_name and "download" in obj_name.lower():
                self._log(f"    Skipping Downloads TreeView")
                continue

            model = view.model()
            if model is None:
                self._log(f"    No model")
                continue
            sm = view.selectionModel()
            if sm is None:
                self._log(f"    No selection model")
                continue
            indexes = sm.selectedRows()
            if not indexes:
                self._log(f"    No selected rows")
                continue

            self._log(f"    Found {len(indexes)} selected rows")
            temp_sel = []
            for idx in indexes:
                try:
                    val = model.data(idx, 0)
                    if isinstance(val, str):
                        self._log(f"      Selected item: '{val}'")
                        # Validate this is actually a mod name
                        if all_mod_names and val not in all_mod_names:
                            self._log(f"        NOT a valid mod name (archive or other item)")
                        else:
                            self._log(f"        Valid mod name")
                            temp_sel.append(val)
                except Exception as e:
                    self._log(f"      Error getting data: {e}")
                    pass

            if temp_sel:
                # Found valid mod selections in this view - use them
                self._log(f"  Using {len(temp_sel)} validated selections from TreeView '{obj_name}'")
                sel = temp_sel
                break

        if not sel:
            self._log(f"  No valid mod selections found in any TreeView")
        return sel

    def _attempt_toolbar_injection(self):
        if self._toolbar_action:
            self._inject_timer.stop()
            return
        app = QApplication.instance()
        if not app:
            return
        if not self._main_window:
            for w in app.topLevelWidgets():
                if isinstance(w, QMainWindow):
                    self._main_window = w
                    break
        if not self._main_window:
            return
        toolbars = self._main_window.findChildren(QToolBar)
        if not toolbars:
            return
        tb = toolbars[0]

        # Create the action
        act = QAction(self.icon(), self.displayName(), self._main_window)
        act.setToolTip(self.tooltip())
        act.triggered.connect(self.display)

        # Find the Settings action and insert before it
        settings_action = None
        all_actions = tb.actions()

        self._log(f"Toolbar has {len(all_actions)} actions")
        for i, action in enumerate(all_actions):
            text = action.text()
            tooltip = action.toolTip()
            self._log(f"  Action {i}: text='{text}', tooltip='{tooltip}'")
            if "settings" in text.lower() or "settings" in tooltip.lower():
                settings_action = action
                self._log(f"  Found Settings action at position {i}")
                break

        if settings_action:
            # Insert before Settings button
            self._log(f"Inserting Tag NoDelete button before Settings")
            tb.insertAction(settings_action, act)
        else:
            # Try inserting at a specific position (6th position, before Settings typically)
            if len(all_actions) >= 6:
                self._log(f"Settings not found, inserting at position 6")
                tb.insertAction(all_actions[6], act)
            else:
                # Fallback: add to the end
                self._log(f"Fallback: adding to end of toolbar")
                tb.addAction(act)

        self._toolbar_action = act
        btn = tb.widgetForAction(act)
        if isinstance(btn, QToolButton):
            btn.setObjectName("MO2KeywordTaggerBtn")
            # No stylesheet of its own: the button is an ordinary toolbar button drawn by MO2's theme, like every
            # other one (2026-09-22, "no delete button is the wrong color").
            btn.setAutoRaise(True)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            btn.setIconSize(tb.iconSize())

    def _log(self, msg: str):
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except:
            pass


def createPlugin():
    return KeywordTagger()


# --- fault handling (standing rule, 2026-09-23: every MO2 plugin of ours logs and arms faulthandler) ---------------
def _arm_faulthandler():
    """Arm Python's faulthandler once per process, into plugins\\data\\faults.log. When MO2 dies inside C++ with a
    Python slot on the stack, the minidump names only modules; faulthandler writes the Python frames of every
    thread first, so the log names the plugin and the line. Whichever of our plugins loads first arms it."""
    try:
        import faulthandler
        import os
        import time
        if faulthandler.is_enabled():
            return
        here = os.path.abspath(__file__)
        while os.path.basename(here).lower() != "plugins":
            parent = os.path.dirname(here)
            if parent == here:
                return
            here = parent
        path = os.path.join(here, "data", "faults.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fh = open(path, "a", encoding="utf-8")
        who = os.path.basename(os.path.dirname(__file__)) if os.path.basename(__file__) == "__init__.py" else os.path.basename(__file__)
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + " faulthandler armed by " + who + chr(10))
        fh.flush()
        globals()["_FAULT_LOG_HANDLE"] = fh          # kept open for the life of the process
        faulthandler.enable(file=fh, all_threads=True)
    except Exception:  # noqa: BLE001
        pass


_arm_faulthandler()
