# Production launcher (phase 2): pre-tension calibration D-runs, production decks, then the queue in priority order.
#   powershell -ExecutionPolicy Bypass -File scripts\launch_production.ps1 [-Level M0] [-CalIter 1] [-Ram 2500] [-StallMin 45] [-Fast]
# 1. for each tissue state (relaxed, contracted) and CalIter times: write a D-only deck (D1 + D2) with the current
#    02_Nastran_Model\calib_dT.json, run it, post it, update calib_dT.json (secant on the free-strap ring tension).
# 2. make_production.py (R1..R7, R1V/R2V vented baselines, mesh study MS_M0/M1/M2) with the calibrated dT.
# 3. run_queue.ps1 on 02_Nastran_Model\queue_production.txt (one job at a time, watchdog, post after every run).
param([string]$Level = "M0", [int]$CalIter = 1, [int]$Ram = 2500, [int]$StallMin = 45, [string]$Study = "M1,M2", [switch]$Fast)
$R = Split-Path $PSScriptRoot -Parent
$py = "python"
$calib = Join-Path $R "02_Nastran_Model\calib_dT.json"
$mesh = Join-Path $R "02_Nastran_Model\mesh_$Level.pkl"
if (-not (Test-Path $mesh)) { & $py -P (Join-Path $PSScriptRoot "mesh_a07.py") --level $Level }
foreach ($t in @("relaxed", "contracted")) {
    for ($i = 1; $i -le $CalIter; $i++) {
        $run = "CAL_${t}_$i"
        $d = Join-Path $R "02_Nastran_Model\$run"
        New-Item -ItemType Directory -Force $d | Out-Null
        $extra = @()
        if ($t -eq "relaxed") { $extra = @("--mu_ring", "0.0") }
        & $py -P (Join-Path $PSScriptRoot "deck_a07.py") --mesh $mesh --out (Join-Path $d "$run.nas") --run $run --seq D --tissue $t --calib $calib @extra
        & (Join-Path $PSScriptRoot "run_queue.ps1") -List "02_Nastran_Model\$run\$run.nas" -Ram $Ram -StallMin $StallMin
        $res = Join-Path $R "04_Runs\$run\${run}_results.csv"
        if (Test-Path $res) { & $py -P (Join-Path $PSScriptRoot "calib_a07.py") $res $calib $t 2>&1 | Out-File -Append -Encoding utf8 (Join-Path $R "06_Error_Log\queue_log.txt") }
    }
}
$fa = @(); if ($Fast) { $fa = @("--fast") }
& $py -P (Join-Path $PSScriptRoot "make_production.py") --level $Level --study $Study --calib $calib @fa
& (Join-Path $PSScriptRoot "run_queue.ps1") -ListFile (Join-Path $R "02_Nastran_Model\queue_production.txt") -Ram $Ram -StallMin $StallMin
