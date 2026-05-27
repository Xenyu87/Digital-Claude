$ErrorActionPreference = "Stop"

$Processes = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*serve_dashboard.py*" }

if (-not $Processes) {
    Write-Output "Dashboard server not running."
    exit 0
}

foreach ($Process in $Processes) {
    Stop-Process -Id $Process.ProcessId -Force
    Write-Output "Stopped dashboard server PID $($Process.ProcessId)."
}
