@echo off
:: -------- run.bat (Macro Manager) --------
:: 1.  Jump to the folder this script lives in
cd /d "%~dp0"

:: 2.  Pick the first interpreter that exists
set "P313=%LocalAppData%\Programs\Python\Python313\python.exe"
set "P311=%LocalAppData%\Programs\Python\Python311\python.exe"

if exist "%P313%" (
    "%P313%" -m streamlit run app.py --server.headless true %*
    goto :done
)

if exist "%P311%" (
    "%P311%" -m streamlit run app.py --server.headless true %*
    goto :done
)

:: Fallback: rely on the launcher if you ever shuffle folders
py -3.13 -m streamlit run app.py --server.headless true %*
if %errorlevel% neq 0 py -3.11 -m streamlit run app.py --server.headless true %*

:done
echo --------------------------------------------------
echo  Press any key to close this window …
pause >nul
