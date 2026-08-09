param(
    [switch]$Development
)

$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"
$powershell = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

$processes = Get-CimInstance Win32_Process
$tradeForgeProcesses = $processes | Where-Object {
    $_.ProcessId -ne $PID -and (
        ($_.Name -eq "python.exe" -and $_.CommandLine -like "*-m uvicorn app.main:app*") -or
        ($_.Name -eq "node.exe" -and (
            $_.CommandLine -like "*standalone/server.js*" -or
            $_.CommandLine -like "*start-production.cjs*" -or
            $_.CommandLine -like "*npm-cli.js start*" -or
            $_.CommandLine -like "*npm-cli.js run dev*"
        ))
    )
}

foreach ($process in $tradeForgeProcesses) {
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

Start-Process -FilePath $powershell -WorkingDirectory $root -WindowStyle Normal -ArgumentList @(
    "-NoLogo",
    "-NoExit",
    "-Command",
    "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
)

$frontendCommand = if ($Development) { "npm.cmd run dev" } else { "npm.cmd start" }
Start-Process -FilePath $powershell -WorkingDirectory $frontend -WindowStyle Normal -ArgumentList @(
    "-NoLogo",
    "-NoExit",
    "-Command",
    $frontendCommand
)

"Trade Forge servers restarted in separate windows. Backend: http://localhost:8000, Frontend: http://localhost:3000"
