@echo off
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py -3
%PY% --version >nul 2>nul || goto nopython
if exist ".venv\Scripts\pythonw.exe" goto launch
echo First run: setting up ZamTab. This takes 1-3 minutes, please wait...
%PY% -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
:launch
start "" ".venv\Scripts\pythonw.exe" run.py
exit /b
:nopython
echo Python was not found. Install Python 3.10+ from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" during installation. Then double-click ZamTab.bat again.
pause
exit /b
:failed
echo Package installation failed. Check your internet connection and try again.
pause
