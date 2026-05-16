$ErrorActionPreference = "Stop"

$SkillRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ConfigPath = Join-Path $SkillRoot "reports\dashboard-config.json"

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    @{
        project_path = ""
        refresh_seconds = 15
        port = 8765
    } | ConvertTo-Json | Set-Content -LiteralPath $ConfigPath -Encoding UTF8
}

$Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$Port = if ($Config.port) { [int]$Config.port } else { 8765 }
$Interval = if ($Config.refresh_seconds) { [int]$Config.refresh_seconds } else { 15 }
$Project = if ($Config.project_path) { [string]$Config.project_path } else { "auto dai log Codex" }
$Url = "http://127.0.0.1:$Port/reports/skill-dashboard.html"

$Existing = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*serve_dashboard.py*" -and $_.CommandLine -like "*$Port*" } |
    Select-Object -First 1

if (-not $Existing) {
    Start-Process -FilePath python `
        -ArgumentList "scripts\serve_dashboard.py --port $Port --interval $Interval" `
        -WorkingDirectory $SkillRoot `
        -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

Start-Process $Url
Write-Output "Dashboard: $Url"
Write-Output "Project: $Project"
