# Production, contracted tissue first (error log E-52, decision D-ORDER, 13 Nov): the relaxed pre-tension (CAL_relaxed_1) does not
# converge (stalls at 60 % of D2), so the contracted runs - which converge (CHK_FAB4) and match the active quadriceps of early
# stance - go first; relaxed runs are attempted at the end of the queue.
#   powershell -ExecutionPolicy Bypass -File scripts\prod_contracted_first.ps1 [-Ram 2500] [-StallMin 45]
# 1. CAL_contracted_1: D-only deck with the current calib_dT.json, run, update calib_dT.json (calib_a07.py, contracted).
# 2. make_production.py --fast --only R1..R7,R1V,R2V (no relaxed mesh study; R1..R7, R1V/R2V with the calibrated dT; production cover = deck_a07 defaults, D-FAB4).
# 3. MS_M1C: mesh study on mesh M1, CONTRACTED tissue, D -> 21 % + VREF (the brief's mesh study uses R1 = relaxed, which does not converge).
# 4. run_queue.ps1 on 02_Nastran_Model\queue_contracted_first.txt.
param([int]$Ram = 2500, [int]$StallMin = 45)
$R = Split-Path $PSScriptRoot -Parent
$py = "python"
$calib = Join-Path $R "02_Nastran_Model\calib_dT.json"
$mesh0 = Join-Path $R "02_Nastran_Model\mesh_M0.pkl"
$mesh1 = Join-Path $R "02_Nastran_Model\mesh_M1.pkl"
$qlog = Join-Path $R "06_Error_Log\queue_log.txt"
function Log([string]$m) { "$(Get-Date -Format s) $m" | Out-File -Append -Encoding utf8 $qlog }
Log "prod_contracted_first: start"
$run = "CAL_contracted_1"
$d = Join-Path $R "02_Nastran_Model\$run"
New-Item -ItemType Directory -Force $d | Out-Null
& $py -P (Join-Path $PSScriptRoot "deck_a07.py") --mesh $mesh0 --out (Join-Path $d "$run.nas") --run $run --seq D --tissue contracted --calib $calib
& (Join-Path $PSScriptRoot "run_queue.ps1") -List "02_Nastran_Model\$run\$run.nas" -Ram $Ram -StallMin $StallMin
$res = Join-Path $R "04_Runs\$run\${run}_results.csv"
if (Test-Path $res) { & $py -P (Join-Path $PSScriptRoot "calib_a07.py") $res $calib contracted 2>&1 | Out-File -Append -Encoding utf8 $qlog }
& $py -P (Join-Path $PSScriptRoot "make_production.py") --level M0 --only "R1,R2,R3,R4,R5,R6,R7,R1V,R2V" --calib $calib --fast 2>&1 | Out-File -Append -Encoding utf8 $qlog
$ms = Join-Path $R "02_Nastran_Model\MS_M1C"
New-Item -ItemType Directory -Force $ms | Out-Null
& $py -P (Join-Path $PSScriptRoot "deck_a07.py") --mesh $mesh1 --out (Join-Path $ms "MS_M1C.nas") --run MS_M1C --opt 2 --plim 20 --tissue contracted --seq D-21 --vref --calib $calib 2>&1 | Out-File -Append -Encoding utf8 $qlog
$q = Join-Path $R "02_Nastran_Model\queue_contracted_first.txt"
@("# contracted first (E-52 / D-ORDER); relaxed runs last",
  "02_Nastran_Model\R2\R2.nas", "02_Nastran_Model\R2V\R2V.nas", "02_Nastran_Model\R4\R4.nas", "02_Nastran_Model\R6\R6.nas",
  "02_Nastran_Model\MS_M1C\MS_M1C.nas",
  "02_Nastran_Model\R1\R1.nas", "02_Nastran_Model\R1V\R1V.nas", "02_Nastran_Model\R3\R3.nas", "02_Nastran_Model\R5\R5.nas",
  "02_Nastran_Model\R7\R7.nas") | Out-File -Encoding ascii $q
Log "prod_contracted_first: queue written $q"
& (Join-Path $PSScriptRoot "run_queue.ps1") -ListFile $q -Ram $Ram -StallMin $StallMin
Log "prod_contracted_first: done"
