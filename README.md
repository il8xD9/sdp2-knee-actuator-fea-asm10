# Inflatable knee actuator – FEA hand-calculation reference (full assembly 10, route a)

SDP-2 (MMNB) soft knee exoskeleton, right leg. Inventor Nastran 2026, SOL 106 (nonlinear static, large displacement,
follower pressure). Report: [`07_Report/FEA_asm10_routeA_HandcalcReference_v3.docx`](07_Report/FEA_asm10_routeA_HandcalcReference_v3.docx).

> **Idealised reference, not the real device.** The leg is two rigid halves turning about the knee axis, and the bladder
> and cover are bonded to them. There is no soft tissue, no pad, no straps and no friction. These are the assumptions of the
> hand calculation (Model B, M = p·k, k = 206 990 mm³ = 0.207 N·m per kPa). The model checks that formula and the way the
> moment is read from the FEA. It does not give the moment of the real device on a leg. The real case was not run.

## Results in one table

| Case | 20 kPa | 40 kPa | 60 kPa |
|---|---|---|---|
| Knee fixed at 3° – FEA / p·k | 1.06 | 1.06 | 1.08 |
| Knee fixed at 7.28° – FEA / p·k | 1.39 | 1.28 | stopped at ~41 kPa (E-136) |
| Gait cycle, 21 % stance (5.78°) – FEA / p·k | 1.66 | 1.24 | reached 60 kPa at 13 % only (E-133) |
| Assist ratio α = M_dev / patient deficit, 21 % stance | 0.209 | 0.312 | – |

- **Project pressure profile:** 6.89 N·m at 21 % stance. That is α = 0.209, or 105 % of the biomechanics target (α 0.20 = 6.59 N·m).
- **Stresses:** factor of safety is 8.5 or more for the bladder and 1.9 or more for the cover, up to 60 kPa.
- **Angle cases that did not reach their angle:** 8.63°, 9.78°, 13°, 16° and 19° stopped while the empty device was being bent (E-150).

Every number is explained in the report. Every decision is in
`00_Plan_and_Decisions/decisions_2026-11-15.txt`, and every error and non-convergence is in `06_Error_Log/error_log.csv`.

## What you need

| Item | Version used | Note |
|---|---|---|
| Autodesk Inventor Nastran | 2026 (solver `Nastran.exe`, ADS NASTRAN 20.2) | Licensed software. The decks use Inventor Nastran cards (e.g. BSCONP contact, SLINESTABKSFACT), so other Nastran codes are not tested. |
| Windows + PowerShell | Windows 11, PowerShell 5.1 | Needed for `run_queue.ps1`. |
| Python | 3.14 (3.10+ should work) | `pip install -r requirements.txt` |
| bash | Git Bash | Needed for `make_decks_v3.sh`; you can also type its commands by hand. |
| PC | 7.7 GB RAM, 4 cores | One job at a time. Peak solver memory is 1.5–2.7 GB. All 12 runs take about 18 h in total. |

## Redo the simulation – step by step

All commands start from the repository root.

```bash
# 0. get the files
git clone <this repository URL>
cd sdp2-knee-actuator-fea-asm10
pip install -r requirements.txt

# 1. (optional) rebuild the mesh and the 12 decks from the CAD build code
#    The committed decks are already the ones that were run; this step proves it.
#    It overwrites 02_Nastran_Model/<run>/*.nas with identical files.
bash scripts/make_decks_v3.sh --mesh
```

```powershell
# 2. run the solver: one deck at a time; a run is stopped if it makes no load progress for 45 min
powershell -ExecutionPolicy Bypass -File scripts\run_queue.ps1 -ListFile 02_Nastran_Model\queue_v3.txt -Ram 2000 -Np 4 -StallMin 45
#    add  -Exe "<path to Nastran.exe>"  if Inventor Nastran is not in C:\Program Files\Autodesk\Inventor Nastran 2026\Nastran
#    add  -Py  "<path to python.exe>"   if python is not on PATH
#    Each run writes 04_Runs\<run>\ (.OUT, .FNO, .LOG, ...) and post-processes itself into 04_Runs\<run>\<run>_results.csv
```

```bash
# 3. tables and figures
cd scripts
python -P cycle_a10.py --tag v3_HC --ref_cyc HCC --ref_ang HC --p0_load_branch --stance_max 36 --state_flag
python -P assist_a10.py
python -P figs_hc_v3.py            # needs the .OUT/.FNO files from step 2 for the 3D pictures; use --skip_out without them

# 4. report (the builder will not overwrite an existing report: move the committed one away first)
mv ../07_Report/FEA_asm10_routeA_HandcalcReference_v3.docx ../07_Report/committed_v3.docx
python -P build_report_a10_hc.py
```

### How to check that you got the same answer

- Compare your `04_Runs/<run>/<run>_results.csv` with the committed copy (`git diff`). The moments are in the
  `M_knee_ext_Nm` column, in N·m.
- Compare `05_Results/Tables/v3_HC/cycle_moment.csv` and `assist_ratio.csv` with the committed copies.
- Expect the same stops as the original runs. HCC_P60 stops after 13 % stance (E-133). HC_A7.3 stops at about 41 kPa
  (E-136). HC_A8.6–A19.0 stop while the empty device is being bent (E-150). CHK_FB stops at about 70 kPa (E-123); only its
  20–60 kPa steps are used.
- Small differences in the last digits can come from a different solver build or number of processors.

Steps 3 and 4 have already been re-run from this repository's own files (19 Nov 2026). The tables came out identical; the
assist ratio differs only in the 7th digit, from rounding in the waveform CSV. The mesh and all 12 decks were also rebuilt
from the code and came out identical.

## Folder map

| Folder | Content |
|---|---|
| `00_Plan_and_Decisions/` | Briefs, status, decisions (D-A10-*), knee-angle and patient-moment waveform (`waveform_O2_opt1.csv`) |
| `cad_build_code/` | `geo8.py` + `geo_A150.json`: the code that built the CAD geometry. The mesh is made from it. |
| `02_Nastran_Model/` | Mesh `mesh_M0.pkl`, rigid-leg calibration `calib_rigid.json`, one folder per run with the deck (`.nas`), mesh/step info and seal check; `queue_v3.txt` |
| `04_Runs/<run>/` | Solver log (`.LOG`), post-processed results (`_results.csv/.xlsx`), convergence history, run time. Raw `.OUT/.FNO` are not committed (see below). |
| `05_Results/` | Summary tables (`Tables/v3_HC`) and every report figure (`Images/v3_HC`) |
| `06_Error_Log/` | `error_log.csv` (E-xx) and the queue logs |
| `07_Report/` | Report v3 (Word) |
| `scripts/` | Mesh (`mesh_a07.py`), decks (`deck_a07.py`, `make_decks_v3.sh`), seal check, run queue, post-processing, tables, figures, report builder |

### Run names

| Run | Meaning |
|---|---|
| `CHK_FB` | Fixed angle 3° (same deck as HC_A3.0), 0–60 kPa used |
| `HC_A7.3` … `HC_A19.0` | Fixed angle 7.28°, 8.63°, 9.78°, 13°, 16°, 19° |
| `HCC_P0`, `HCC_P20`, `HCC_P40`, `HCC_P60` | Gait cycle (stance 1–36 %, Option-2 window 13–36 %) at 0 (vented), 20, 40, 60 kPa |
| `HCC_PROJ` | Gait cycle with the project pressure profile (6.9 kPa at 13 % → 20 kPa at 21 % → 2.8 kPa at 36 %) |

## Not in this repository

- **Raw solver output** (`.OUT`, `.FNO`, `.RSF`, about 3.3 GB). GitHub rejects files over 100 MB; run step 2 to regenerate them.
- **Inventor CAD files** (`.ipt` / `.iam`). They are not needed to re-run, because the mesh comes from `cad_build_code/`.
  Pictures of the CAD are in `05_Results/Images/v3_HC/cad_*.png`.
- **Superseded runs** of the first reference attempt (B0*, B0C*, CHK_* checks other than CHK_FB) and the real-case decks
  (held, not run). The report's Section 6 and the error log describe them.

## Notes

- Personal names in the notes are replaced by roles (mechanical lead, biomechanics lead, controls lead). Local paths are
  shown as `<PROJECT>` / `<USER_HOME>` / `<TEMP>`; they only appear in history notes, and the scripts do not use them.
- The patient data (knee angle, healthy and patient knee moment, deficit) come from the team's biomechanics hand-over
  (Option 2, 13–36 % stance window). They are proposed values until the team records them.
