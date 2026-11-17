# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for huggingface/pybot -> Windows console pybot.exe.

Layout assumed:
    pybot-build/
      pybot-src/   # shallow clone of https://github.com/huggingface/pybot
      exe/
        pybot.spec          # this file
        build-exe.yml       # GitHub Actions workflow (windows-latest)
        README.md

Run from the exe/ directory:
    pyinstaller pybot.spec --noconfirm

Why --collect-all bot (instead of plain hidden imports):
    bot/runtime.py discovers every module in bot/modules/ at import time via
    pkgutil.iter_modules() + importlib.import_module(). A static analyser
    cannot see those imports, so the whole `bot` package (all 528 .py files,
    ~41 MB of source) must be collected explicitly. collect_all() returns
    the package's datas, binaries and hiddenimports; all three are used.

One-dir (COLLECT), not one-file: pybot takes ~13 s to import all modules on
a Linux VM, longer on first run; a one-file bundle would add extraction of
~100 MB to a temp dir on every start and trips antivirus heuristics more
often. Ship the dist/pybot/ folder (or wrap it with Inno Setup, see README).
"""

import os
import sys

# Resolve paths relative to this spec file, regardless of cwd.
try:
    SPEC_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:  # __file__ not defined when PyInstaller execs the spec
    SPEC_DIR = os.getcwd()
SRC_DIR = os.path.normpath(os.path.join(SPEC_DIR, "..", "pybot-src"))
ENTRY = os.path.join(SRC_DIR, "pybot.py")

# Make the bot package importable so collect_all('bot') can find it.
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from PyInstaller.utils.hooks import collect_all

bot_datas, bot_binaries, bot_hiddenimports = collect_all("bot")

a = Analysis(
    [ENTRY],
    pathex=[SRC_DIR],
    binaries=bot_binaries,
    datas=bot_datas,
    hiddenimports=bot_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pybot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX slows startup on a ~100 MB bundle and raises AV flags
    console=True,  # pybot is a terminal chatbot; it needs a console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="pybot",
)
