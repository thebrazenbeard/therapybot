$ErrorActionPreference = 'Stop'
$InvocationDirectory = (Get-Location).ProviderPath
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))

$Mode = 'run'
$OfflineWheels = $null
$AppArgs = @($args)
# Keep all unfamiliar arguments untouched, including --model-url and --no-browser.
if ($AppArgs.Count -gt 0) {
    switch ($AppArgs[0]) {
        '-Setup' { $Mode = 'setup'; $AppArgs = @($AppArgs | Select-Object -Skip 1) }
        '-Check' { $Mode = 'check'; $AppArgs = @($AppArgs | Select-Object -Skip 1) }
        '-SetupOffline' {
            $Mode = 'setup-offline'
            if ($AppArgs.Count -ne 2) { throw 'Usage: -SetupOffline PATH' }
            $OfflineWheels = $AppArgs[1]
            $AppArgs = @()
        }
    }
}
if ($Mode -ne 'run' -and $AppArgs.Count -ne 0) {
    throw 'Setup and check modes do not accept application arguments'
}
if ($Mode -eq 'setup-offline') {
    # Do not let an empty argument silently select the network-capable branch.
    if ([string]::IsNullOrWhiteSpace($OfflineWheels)) { throw 'Usage: -SetupOffline PATH' }
    $wheelCandidate = $OfflineWheels
    if (-not [System.IO.Path]::IsPathRooted($wheelCandidate)) {
        $wheelCandidate = Join-Path $InvocationDirectory $wheelCandidate
    }
    $OfflineWheels = [System.IO.Path]::GetFullPath($wheelCandidate)
    if ($OfflineWheels.StartsWith('\\')) { throw 'Use a local wheel directory, not a network share' }
    if (-not (Test-Path -LiteralPath $OfflineWheels -PathType Container)) {
        throw 'The local wheel directory does not exist'
    }
}

$python = '.\.venv\Scripts\python.exe'
if ($Mode -eq 'setup' -or $Mode -eq 'setup-offline') {
    if (-not (Test-Path $python)) {
        py -3 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create a local Python environment' }
    }
    if ($Mode -eq 'setup-offline') {
        & $python -m pip --isolated install --no-index --find-links $OfflineWheels -r requirements.txt
    } else {
        Write-Host 'One-time setup may contact the Python package index; no model weights are downloaded.'
        & $python -m pip install -r requirements.txt
    }
    if ($LASTEXITCODE -ne 0) { throw 'Local dependency installation failed' }
}

if (-not (Test-Path $python)) {
    throw 'TherapyBot environment missing. Run -Setup once (may use PyPI), or -SetupOffline PATH with local wheels.'
}
& $python launch/preflight.py
if ($LASTEXITCODE -ne 0) { throw 'Local Python dependencies failed preflight' }
if ($Mode -ne 'run') {
    Write-Host 'TherapyBot local Python dependencies are ready. Model-server connectivity was not tested.'
    exit 0
}

& $python -m therapybot @AppArgs
if ($LASTEXITCODE -ne 0) { throw 'TherapyBot exited with an error' }
