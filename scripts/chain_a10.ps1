# waits until the running queue process ends, then runs the next queue list (one Nastran job at a time, same RAM cap)
param([int]$WaitPid, [string]$ListFile, [int]$Ram = 2000)
$R = Split-Path $PSScriptRoot -Parent
$qlog = Join-Path $R "06_Error_Log\queue_log.txt"
while (Get-Process -Id $WaitPid -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 30 }
"$(Get-Date -Format s) chain: queue PID $WaitPid ended, starting $ListFile" | Out-File -Append -Encoding utf8 $qlog
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run_queue.ps1') -ListFile $ListFile -Ram $Ram -StallMin 45
