@echo off
:: -------- run.bat (Macro Manager) --------
:: 1.  Jump to the folder this script lives in
cd /d "%~dp0"

:: 2.  Use the interpreter on PATH
python -m macro_manager %*

:done
echo --------------------------------------------------
echo  Press any key to close this window …
pause >nul
