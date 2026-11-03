# ZamTab - a Minitab 17 style statistics program in Python

## Windows: run
1. Install Python 3.10+ from python.org (tick "Add python.exe to PATH").
2. Double-click **ZamTab.bat** (first run installs packages, 1-3 minutes; after that it opens instantly).

## Windows: standalone .exe
Double-click **build_exe.bat** -> `dist\ZamTab\ZamTab.exe` (copy the whole `dist\ZamTab` folder to any PC).

## Linux / Mac
    pip install -r requirements.txt && python run.py      (Linux: sudo apt install python3-tk)

## How to use
- Type or paste data into the worksheet (Ctrl+V from Excel). Double-click the name row under C1, C2... to name a column.
- Press the chart button on the toolbar: every graph that fits your columns opens and UPDATES LIVE as you change the data.
- Stat / Graph / Calc / Data menus open Minitab-style dialogs (column list, Select, Options..., Graphs..., Storage..., Statistics..., Labels..., Scale...).
- Graph menu shows a gallery first (Simple, With Groups, With Fit, Multiple Y's ...), exactly like Minitab.
- Results go to the Session window in Minitab 17 text format. Each graph has its own window (right-click: Edit Title / Save).
- Ctrl+Z / Ctrl+Y undo/redo, Ctrl+E Edit Last Dialog, Ctrl+F Find, File > Save Project (.zamtab).

## Folder
    ZamTab/  ZamTab.bat  build_exe.bat  run.py  requirements.txt
      assets/  icon     data/sample.csv
      zamtab/  ui.py  commands.py  dialogs.py  sheet.py  stats_ops.py  graphs.py  gallery.py

Greyed menu items (DOE, Reliability, Multivariate, Time Series, Assistant ...) are Minitab features not built yet.
