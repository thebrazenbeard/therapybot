@echo off
setlocal
set "APP_ROOT=%~dp0.."
set "APP_PYTHON=%APP_ROOT%\.venv\Scripts\python.exe"
if not exist "%APP_PYTHON%" (
  echo Missing .venv. Run: py -3 -m venv .venv ^&^& .venv\Scripts\python.exe -m pip install -e .
  exit /b 1
)
"%APP_PYTHON%" -m therapybot %*
