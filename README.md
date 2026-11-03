# ZamTab

ZamTab is a desktop statistics application inspired by Minitab 17, built with Python and Tkinter. It includes a spreadsheet-style worksheet, statistical commands, charts, and project files.

## Get the application

Download the source from [GitHub](https://github.com/mursalin-decen/ZamTab):

- **No Git required:** On GitHub, select **Code > Download ZIP**, then extract the ZIP.
- **Using Git:** Run `git clone https://github.com/mursalin-decen/ZamTab.git`, then open the downloaded `ZamTab` folder.

## Windows: easiest setup

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). During installation, enable **Add python.exe to PATH**.
2. Open the extracted `ZamTab` folder.
3. Double-click **ZamTab.bat**.
4. On first launch, the script creates a local `.venv` environment and installs the required packages. This needs an internet connection and can take a few minutes. Later launches open the app directly.

If Windows asks which app to use for a `.bat` file, open it with **Windows Command Processor**. You can also launch from PowerShell in the project folder:

```powershell
.\ZamTab.bat
```

## Linux

Install Python 3, Tkinter, and pip. On Debian or Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-tk python3-venv python3-pip
```

From the project folder, create an environment, install dependencies, and start ZamTab:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

## macOS

Install Python 3.10 or newer with Tkinter support. Open Terminal in the project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

If Python reports that Tkinter is unavailable, install a Python distribution that includes Tk support, then retry.

## Build a standalone Windows app

To build a Windows app folder that can run on a Windows computer without a separate Python installation:

1. Install Python 3.10 or newer on Windows.
2. Double-click **build_exe.bat** in the project folder.
3. When the build completes, find the app at `dist\ZamTab\ZamTab.exe`.
4. Distribute or copy the **entire** `dist\ZamTab` folder; the executable depends on files alongside it.

The first build installs the Python dependencies and PyInstaller and requires an internet connection. This script builds for Windows; it does not deploy ZamTab to Vercel.

## First use

1. Start ZamTab using the instructions above.
2. Load the included example dataset using the **flask button** on the toolbar, or open your own data with **File > Open Worksheet...** (also **Ctrl+O**).
3. Supported input formats include CSV, TSV, TXT, XLS, and XLSX.
4. To enter data yourself, type or paste it into the worksheet. You can paste cells copied from Excel.
5. Double-click a column heading (such as C1 or C2) to rename it.
6. Choose an analysis from the **Stat**, **Graph**, **Calc**, or **Data** menus. Follow the dialog to select columns and options. The **Graph** menu opens a graph gallery.
7. Use the chart toolbar button to open charts that fit the current worksheet. Graph windows can be edited and saved.
8. Save your data as CSV or Excel from the worksheet menu. Save the complete project, including worksheets and session output, using **File > Save Project** (Ctrl+S); projects use the `.zamtab` extension.

Other useful shortcuts: **Ctrl+Z** undo, **Ctrl+Y** redo, **Ctrl+E** edit the last dialog, and **Ctrl+F** find worksheet data.

## Dependencies

The Python package requirements are listed in [`requirements.txt`](requirements.txt): pandas, NumPy, SciPy, Matplotlib, and openpyxl. Tkinter is also required and is included with many Python installations; on Linux it may need to be installed separately (see above).

## Troubleshooting

- **Python not found on Windows:** Re-run the Python installer, enable **Add python.exe to PATH**, and reopen the terminal or rerun `ZamTab.bat`.
- **Package installation failed:** Check your internet connection, then run `ZamTab.bat` again.
- **Tkinter/display error:** Install a Python build with Tk support. Linux users should install `python3-tk`; the app also needs a graphical desktop session.
- **Windows executable does not start on another PC:** Copy the whole `dist\ZamTab` folder, not only `ZamTab.exe`.

## Project structure

```text
ZamTab/
├── assets/           Application icons
├── data/             Example dataset
├── zamtab/           Application interface, worksheet, statistics, and graphs
├── ZamTab.bat        Windows launcher
├── build_exe.bat     Windows standalone-app builder
├── requirements.txt  Python dependencies
└── run.py            Application entry point
```

Some Minitab features, including DOE, Reliability, Multivariate, Time Series, and Assistant, are not implemented yet.
