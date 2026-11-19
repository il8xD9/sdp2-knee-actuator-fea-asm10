# STATUS - Simulation 2, full asseymbly 07 - phase 1 (build + validate)

Written 13 Nov 2026 01:20-05:30 by the model builder. R = this run folder. The production runs R1..R7 were NOT started in phase 1.
Every problem is in `06_Error_Log\error_log.csv` (E-01 .. E-3x: exact solver message, step, cause, fix, proof).

## 1. What works
| Item | State | Proof |
|---|---|---|
| Geometry | exact CAD build code imported (`geo8.py` + `geo_A150.json`, option A150, asm 07); no numbers copied by hand | `scripts\mesh_a07.py` |
| Structured mesh | tissue hex (bone bores r 15), pad + seats hex (2 layers), rings / closure laminates / hooks / cover flanges / M3 tabs as shells sharing nodes (= bonded), carrier + M3-patch stack hex, bladder closed mid-surface capsule (R9 end rounds, flat caps, flaps to the tabs), cover mid-surface with R11.215 end rounds, Coons end caps and the M3 notch | `02_Nastran_Model\mesh_M*_view.png`, `mesh_quality_M*.csv` |
| Solver features (`04_Runs\solver_test`, mk_t3/t4/t5.py) | BSCONP TYPE 1 (= blank) separation, 3/4 bonded, 5/6 no-separation sliding, 0 inactive; FRIC field 6 active (penalty stick = 1 % of normal); contact results printed by default (per segment + per grid); MAT8 hoop-only thermal shrink works; follower PLOAD4 on shells (+p along +normal, THRU form); MATHP on PSHELL rejected (T2027) -> bladder MAT1 7.2 / 0.49; RBE2 is LINEAR (small rotation) -> bones driven by exact SPCD | E-06..E-13, E-15 |
| Deck `deck_a07.py` | SOL 106 multi-subcase, LGDISP 1, AUTOSPC; shank-bore SPCD = exact rotation about the knee axis (Z through X 4.06, Y 0; flexion + = shank to +X), steps <= 2.5 deg (auto sub-steps); PLOAD4 on all 2052 (M0) bladder shells; per-ring MAT8 cooling (TEMP set 3 = 25 % in D1, set 2 = 100 % from D2); contacts split into spatial patches; NLPARM per subcase (D1 10, D2 20, pressure-rise frames 4, others 2-4 increments, ITER/KSTEP 1, MAXITER 25, MAXBIS 10); option 1/2 windows, 20/27 kPa, relaxed/contracted, pad E, sequence D / D-21 / D-R / FULL / D-SW, VREF vented reference, --vent twin runs | `scripts\deck_a07.py` |
| Queue `run_queue.ps1` | one job at a time, RAM= / NPROCESSORS= / HEXREDORD=OFF on the command line, peak memory + wall time (`04_Runs\<run>\runtime.txt`), watchdog (no load-level progress for -StallMin min -> stop, keep converged subcases), native files moved to `04_Runs\<run>`, FATAL / bisection counts appended to the error log, post after every run | `06_Error_Log\queue_log.txt` |
| Post `post_a07.py` | per subcase: knee moment (shank-bore reactions about the knee axis), thigh reaction, net shank force (ACL), ring tension per loop column (free strap on the skin / back median / min / max), skin pressure mean / peak per zone (under bladder, posterior knee y -40..20, each ring), contact force total, cavity volume, axial slip, pad-skin penetration, max von Mises per part (bladder, cover body, cover flanges, hooks, rings, tabs), ESE, iterations / bisections; device moment vs VREF and vs the vented twin run; CSV + XLSX + history plot + unrolled skin-pressure maps + deformed side views | `04_Runs\SMOKE_K\smoke_K_*` |
| Calibration | `calib_a07.py` secant update of dT per ring on the free-strap tension; `calib_dT.json` keeps the history | |
| Production | `make_production.py` writes R1..R7, R1V/R2V (vented twins) and the mesh-study decks MS_M1/MS_M2 and `02_Nastran_Model\queue_production.txt`; `launch_production.ps1` = calibration D-runs + decks + queue | |

## 2. Modelling choices made in phase 1 (all logged)
- Bones: tissue grids on the bores SPC 123; thigh fixed; shank driven to the exact rigid rotation (RBE2 is linear in this solver, E-11). Knee moment = sum (x - H) x F_spc (identical to R6 of a rigid control node, exact at 78 deg).
- The d30 bore stays open through the 20 mm knee gap (tissue annulus continuous across the gap).
- Shell contact acts on the mid-surface (E-12): rings / flanges / tabs share the pad-top nodes (webbing mid-surface 1.59 mm low); bladder and cover at their true mid-surfaces -> clearances bladder-cover 2.215 mm (physical 1.0) and bladder base-ring 4.18 mm (physical 0); device skin surfaces get 0.05 mm + facet-sagitta interference so the contact is closed at donning.
- Velcro closure + fold-back tail merged with the ring (PSHELL t 7.86, bending ratio 0.139 = three separate layers); M3 carrier + patch = one 4.68 mm hex layer (95 snapped to 96.2); bladder tab = TPU shell on the stack + flap to the bladder base row at |y| 91.4; hook = POM shell t 4 between the webbing ends (hook length snapped to the seat length 62.5 / 37); cover notch across the full cap width (2 mm corners omitted); port D6 and tube omitted.
- Pre-tension: MAT8 A1 = 1e-3 /K along the hoop only (no width shrink, E-13); dT per ring calibrated on the FREE STRAP tension (front, on the skin). Where the cover flanges cross the near rings the ring cooling compresses the flange (artefact, E-29) - flange stresses reported separately.
- Full-integration hexes (HEXREDORD=OFF): the default one-point hexes hourglassed in the soft tissue (E-20).
- Contact penalty (E-21, E-26, E-30, E-36): skin pairs SFAC 0.01 with the solver default penalty scale for both tissue states (SFAC 1 diverges in D1 for relaxed AND contracted; a global INITSLINEKSFACT 1e-3 let the pad sink 6-16 mm); pad-skin penetration ~6 mm median at D2 (contracted, MINI_K) is reported per subcase (pen_pad_*). RELAXED runs: ring-skin frictionless, pad/seat-skin mu 0.37 (deviation from the brief contact table, forced by convergence, E-26). Pad-skin penetration is reported per subcase.
- The tissue annulus across the knee gap gives a passive knee moment (~2.6 N.m/deg contracted, E-28): device moment = total - vented reference (VREF subcase in D-21 runs, vented twin runs R1V/R2V for the full sequences).
- Output: DISPLACEMENT (device + skin grids), SPCFORCES (bores), STRESS / ESE (device shells + stack), STRAIN (bladder + cover), FORCE (rings, hooks, cover), OLOAD (bladder grids), contact tables (default), PARAM GRDPNT 0. GPFORCE not requested (size; ring tension from FORCE), MPCFORCES not applicable (no MPC), INTOUT = NO (each 1 % frame is its own subcase; all-increment output would be several GB).

## 3. Smoke run and checks (M0, D -> 21 %)
**SMOKE_K** (contracted tissue, option 2, 20 kPa, `04_Runs\SMOKE_K`): all 17 subcases converged (6558 s = 1 h 49 min, 631 iterations, 31 bisections, peak RAM 1.9 GB).
| subcase | theta deg | p kPa | knee moment N.m (+ ext.) | cavity cm3 |
|---|---|---|---|---|
| D2 pre-tension | 0 | 0 | +0.12 | 423.8 |
| S1 1 % / 6 % / 12 % | -1.92 / 0.01 / 2.59 | 0 | -4.73 / +0.32 / +6.82 | 423.5-424.2 |
| W 13 % / 17 % / 21 % | 3.28 / 5.29 / 5.78 | 6.9 / 17.8 / 20.0 | 8.53 / 12.76 / 13.90 | 454.1 / 470.0 / 472.9 |
| VREF (vented, 5.78 deg) | 5.78 | 0 | 13.91 | 440.7 |
- Converges: yes. Bladder inflates: yes (+11.5 % cavity at 20 kPa, follower pressure on all bladder shells). Knee moment: non-zero and of the right sign
  for the leg (+ = extension, resisting flexion: -4.7 N.m at -1.9 deg, +13.9 N.m at 5.8 deg = passive tissue bending, ~2.5 N.m/deg, E-28),
  but the DEVICE part at 21 % (moment minus vented reference) is ~0 (-0.006 N.m). First suspicion (E-30/E-34): the soft skin penalty
  (pad 6-16 mm 'into' the skin). Production settings: global penalty scale back to the default, skin SFAC 0.01 (SFAC 1 diverged even
  for the contracted tissue, E-36); the measured pad-skin penetration stays ~6 mm, it is reported per subcase.
- **MINI_K** check (same model, production contact settings: D1, D2, flex vented to 5.78 deg, inflate 20 kPa at
  5.78 deg, VREF), `04_Runs\CHK_MINI_K`, 7/7 converged in 1309 s:
  | state at 5.78 deg | knee moment N.m | cavity cm3 | skin p under bladder mean / peak kPa |
  |---|---|---|---|
  | vented (before) | 14.874 | 424.8 | 1.97 / 13.2 |
  | 20 kPa | 14.703 | 471.8 | 2.02 / 17.8 |
  | vented again (VREF) | 14.630 | 443.1 | 1.94 / 18.3 |
  **Device moment at 21 % = -0.17 N.m (vs vented before) / +0.07 N.m (vs VREF), i.e. ~0, against the hand calculation +4.14 N.m (E-38).**
  This is not a solver failure: with the cover bonded to the pad along its whole length (approved decision; CAD cover.06 flanges run
  over +/-95.9 mm) the bladder pressure is reacted inside bladder + cover + pad at every cross-section (base push and flange pull
  10-20 mm apart), so almost no net moment reaches the bones; the hand calculation F r takes the base force without its cover
  reaction. The pad-skin penalty penetration (~6 mm) may weaken the coupling further. Design values were not changed. **Owner
  decision needed** (e.g. cover anchored only at the strap stations / not sewn over the knee zone) if the FE is to show the intended
  torque path; the production runs still deliver every requested output.

## 4. Calibrated dT (MAT8 A1 = 1e-3 /K, hoop only; target = free-strap tension)
| ring | target N | dT now (contracted) | dT now (relaxed) |
|---|---|---|---|
| thigh near | 20.89 | -87.4 | -30 |
| shank near | 19.59 | -53.3 | -30 |
| thigh far | 13.3 | -36.0 | -30 |
| calf far | 9.4 | -96.6 | -30 |
Contracted: one proportional update from MINI_K D2 (production settings): dT -37.3 / -74.6 / -33.0 / -62.0 gave 8.9 / 27.4 / 12.2 / 6.0 N
(free strap; friction makes the front tension vary 2-3 x round the ring, so the response is noisy). Relaxed: not yet calibrated.
Because the production contact settings differ, `launch_production.ps1` first runs one D-run per tissue state (CAL_relaxed_1,
CAL_contracted_1, ~15-25 min each), updates `calib_dT.json` (proportional / secant) and only then writes the production decks.
Expect +/- 20 % on the ring tensions after one update (check T_*_front_N at D2 of every run; a second -CalIter costs ~40 min).

## 5. Size, RAM and time
| mesh | device h / tissue h (mm) | grids | elements | contact products | status |
|---|---|---|---|---|---|
| M0 (production) | 5 / 10 | 26 777 | 22 636 | 0.27 M (solver ELEMENTS 0.39 M) | run: set-up 2-4 min, ~15 s per Newton iteration, peak 1.9 GB |
| M1 | 4 / 8 | 42 504 | 36 430 | 0.46 M | estimate x1.8 per iteration |
| M2 | 3.4 / 6.8 | 56 371 | 48 377 | 0.71 M | estimate x2.8 per iteration, ~2.5-3 GB (may page) |
Measured on M0: D1 + D2 10-30 min (contracted 14 min; relaxed slower, bisections), stance subcase ~2.5 min, pressurised window
subcase 4-9 min (3-4 bisections each), D -> 21 % + VREF 1 h 49 min (SMOKE_K); MINI_K (D1, D2, 3 flex steps, 0 -> 20 kPa in one
subcase, VREF) 22 min. Output ~14 MB of .OUT per subcase (R1 FULL ~1 GB).
Estimates on M0: R1 FULL (72 subcases) 5.5-7 h; R1 D-R (43) 3.5-4.5 h; R3-R6 D-R 3.5-4.5 h each; R7 / D-21 runs ~2 h;
MS_M1 (D-21) ~3.5 h, MS_M2 ~5.5 h. The whole priority list (~45 h) does NOT fit one night.
**Mesh chosen: M0** - the only level that lets R1 finish overnight on this PC (7.7 GB, ~0.8 GB free); M1/M2 kept for the mesh study
(5 % rule) when time allows. Trade-off: coarse skin pressure peaks (node-area based) and ring pressure lines; the 5 % mesh-convergence
check is not reachable tonight.

## 6. Open issues (all in the error log)
1. RELAXED tissue (G 5.5 kPa): D1 converges with bisections (dH); D2 and the gait sequence are not yet proven - R1 is the first full
   relaxed run. Ring-skin is frictionless in relaxed runs (convergence, E-26); pad-skin friction kept. Watchdog stops a stalled run.
2. MAIN ITEM: device (inflation) knee moment ~0 at 21 % in SMOKE_K and MINI_K (-0.17 / +0.07 N.m vs hand calc 4.14 N.m) - the
   cover bonded along its full length makes the actuator self-reacting (sec. 3, E-34, E-38). Owner decision on the cover anchorage.
3. Passive knee moment of the tissue annulus across the knee gap is of the same order as the device moment -> device moment only
   from (pressurised - vented twin) or VREF. R1V/R2V double the run time of R1/R2.
4. Pad-skin penetration (penalty) ~6 mm median at D2 with SFAC 0.01 - reported (pen_pad_*); skin pressures are force/area
   (equilibrium), positions / moment arms carry this error. A stiffer penalty does not converge in this solver (E-21, E-36).
5. Cover flange stress at the near-ring crossings is a pre-tension artefact (E-29); cover body stress reported separately.
6. Shell contact on mid-surfaces: bladder-cover clearance 2.215 mm (physical 1.0), bladder base-ring 4.18 mm (physical 0).
7. Shells keep the solver default reduced-order quads (QUADREDORD=OFF on the command line has no effect, E-20).
8. Contact output: the per-grid table gives normal / shear force magnitudes only; skin pressure = normal force / tributary area of the
   device-side grid (peaks at edge grids are node-area artefacts - use the zone means and the 95th percentiles in the maps).

## 7. Launch the production (phase 2)
From R (the run folder), in PowerShell (one Nastran job at a time; Inventor may stay open):
```
powershell -ExecutionPolicy Bypass -File scripts\launch_production.ps1 -Level M0 -CalIter 1 -Ram 2500 -StallMin 45
```
Night-fitting variant (R1/R2 + vented twins only to the end of release, 87 %): add `-Fast`.
Queue order (`02_Nastran_Model\queue_production.txt`): R1, R1V, MS_M1, MS_M2, R2, R2V, R3, R5, R7, R4, R6.
Results: `04_Runs\<run>\<run>_results.csv / .xlsx / _history.png / _map_subNN.png / _ring_tension.csv / _convergence.csv`,
`<run>_device_moment.csv` (pressurised minus vented twin), native files in `04_Runs\<run>`; queue log `06_Error_Log\queue_log.txt`.
To post-process again: `C:\Python314\python.exe -P scripts\post_a07.py 04_Runs\R1\R1.OUT`.

## 8. Files
- `scripts\mesh_a07.py` (mesh, quality, render), `deck_a07.py` (deck), `run_queue.ps1` (queue), `post_a07.py` (post), `calib_a07.py`,
  `make_production.py`, `launch_production.ps1`
- `02_Nastran_Model\mesh_M0/M1/M2.pkl`, `mesh_quality_M*.csv`, `mesh_M*_view.png`, `calib_dT.json`, `queue_production.txt`,
  production decks `R1..R7, R1V, R2V, MS_M1, MS_M2` (each with `_info.pkl`, `_steps.csv`, `_mesh.pkl`), `CHK_MINI_K`
- `04_Runs\solver_test` (feature tests mk_t3/t4/t5.py + outputs), `04_Runs\dev`, `04_Runs\dev2` (convergence trials d0, dA..dN),
  `04_Runs\SMOKE_K` (smoke run, results), `04_Runs\CHK_MINI_K` (check)
- `00_Plan_and_Decisions\waveform_O2_opt1.csv` (option-1 waveform from Biomech O2, used for R5/R6)
- `06_Error_Log\error_log.csv`, `queue_log.txt`

## 9. Update 13 Nov 06:05 (after phase 1)
- Cause of the ~0 device moment found (E-39): the cover was modelled as a plate-stiff shell, so the whole device stayed straight
  (bend 0.1 deg while the skin under it bends 3.65 deg) and the bladder was never squeezed. Fix: fabric bending stiffness
  (`--cover_bend 0.003`); check deck `02_Nastran_Model\CHK_FABab.nas` (= MINI_K + fabric cover).
- CHK_FAB was stopped after 2 min by the shell's low-memory guard (E-40), not by the solver. Waiting for the owner's go to restart.
- Production decks R1..R7 are NOT yet regenerated with the fabric cover; do that after CHK_FAB confirms the torque.


## 10. Update 13 Nov 10:30
- CHK_FAB (fabric bending 0.003) failed in D2: flange rotations near-singular (E-41/E-43). CHK_FAB2 (flange bending 1.0) failed in
  D2: cover side wall wrinkles at the thigh-near ring edge (E-44/E-46). Low plate bending is not usable with the static solver.
- Owner decision D-FAB3: plate bending 1 (as MINI_K) + orthotropic cover membrane (E_leg = G12 = 1 % of E_hoop), `--cover_ortho 0.01`;
  MCID orientation verified by solver test t7. Check deck `02_Nastran_Model\CHK_FAB3\fab3.nas`, to be run by the owner.
- `--flange_bend` (E-43) kept as an option; not used in CHK_FAB3.


## 11. Update 13 Nov 11:20 (owner D-AUTO: continue without stopping for approval)
- CHK_FAB3 failed in the first flex step (E-47..E-50; E-49 pad-edge explanation withdrawn in E-50). CHK_FAB4 (= FAB3 with an isotropic
  flange) converged 7/7: device moment -0.10 / +0.09 N.m vs hand calc 4.14 N.m; device bend 1.4 deg vs skin 3.66 deg; dV/dtheta ~ 15 mL/rad
  vs k 207 mL/rad (E-51). Production default = CHK_FAB4 cover (D-FAB4). Production launched (Fast: R1/R2 to the end of release).


## 12. Update 13 Nov 19:10
- E-52 relaxed CAL stalled -> D-ORDER (contracted first). E-53 PC restart at 13:22 killed R2 at 42/43 (41 steps with data, to 80 % stance); R2V 43/43.
- R2 device moment (R2 - R2V): 0.015-0.093 N.m over the pulse (0.078 at 21 %) vs hand calc 0.58-4.14 N.m; ACL |dFx| <= 0.26 N; skin mean <= 2.4 kPa, posterior peak 10.1 kPa; bladder vm 0.95 MPa.
- Delivered v1: 07_Report\FEA_asm07_routeA_Report_v1.docx, 05_Results\Tables\v1 (summary_all_runs_v1.xlsx + CSV), 05_Results\Images\v1.
- Queue running: queue_resume_1.txt (R4, R6, MS_M1C, R1, R1V, R3, R5, R7). Next issue: collect_a07.py --tag v2 / build_report_a07.py --tag v2.
- error_log: duplicate auto id E-51 (run fab4 bisect) renamed E-51a.


## 13. Update 13 Nov 23:30 - production finished
- R4 43/43, R6 51/51 (restarted after the external stop at 20:09, E-56), MS_M1C 17/17; relaxed runs not run (D-RELAX). Queue finished 23:04.
- Device moment over the pulse: R2 <= 0.09, R4 (27 kPa) <= 0.12, R6 (option 1, twin interpolated) -0.15..0.10 N.m vs hand calc 4.14 / 5.59 N.m.
- Mesh study M1 vs M0 at 21 %: knee reaction -4.4 % (<= 5 %), device moment 0.06 vs 0.08 N.m; skin pressure and ring tension NOT mesh-converged (20-70 %), all far below limits except ring-edge peaks.
- Delivered v2: 07_Report\FEA_asm07_routeA_Report_v2.docx (23 pp), 05_Results\Tables\v2, 05_Results\Images\v2. v1 kept unchanged.
- collect_a07.py fix: runs with several W steps (mesh study) use W(last before VREF) - VREF.
