# Inflatable knee actuator – FEA hand-calculation reference (full assembly 10, route a)

SDP-2 (MMNB) soft knee exoskeleton, right leg. Inventor Nastran 2026, SOL 106 (nonlinear static, large displacement,
follower pressure). Report: [`07_Report/FEA_asm10_routeA_HandcalcReference_v3.docx`](07_Report/FEA_asm10_routeA_HandcalcReference_v3.docx)
([PDF](07_Report/FEA_asm10_routeA_HandcalcReference_v3.pdf)).

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

- **Project pressure profile:** 6.89 N·m at 21 % stance. That is α = 0.209, or 104 % of the target (α 0.20 × 33 N·m = 6.60 N·m), as in the final project report D36.
- **Stresses:** factor of safety is 8.5 or more for the bladder and 1.9 or more for the cover, up to 60 kPa.
- **Angle cases that did not reach their angle:** 8.63°, 9.78°, 13°, 16° and 19° stopped while the empty device was being bent (E-150).
- **Option-2 cap:** in `05_Results/Tables/v3_HC/assist_ratio.csv`, `over_cap = yes` means that the device moment is larger than
  the patient's own knee moment at that frame. With the project pressure profile (HCC_PROJ) this is the case at 13–17 %, 20 %, 26 %
  and 28–36 % stance, where the patient's own moment is small; at the 21 % peak the device stays below the cap. At a constant
  40 kPa every window frame is over the cap.

Every number is explained in the report. Every decision is in
`00_Plan_and_Decisions/decisions_2026-11-15.txt`, and every error and non-convergence is in `06_Error_Log/error_log.csv`.

## What you need

| Item | Version used | Note |
|---|---|---|
| Autodesk Inventor Nastran | 2026 (solver `Nastran.exe`, ADS NASTRAN 20.2.0.23) | Licensed software. The decks use Inventor Nastran cards (e.g. BSCONP contact, SLINESTABKSFACT), so other Nastran codes are not tested. |
| Autodesk Inventor | 2026.2 (Build 302298010) | Only to open the CAD in `01_CAD_copy/`; not needed to re-run. |
| Windows + PowerShell | Windows 11 Home, Windows PowerShell 5.1 | Needed for `run_queue.ps1`. |
| Python | 3.14.8 | `pip install -r requirements.txt`: numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.2, openpyxl 3.1.5, python-docx 1.2.0. These are the versions used; others were not tested. |
| bash | Git Bash (Git for Windows 2.55.0) | Needed for `make_decks_v3.sh`; you can also type its commands by hand. |
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
| `01_CAD_copy/` | Inventor CAD of full assembly 10 (reference only, see below) |
| `cad_build_code/` | `geo8.py` + `geo_A150.json`: the code that built the CAD geometry. The mesh is made from it. |
| `02_Nastran_Model/` | Mesh `mesh_M0.pkl`, rigid-leg calibration `calib_rigid.json`, one folder per run with the deck (`.nas`), mesh/step info and seal check; `queue_v3.txt` |
| `04_Runs/<run>/` | Solver log (`.LOG`), post-processed results (`_results.csv/.xlsx`), convergence history, run time. Raw `.OUT/.FNO` are not committed (see below). |
| `05_Results/` | Summary tables (`Tables/v3_HC`) and every report figure (`Images/v3_HC`) |
| `06_Error_Log/` | `error_log.csv` (E-xx) and the queue logs |
| `07_Report/` | Report v3 (Word, and a PDF export of the same file) |
| `scripts/` | Mesh (`mesh_a07.py`), decks (`deck_a07.py`, `make_decks_v3.sh`), seal check, run queue, post-processing, tables, figures, report builder |

### Run names

The final project report (SDP II Final Report D36, Sections 5.4 and 6.3.2, Appendices A and P) uses short names for these
runs. Each one is the same run as the full name used in this repository:

| D36 name | Full run name (folder in this repository) |
|---|---|
| A3 | `CHK_FB` (the 3° case). `HC_A3.0` has the same deck, so it was not run a second time; that is why it is in `_dropped_owner_60kPa/`. |
| A7.3, A8.6, A9.8, A13, A16, A19 | `HC_A7.3`, `HC_A8.6`, `HC_A9.8`, `HC_A13.0`, `HC_A16.0`, `HC_A19.0` |
| C0, C20, C40, C60 | `HCC_P0`, `HCC_P20`, `HCC_P40`, `HCC_P60` |
| CP | `HCC_PROJ` |

| Run | Meaning |
|---|---|
| `CHK_FB` | Fixed angle 3° (same deck as HC_A3.0), 0–60 kPa used |
| `HC_A7.3` … `HC_A19.0` | Fixed angle 7.28°, 8.63°, 9.78°, 13°, 16°, 19° |
| `HCC_P0`, `HCC_P20`, `HCC_P40`, `HCC_P60` | Gait cycle (stance 1–36 %, Option-2 window 13–36 %) at 0 (vented), 20, 40, 60 kPa |
| `HCC_PROJ` | Gait cycle with the project pressure profile (6.9 kPa at 13 % → 20 kPa at 21 % → 2.8 kPa at 36 %) |

## Raw solver output (GitHub Release)

The raw Nastran files (`.OUT`, `.FNO`, `.RSF`, console logs: about 3 GB unpacked, 0.88 GB as zips, single files up to 350 MB) are too big for git.
They are attached to the release **`raw-output-v3`** (repository page → *Releases*), with one zip per run: `raw_<run>.zip`.
`RAW_OUTPUT_MANIFEST.txt` lists every zip with its size and SHA-256.

To restore them, unzip each archive **at the repository root**. The paths inside are `04_Runs/<run>/<file>`, so every file
lands next to that run's committed results.

```powershell
# example: one run
Expand-Archive raw_HCC_PROJ.zip -DestinationPath . -Force
```

With the raw files in place you can rerun the post-processing (`python -P scripts/post_a07.py 04_Runs/<run>/<run>.OUT`) and
`figs_hc_v3.py` without `--skip_out`, without running Nastran again. Inside the text output the Windows user name in stored
file paths is replaced by `user_`, which has the same length, so the line layout is unchanged.

## Inventor CAD (`01_CAD_copy/`)

These are the 13 CAD files of full assembly 10 (`full asseymbly 10.iam`, actuator-V11, cover.09, side vents, leg and strap
parts), copied from the project. You don't need them to re-run the FEA, because the mesh is built from `cad_build_code/`.
They are here for reference and need Autodesk Inventor 2026. Author, Designer and Description are set to roles. Inventor
still stores the folder each file was last saved in (the Windows user name in it is replaced by `user_`), so open the
assembly from this folder and Inventor finds the parts beside it. The file names (for example `full asseymbly 10.iam`,
`tupe-16.ipt`, `streches.10.ipt`) are kept exactly as in the project and the report, because the assembly finds its parts by name.

## Superseded and held runs

Besides the 12 runs of the report, `02_Nastran_Model/` and `04_Runs/` also hold every earlier deck and run of this
folder. A run that was solved has its deck, solver log, results CSV and convergence history here, and its raw output in the
release.

| Runs | What they were |
|---|---|
| `B0_*`, `B0C_*` | First reference attempt (full stack on rigid halves), superseded by the core model (report Section 6, E-64…E-71) |
| `B0R_A5.8`, `B1_A5.8`, `B2_A5.8`, `B2m48_A5.8` | Further full-stack variants at 5.8°: decks built, **not run** (no `04_Runs` folder) |
| `CHK_CORE*`, `CHK_STAB1/2`, `CHK_BLEND`, `CHK_BED`, `CHK_END`, `CHK_GAP*`, `CHK_SLV`, `CHK_FAB4` | Check runs that each tested one fix (report Section 6 table, E-108…E-120) |
| `*_attemptN_*` folders in `04_Runs` | Earlier attempts of a run that were stopped or rebuilt (the error log explains each one) |
| `MS3_M1`, `MS3_M2`, `mesh_M1/M2.pkl` | Mesh-study decks on finer meshes M1 / M2 (built, not run) |
| `_held_real_case/`, `REAL_*`, `RC_*` | Real-case decks (soft tissue, straps, friction 0.37), built and sealed, **not run** |
| `_held_core_cycles/`, `_dropped_owner_60kPa/` | Cycle decks held back, and the 80 / 100 kPa decks dropped by the 60 kPa limit |
| `_regen_test/` | Check that the decks rebuild identically |
| `B0_A8.6`, `B0C_P20_attempt1_killed` | Stopped in their first minutes (queue log 03:36 and 00:16 on 16 Nov, E-71 / E-64): no solver log or results, so there is no `04_Runs` folder; the release zip holds only the console log |
| `05_Results/*/v3_B0` | Tables and figures of the superseded B0 attempt |

`scripts/old_versions/` keeps the earlier versions of the scripts that some of these runs were built with. The current
scripts rebuild the 12 report runs identically (see above).

## Notes

- Personal names in the notes are replaced by roles (mechanical lead, biomechanics lead, controls lead). Local paths are
  shown as `<PROJECT>` / `<USER_HOME>` / `<TEMP>`; they only appear in history notes, and the scripts do not use them.
- The patient data (knee angle, healthy and patient knee moment, deficit) come from the team's biomechanics hand-over
  (Option 2, 13–36 % stance window). They are proposed values until the team records them.
- The rounded values follow the final project report D36: target 6.60 N·m (0.20 × 33 N·m), assistance limit α ≤ 0.25.
  The CSV files and the v3 report keep the unrounded values from the waveform (deficit 32.96 N·m and target 6.59 N·m at
  21 % stance; limit 0.254). The results are the same.

## Source of the patient data

The knee-angle and knee-moment waveforms (healthy controls, and the reconstructed limb 2 months after ACL reconstruction)
were digitised from:

C. Büttner, C. Lisee, E. Bjornsen, A. Buck, N. Favoreto, A. Creighton, G. Kamath, J. Spang, J. R. Franz, T. Blackburn, and
B. Pietrosimone, "Bilateral waveform analysis of gait biomechanics presurgery to 12 months following ACL reconstruction
compared to controls," *J. Orthop. Res.*, vol. 43, no. 2, pp. 322–336, 2025, doi:
[10.1002/jor.26001](https://doi.org/10.1002/jor.26001).

They were interpolated to 1 % stance, and the moment was converted from BW·h with a reference height of 1.70 m (body mass
70 kg). Source: the final project report D36, reference [2].

## License

All rights reserved; see [LICENSE](LICENSE).
