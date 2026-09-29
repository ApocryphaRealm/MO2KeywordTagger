"""The toolbar button follows the theme (1.0.3; gate rule mo2-plugin-toolbar-icon-follows-the-theme), under PyQt6
offscreen: added before Settings, painted in the colour the stylesheet gives toolbar buttons, repainted when the
stylesheet changes, and put back when MO2 rebuilds its toolbar.

    python tools\\test_toolbar_theme.py        exit 0 = every check passed
"""
import importlib.util, os, sys, types

os.environ["QT_QPA_PLATFORM"] = "offscreen"
stub = types.ModuleType("mobase")
stub.__getattr__ = lambda n: type(n, (object,), {"__init__": lambda self, *a, **k: None})
sys.modules["mobase"] = stub
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar
app = QApplication([])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("kt", os.path.join(HERE, "MO2KeywordTagger.py"))
kt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kt)

bad = 0


def ok(cond, what):
    global bad
    print(("PASS " if cond else "FAIL ") + what)
    bad += 0 if cond else 1


win = QMainWindow()
tb = QToolBar(win)
win.addToolBar(tb)
tb.addAction(QAction("Executables", win))
settings = QAction("Settings", win)
tb.addAction(settings)
win.show()
p = kt.KeywordTagger()
p._inject_timer.stop()                      # driven by hand here
p._main_window = win

app.setStyleSheet("QToolButton { color: #ff0000; }")
p._attempt_toolbar_injection()
acts = tb.actions()
ok(p._toolbar_action in acts and acts.index(p._toolbar_action) == acts.index(settings) - 1, "added before Settings")
ok(p._icon_colour == "#ffff0000", f"painted in the stylesheet's button colour: {p._icon_colour}")

app.setStyleSheet("QToolButton { color: #00ff00; }")
btn = tb.widgetForAction(p._toolbar_action)
btn.setStyleSheet(btn.styleSheet())         # re-polish, as a real theme switch does
app.processEvents()
p._attempt_toolbar_injection()
ok(p._icon_colour == "#ff00ff00", f"a stylesheet change repaints it: {p._icon_colour}")
ok(p._inject_timer.interval() == 2000, "the timer keeps watching (2 s) instead of stopping")

tb.removeAction(p._toolbar_action)          # MO2 rebuilds its toolbar
p._attempt_toolbar_injection()
ok(p._toolbar_action is not None and p._toolbar_action in tb.actions(), "put back after the toolbar dropped it")
print("ALL PASS" if not bad else f"{bad} FAILED")
sys.exit(1 if bad else 0)
