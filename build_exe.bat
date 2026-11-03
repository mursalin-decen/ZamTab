@echo off
rem Builds a standalone ZamTab.exe (no Python needed on the target PC)
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py -3
if not exist ".venv\Scripts\python.exe" (
  %PY% -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\pyinstaller.exe --noconfirm --noconsole --name ZamTab --icon assets\zamtab.ico --add-data "data;data" --add-data "assets;assets" --hidden-import matplotlib.backends.backend_tkagg run.py
echo.
echo Done. Your program is in: dist\ZamTab\ZamTab.exe  (copy the whole dist\ZamTab folder to share it)
pause
