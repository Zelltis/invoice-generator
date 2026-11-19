@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto :build_exe

call :find_python
if not defined PY_EXE (
    echo [FEHLER] Es wurde keine kompatible Python-Installation ^(ab Python 3.10^) gefunden.
    echo Bitte installiere Python von https://www.python.org/downloads/ und starte erneut.
    pause
    exit /b 1
)

echo Erstelle virtuelle Umgebung mit %PY_EXE% %PY_ARGS%...
"%PY_EXE%" %PY_ARGS% -m venv .venv
if errorlevel 1 (
    echo [FEHLER] Virtuelle Umgebung konnte nicht erstellt werden.
    pause
    exit /b 1
)

:build_exe
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [FEHLER] Pakete oder PyInstaller konnten nicht installiert werden.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed --name "Rechnungs-Generator" main.py
if errorlevel 1 (
    echo [FEHLER] Build der EXE ist fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo Fertig! Die ausfuehrbare Datei liegt unter: dist\Rechnungs-Generator.exe
pause
exit /b 0

:find_python
set "PY_EXE="
set "PY_ARGS="

call :try_python "py" "-3"
if defined PY_EXE exit /b 0

call :try_python "py" ""
if defined PY_EXE exit /b 0

call :try_python "python" ""
if defined PY_EXE exit /b 0

call :try_python "python3" ""
if defined PY_EXE exit /b 0

for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if not defined PY_EXE if exist "%%~P" (
        call :try_python "%%~P" ""
    )
)
exit /b 0

:try_python
"%~1" %~2 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PY_EXE=%~1"
    set "PY_ARGS=%~2"
)
exit /b 0
