# BRIEF v3 - FEA matching the hand-calculation assumptions, real-case effects, pressure sweep, path to 4.4 N.m, report v3
Written 14 Nov 2026 and approved item by item by the owner (merge of the owner's simulation notes and the previous brief).
Run folder R = <PROJECT>\03_Mechanical_Design\CAD\last v2\last v6\simulation_2_assymbly_7
Read this whole file before doing anything.

## 0. Owner intent and working rules
- Make an FEA whose assumptions MATCH the hand calculation (v12 Part E, Model B), then add the real-case assumptions one at a time and
  state the effect of each with FEA evidence; explain the low torque; show how to raise it to 4.4 N.m within the constraints (if not
  possible: the reason and the highest reachable value, with the governing limit); compare everything; justify every choice; state
  every limit clearly; write it as an engineer.
- The hand-calc-matching run is an IDEALISED REFERENCE requested by the owner - label it so; it is never the real-device verdict.
- DECIDE AND CONTINUE (owner): do not stop for missing data. For every missing/uncertain input make the engineering choice, and list
  it in the report (Decisions table: input, value chosen, reason, source or basis, effect of the other possible choices - quantified
  by a run or an estimate). Also append each decision to 00_Plan_and_Decisions\decisions_2026-11-13.txt (ASCII).
- No web search, no external databases or papers; never present an invented number as source data. A chosen value is labelled
  "engineering choice" with its reason. Never change the hand-calculation values.
- Questions to the owner only if truly blocking, in plain text (no dialogs).
- Before starting, tell the owner in one short list which files you will use (section 1) - they are already approved; just confirm.

## 1. Allowed sources (approved 14 Nov)
Engineering / design / material data:
1. 06_Reports_and_Presentations\Working\Progress_Document\progress-7.9.docx
2. 03_Mechanical_Design\Design_Reports\M1-M7 work v12.docx  (hand calc; replaces v10 - same k, same Model A / B)
3. 03_Mechanical_Design\Design_Reports\Component_Data_Book_last-v6.docx
4. CAD: 03_Mechanical_Design\CAD\last v2\last v6\Route a - thigh strap 150 (main)\ (full asseymbly 07.iam, actuator-V8.ipt and parts)
   - read only; work on copies (R\01_CAD_copy); never modify the originals (md5 in R\00_Plan_and_Decisions)
Pipeline / history (needed by the scripts):
5. Everything in the run folder R (BRIEF.md, STATUS.md, decisions_2026-11-13.txt, error_log.csv, queue_log.txt, scripts\, meshes,
   04_Runs\*, 05_Results\v1, v2, 07_Report v1, v2)
6. 03_Mechanical_Design\Design_Reports\m1-m7\_cad_v8_scripts\geo8.py and geo_A150.json (the code that built the CAD; the mesh is made from it)
7. 02_Biomechanics\Team_Inputs\Biomechanics_Handover\01_Requirements_and_Inputs\Clinical_Constraints_B1-B8_2026-11-12\
   Biomech_Constraints_Option2_PatientRange_13-36_v3.xlsx (window, angle and pressure frames) and
   02_Biomechanics\Team_Inputs\Biomech_B7_Tissue_Tolerance_v8.xlsx (tissue limits)
Text-dump the .docx files with python-docx (paragraphs + tables) and grep; do not read the raw docx. Older files (v10 etc.) are not
sources any more; earlier results cite v10 = same numbers as v12.

## 2. Hand calculation to match (v12)
- Model B (Part E.3, Eq. 43): Mz = p k, k = dV/dtheta = integral over the cavity cut at y = 0 of rho dA = 206 990 mm3 at d_h 65 mm
  (= 0.207 N.m per kPa) -> 4.14 N.m at 20 kPa, 5.59 at 27 kPa. UPPER bound. 4.4 N.m needs 21.3 kPa in Model B.
- Model A (E.2, Eq. 42): base pushes each half forward, near ring pulls back at almost the same y -> 0.280 N.m (20 kPa), 0.379 (27).
  LOWER bound.
- E.4 Table E-3: passing the full Model-B moment needs skin shear with mu_req = 0.48; approved mu = 0.37.
- Model B assumptions: rigid leg halves turning about the knee axis Z through O (d_h 65 mm in front of the back skin; no source,
  band 0-80 -> 1.35-4.79 N.m); bladder cavity halves turn rigidly with thigh / shank (no pad shear, no tissue deformation, no slip);
  no losses; constant pressure; quasi-static.
- v12 W.7 (Table W-7): FEA stance angle cases 0.7 / 3.3 / 5.8 deg, swing check 65 deg, pressure range 0-27 kPa (design 20).
- v12 Table V-1: readings 0-200 kPa (step 10) with tau, alpha, near-strap pressure, seam factor.
- v12 W.9: 20 kPa = the biomechanics lead option-1 limit (22.7 x 0.9, no pain), 27 kPa = option-2 side case (31 x 0.9), both from tissue tests and
  applied in v12 to the BLADDER pressure ("30 kPa: tissue fails"). Owner, 14 Nov: the 27 kPa limit is ON THE SKIN. Report both views.

## 3. Real-case FEA already done (v1/v2, contracted tissue, fabric cover D-FAB4) - reuse, do not re-run
| Run | case | converged | device moment (run - vented twin) | p k |
|---|---|---|---|---|
| CHK_MINI_K | plate-stiff cover, 20 kPa at 21 % | 7/7 | -0.17 / +0.07 N.m | 4.14 |
| CHK_FAB4 | production cover, 20 kPa at 21 % (= ladder step B3) | 7/7 | -0.11 / +0.09 N.m | 4.14 |
| R2 | opt 2, 20 kPa, D->release | 41/43 (PC restart E-53) | 0.015-0.093 N.m (0.078 at 21 %) | 0.58-4.14 |
| R4 | opt 2, 27 kPa | 43/43 | <= 0.12 N.m | 5.59 |
| R6 | opt 1, 20 kPa (twin R2V theta-interpolated) | 51/51 | -0.15..0.10 N.m | 4.14 |
| MS_M1C | mesh M1, D->21 % + VREF | 17/17 | 0.059 N.m; knee reaction -4.4 % vs M0 | 4.14 |
Why low (evidence): dV/dtheta (vented) ~15-17 vs 207 mL/rad; device bends 1.4 deg vs skin 3.66 deg (knee 5.78; diag_bend.py on
CHK_FAB4); skin slip 7-12 mm; skin force under the bladder +1.4 N only on inflation, mean skin pressure 2.3 kPa at 20 kPa inside
(pad + cover = self-reacting drum); near rings (y +-35) on the bladder line (y -85..+85) -> Model A situation; pad sink ~6 mm (penalty
contact, E-36). Other: skin mean <= 2.4, peak <= 12.8, posterior-knee peak <= 10.1 kPa; ring donning mean <= 6 kPa; ring edge peaks
~236 kPa (single nodes, mesh-dependent); bladder vm <= 1.1, cover <= 6.9, hooks <= 2.0 MPa; Velcro <= 31.8 N; ACL |dFx| <= 0.3 N.
D2 ring tension 31.8/12.1/16.9/12.2 vs targets 20.89/19.59/13.3/9.4 N. Contact pressures / ring tensions not mesh-converged (20-70 %).
Relaxed tissue: pre-tension does not converge (E-52, D-RELAX). Pressure trend of the real case: ~0.004 N.m per kPa (R2 vs R4).

## 4. Model approach (approved)
- Solver: C:\Program Files\Autodesk\Inventor Nastran 2026\Nastran\Nastran.exe (NOT NastranCmd.exe - only a wrapper shell), SOL 106,
  PARAM,LGDISP,1, multi-subcase, run through scripts\run_queue.ps1.
- Mesh: scripted from the CAD build code (scripts\mesh_a07.py <- geo8.py + geo_A150.json); Inventor's own mesher failed on this
  assembly (E-02..E-05). Inventor 2026 only to read dimensions / materials of actuator-V8.ipt and the assembly and for CAD screenshots.
- Actuator = inflatable bladder: shell on the mid-surface (t 2), follower PLOAD4 on all inner walls = air pressure in the cavity;
  air path outside -> tube -> cavity stated; tube not structural (state it). Verify the bladder material against v12 / Data Book
  (Elastollan 1185A TPU) and state the model value (MAT1 E 7.2 MPa, nu 0.49 now) with its source; if the source differs, decide and
  document (section 0).
- Leg for the hand-calc-matching case = rigid blocks + knee hinge: rigid halves split at the plane y = 0 (all tissue nodes y >= 0 RBE2
  to the thigh control node, y < 0 to the shank control node; tissue CHEXA removed), shank turned about the knee axis by SPCD.
  Real case = existing soft neo-Hookean leg (contracted).
- New deck options must be opt-in flags of scripts\deck_a07.py with default = old behaviour, proven by regeneration of fab4.nas with
  0 differences (done this way for every earlier option). Options already present: --cover_ortho (default 0.01), --flange_iso /
  --flange_ortho, --cover_bend, --padE, --mu, --mu_ring, --bond_skin, --vref, --vent, --opt, --plim, --seq (MINI / D / D-21 / D-R / FULL).

## 5. Run plan (one Nastran job at a time; ~15-25 min per MINI-type run on M0)
Case IDs: <model>_A<angle>_P<pressure>, e.g. B0_A5.8_P20, REAL_A3.3_P27; mesh study MS3_<level>.
5.1 Mesh study on the rigid hand-calc model B0: M0 / M1 / M2 (meshes exist: 02_Nastran_Model\mesh_M0/M1/M2.pkl; rigid leg drops the
    tissue elements, so M2 should fit in RAM); criterion <= 5 % change of knee moment, max bladder stress, max deformation, bladder
    volume. Real case: reuse the M0 vs M1 study (MS_M1C). 4 levels are not feasible on 7.7 GB RAM - state it.
5.2 Assumption ladder at 5.8 deg / 20 kPa (MINI sequence: D1, D2, flex vented to 5.78 deg, inflate, VREF), contracted, M0:
    B0 rigid halves + bonded pad/ring-skin (--bond_skin) + stiff pad (decide E, state it) -> expected ~ Model B 4.14 N.m (validates
       the hand calc and the moment extraction; if not reached, find why - e.g. the self-reacting pad+cover drum - and consider B0'
       with the cover outer panel also tied to the halves; that is itself a finding about the hand-calc assumption);
    B1 = B0 + soft tissue (contracted G 400 kPa);  B2 = B1 + real pad E 0.0965 MPa;  B3 = B2 + friction mu 0.37 (= CHK_FAB4, reuse);
    optional mu 0.48 (v12 mu_req). Waterfall 4.14 -> ... -> 0.1 N.m with the share of each assumption.
5.3 Matrix on B0 (rigid, fast): angles 0.7 / 3.3 / 5.8 / 65 deg (v12 W.7) x pressures 0 / 10 / 20 / 27 + a fifth level (decide, e.g.
    2.4 kPa residual or a higher reading - state why) = 20 cases. Real case: the stance angles at the same pressures where feasible
    (65 deg on the soft leg risky - earlier rigid halves closing on the bladder above ~20 deg failed; decide and document).
5.4 Pressure sweep FAR beyond the limits (owner): state the limits (section 7) and go well past them - e.g. 27, 40, 60, 100, 150,
    200 kPa (v12 readings reach 200 kPa) at 5.8 deg on B0 AND on the real case. For every level report the result (moment, skin
    mean/peak, posterior-knee peak, ring/cuff pressure, bladder / cover / hook stresses, volume, ACL force), which limits pass or fail
    with the margin, a justification and an engineering comment (what it means for the patient and the hardware).
5.5 Fix-path runs toward 4.4 N.m within the constraints (as time allows): cover outer panel stiff in tension along the leg anchored to
    the FAR cuffs (+150 / -120 mm) instead of the near rings; + load-spreading (stiffer / thinner pad under the bladder) so that
    p_skin = p_inside x A_bladder / A_spread stays <= the skin limit; mu 0.48; ring pre-tension calibrated to target (2-3 CAL
    iterations). If 4.4 N.m is not reached: highest value that passes every limit and the governing limit with its number.

## 6. Results to extract per case (only what the solver or an allowed source really gives; otherwise "unavailable" + reason)
Stress (von Mises; principal; shell top/bottom), strain, total deformation, reaction forces and moments (thigh / shank control nodes),
knee torque = device moment (run - vented twin or own VREF), effective moment arm = Mz / resultant bladder force on the leg half,
skin contact pressure (mean / peak, under the bladder, posterior-knee zone, each ring), contact status / slip, ring tension, bladder
cavity volume and total volume, volume change, factor of safety (from strengths in v12 / Data Book: equation, inputs, units, result),
fatigue and cycles ONLY if S-N / fatigue data exist in the allowed sources (else state the missing input), numerical data
(convergence, iterations, bisections, warnings). Flow, fill time, pressure-rise and time-to-torque are NOT structural-FEA results:
quote v12's hand values (e.g. Table W-9) labelled as hand calculation. Deformation animation rendered from the solver displacements
(real data, e.g. matplotlib frames -> mp4/gif) if feasible; otherwise state it.

## 7. Limits table (one table in the report, with the source of each; flag conflicts)
- Skin contact pressure: 27 kPa (owner, 14 Nov). B7 v8 / BRIEF Q14: mean <= 24 kPa (20 kPa case) / 36 kPa (27 kPa case),
  posterior-knee peak 24 / 36. v12 W.9: 20 / 27 kPa applied to the bladder pressure. Show all three, state which governs (owner: skin 27).
- Ring/strap: local peak <= 19 kPa in the pulse; donning mean <= 11 kPa.
- Bladder wall vm <= 11.1 MPa; cover <= 37.2 MPa; hooks <= 5.68 MPa (pre-tension) / 14.2 MPa (pulse); webbing T <= 5300 N; Velcro <= 65.5 N.
- ACL (DR-B6-1): net forward shank force ~ 0; DR-B6-2 no device torque at theta <= 0; residual 2.4 kPa.
- Internal pressure practical limits: stresses above, seam factor (v12 V-1), air volume / flow per step and rise rate (v12 W-9:
  864 kPa/s at 20 kPa in window 2), sensor range (v12 K.2: 0-50 kPa part).
- Target torque 4.4 N.m (owner); v12 design point 4.14 N.m at 20 kPa.

## 8. Report v3 (Word .docx only; include ALL chapters - owner)
07_Report\FEA_asm07_routeA_Report_v3.docx (never overwrite v1/v2); tables 05_Results\Tables\v3; images 05_Results\Images\v3;
video 05_Results\Videos\v3. Build with scripts\collect_a07.py / build_report_a07.py (extend or copy to a v3 builder): python-docx,
native OMML equations (r / fr / sb / sp / par helpers), [n] citations with real file names, every table numbered with units, every
figure numbered with case information; charts: fixed palette #2a78d6 #eb6834 #1baf7a #eda100, one y-axis per chart, labelled limit
lines. Check the docx via a Word-COM PDF in the scratchpad (not delivered).
Chapters: Summary (key numbers + verdicts) - Introduction / task and mechanism - Allowed sources - Hand calculation (Model A / B,
assumptions) - Model and set-up (geometry, material, boundary conditions, inflation model, rigid-leg reference vs real case,
assumptions side by side: same / not) - Decisions table (section 0) - Mesh study (levels, quality, convergence table and graphs,
selected mesh) - Simulation matrix and solver status - Assumption ladder B0..B3 (waterfall, effect of each real-case assumption with
evidence) - Matrix results (pressure vs torque, angle vs torque, angle vs moment arm, FEA vs hand calc) - Pressure sweep beyond the
limits (result, pass/fail, justification, comment per level) - Stress, strain, deformation, reaction force, torque, moment arm, FoS,
fatigue / cycles (or unavailable), pressure-volume, inflation stages, time / flow (hand values, labelled) - Real-case production
results (v2) - Why the torque is low (ranked causes with evidence) - How to reach 4.4 N.m (options compared: change, mechanism,
FEA / estimated moment, every limit checked, effort; recommended path; highest reachable value) - Justification of every choice -
Limits table - Limitations and idealisations - Future work and tests (v12 T-06 fabric, T-08 internal friction, T-09 slip, torque
test on a leg phantom, measured pad shear modulus, d_h source) - Images (CAD, mesh, BCs, pressure, deformed, contours) and video -
Solver logs / status - Errors encountered (all E-xx) - Missing / unavailable data - References [n] - Delivered files.
Tables to include (owner list): material; geometry and model parameters; mesh levels; mesh convergence; solver status; full matrix;
stress; strain; deformation; reaction forces; knee torque; effective moment arm; FoS; fatigue; cycles; pressure-volume; inflation
stages; hand calc vs FEA (|FEA - HC| / |HC| x 100) - plus the ladder, sweep, decisions and limits tables.
Graphs: mesh size vs stress / deformation / torque; convergence; pressure vs torque; angle vs torque; pressure vs deformation; pressure
vs cavity and total volume; angle vs moment arm; FEA vs hand calc torque; ladder waterfall; sweep vs limits; contour images.

## 9. How to run (traps learned the hard way)
- Python: C:\Python314\python.exe -P script.py (no -I). Write .py files with the Write tool only (PowerShell Set-Content
  double-encodes, cp1256). In %-format strings write a literal percent as %%.
- PowerShell 5.1: variables are case-insensitive ($r overwrites $R); empty "" arguments to native exes are dropped.
- Deck: python -P scripts\deck_a07.py --mesh 02_Nastran_Model\mesh_M0.pkl --out 02_Nastran_Model\<RUN>\<run>.nas --run <RUN>
  --seq MINI --tissue contracted --calib 02_Nastran_Model\CHK_FAB4\calib_minik.json [options]
- Launch detached (keeps running when the terminal is closed), one job at a time:
  Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='powershell.exe -NoProfile -ExecutionPolicy
  Bypass -File "<R>\scripts\run_queue.ps1" -ListFile "<R>\02_Nastran_Model\<queue>.txt" -Ram 2500 -StallMin 45'; CurrentDirectory='<R>'}
  run_queue moves the native files to 04_Runs\<RUN>, writes runtime.txt, post-processes (post_a07.py) and appends solver warnings to
  error_log.csv (numbering = row count + 1: give your own rows max-id + 1 and check for duplicates).
- Watch with Monitor on 06_Error_Log\queue_log.txt ("done", "post-processed", "stall", "queue finished"); re-arm every 30 min. No long
  background shell waiters (reaped when RAM is low; never restart a reaped one on your own).
- PC 7.7 GB, often < 1 GB free; M0 runs peak ~2.8 GB, M1 ~2.9 GB (slow when swapping); Word-COM ~300 MB. Runs were ended externally
  twice (E-53 restart, E-56 unknown): partial .OUT files can be post-processed (post_a07.py <run.OUT>); restart without the finished runs.
- diag_bend.py <run.OUT> = bladder bend vs skin bend. collect_a07.py --tag vN refuses an existing non-draft tag.

## 10. Must not be lost
- Never touch the last v6 originals or 99_Archive; never overwrite delivered files (new tags); never simulate route (b); Word .docx only.
- Log every problem in error_log.csv (exact message, step, cause, fix, proof) and every decision in decisions_2026-11-13.txt.
- Final message to the owner: short - the Word file, the output package location, unresolved items / failed cases. Never claim a
  result, convergence, fatigue life or flow quantity that was not actually computed.
