$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Local dependency installation failed' }
& '.\.venv\Scripts\python.exe' -m therapybot @args
if ($LASTEXITCODE -ne 0) { throw 'TherapyBot exited with an error' }
