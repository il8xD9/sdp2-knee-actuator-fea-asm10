# BRIEF - Simulation 2, full asseymbly 07 (route a, thigh strap +150) - gait FEA with Inventor Nastran solver

Owner: mechanical lead (MMNB team, SDP-2 knee-assist soft exoskeleton). Run folder (ALL output here):
R = <PROJECT>\03_Mechanical_Design\CAD\last v2\last v6\simulation_2_assymbly_7
Owner is asleep and said: do all the work, take the best engineering choice, never ask, solve every problem,
log every problem (exact message, step, cause, fix, proof) and state it in the report. Deliver outputs usable in the project.
Owner also said: the bladder MUST be inflated by pressurised air (internal follower pressure on the bladder inner walls),
and the inflation must PRODUCE the knee torque (knee moment = reaction about the knee axis from the solver).

## 0. Hard rules
- Never modify anything in CAD\last v2\last v6 outside this run folder; never use 99_Archive; never overwrite delivered files.
- PC: 7.7 GB RAM, ~0.8 GB free (user apps open - do NOT close them). ONE Nastran job at a time. Keep models small (target <= 60 000 grids).
- Python: C:\Python314\python.exe (numpy, scipy, matplotlib, python-docx, openpyxl, lxml, PIL; NO gmsh/pyNastran/meshio). Run python with -P.
  Never edit .py files with PowerShell Get-Content/Set-Content (cp1256 codepage double-encodes UTF-8). Write files with the Write tool.
- Solver: "C:\Program Files\Autodesk\Inventor Nastran 2026\Nastran\Nastran.exe" deck.nas  (ADS NASTRAN 20.2, licensed, headless OK).
  Outputs: .OUT (f06-like text), .FNO, .LOG, .RSF, _err.json. Real numbers MUST have a decimal point (GRID 0 -> 0.0, else FATAL T2002).
- Error log: R\06_Error_Log\error_log.csv  columns: id, time, step, exact_message, cause, fix, proof. Append every error/warning/non-convergence.
  Already happened (add as E-01..E-05): E-01 NINAutomation (Inventor Nastran add-in automation object) exposes no callable
  methods (IDispatch GetIDsOfNames 0x80020006 for all 56 names; no type library, LoadTypeLibEx 0x80029C4A) -> set-up dialogs not scriptable.
  E-02 Inventor default mesh: "'Mesh': Mesh does not contain any nodes or elements" / "Mesh is not valid" (thin parts) ->
  "Nastran File cannot be created". E-03 After suppressing thin parts: "Some features have been lost due to geometry modification"
  dialogs, then "Meshing Failed." (hooks / pad at default 17.9 mm size). E-04 Mesh Settings dialog is a custom control (UIA panes,
  no Invoke/Value patterns) -> only mouse automation; route judged unreliable overnight. FIX for E-01..E-04: geometry taken from the
  exact CAD build definitions of last v6 (geo8.py + geo_A150.json, the same code that built the parts), structured mesh written by
  script, solved by the Inventor Nastran solver (Nastran.exe) - all results come from Nastran output. E-05 test deck: FATAL T2002
  invalid real (integers in GRID) -> fixed by %.4f formatting.

## 1. Geometry sources (exact CAD of last v6 asm 07)
- Builder code: 03_Mechanical_Design\Design_Reports\m1-m7\_cad_v8_scripts\geo8.py (functions r(y) leg radius PCHIP, pad outline
  s_edge/th_edge, station_angles, web_parts, hook_parts, frame/path/stadium/bladder_a, cover8, tube_place) and geo_A150.json
  (option A150 = main). Read geo8.py fully; reuse its functions by importing (sys.path insert) - do not copy numbers by hand.
- CAD frame: Y = leg axis (thigh +Y), knee line y = 0, point = (R cos th, y, R sin th), th = 0 at the BACK of the leg (+X = posterior).
  Leg: leg-tissue.02 Y -170..180, r(y) (girths B8 +2 SD); bones d30 on the axis: thigh-bone Y 10..180, shank-bone Y -170..-10.
  Live Inventor read (12 Nov): actuator-V8 X 73.6..140.4, Y -120.1..119.8, Z +-33.0; cover.06 X 54.6..142.0, Y -97.9..97.4, Z +-50.9;
  pad streches.10 Y -143..173; webbing.03 Y -132.7..162.7; velcro.05 Y -132.7..162.7.
- Knee axis: parallel to Z through (X = r(0) - 65 = 4.06 mm, Y = 0) (d_h = 65 mm in front of the back skin, owner Q6).
  Flexion theta > 0 moves the shank (y < 0) towards +X (posterior): rotation about +Z by +theta for the shank (check sign once).
- Parts in asm 07: leg-tissue.02, thigh-bone.02, shank-bone.02, streches.10 (pad, 6 mm), webbing.03 (4 closed Type XXV rings:
  near +-35 (two webbings side by side, 50.8 wide), thigh far +150, calf far -120 (25.4 wide), t = 3.18; 72 mm tails; M3 carriers
  thigh 95-120, shank -107.3..-95), velcro.05, hook.05 (near, 40x60.5x4) x2, hook.06 (far, 31x35x4) x2, actuator-V8 (moulded capsule
  66 x 44 outer, wall 2, ends R10, inner 62 x 40, 190 long / 170 contact, M3 base tabs 40x25x2, port d6), cover.06 (0.43 mm,
  1.0 mm gap to the bladder everywhere, end caps R11/R11.43, M3 notch 42 x 4.5 R1 on the leg-side edge of each cap, 10 mm sewing
  flanges), tupe-15 (tube, not structural).

## 2. Approved modelling decisions (owner, 13 Nov) - see decisions_2026-11-13.txt for the justifications
| Item | Decision |
|---|---|
| Analysis | Nonlinear static (SOL NLSTATIC / 106 style), PARAM,LGDISP,1, follower pressure, multi-subcase sequence (each subcase continues) |
| Tissue | neo-Hookean MATHP: relaxed A10 = 0.00275 MPa, D1 = 0.0275 MPa; contracted A10 = 0.2, D1 = 2.0 (G 5.5 / 400 kPa, K = 10 G, D1 = K/2 convention used by Inventor: MATHP,id,A10,,,D1 - check field order against the working test deck t1.nas: "MATHP,1,0.00275,,,0.0275,1.e-6") ; rho 1000 kg/m3 |
| Bones | rigid: RBE2 from a control node to all tissue nodes on the bone bore (r = 15 mm) of each bone; thigh control node fixed 123456; shank control node on the knee axis: 12345 fixed, 6 enforced (SPCD, radians). Tissue across the 20 mm knee gap: continuous (state the d30 hole idealisation if the core is not meshed) |
| Pad streches.10 | solid hex (>= 2 layers through 6 mm), linear elastic E 0.0965 MPa, nu 0.33, rho 203.9 kg/m3 (2nd case R7: E 0.276) |
| Webbing rings + tails + carriers | shell t = 3.18, MAT1 E 498 MPa nu 0.35 rho 576 |
| Velcro closures / M3 patches | shell, E 498, nu 0.35, rho 109 (may be merged into the ring/tab where they overlap - state it) |
| Hooks hook.05/.06 | POM E 2760 MPa nu 0.37 rho 1410 (shell t = 4 or solid) |
| Bladder actuator-V8 | SHELL on the mid-surface (t = 2): owner Q4. Try MATHP on shells; if rejected use MAT1 E 7.2 MPa nu 0.49 (large displacement). rho 1120 |
| Cover cover.06 | shell t = 0.43, MAT1 E 498 MPa nu 0.35 rho 1105, flexible (no rigid cover, no springs, no check models) |
| Tube | not structural - may be omitted (state it) |
| Contacts | bonded (shared nodes or bonded contact): cover flanges/cap edges - pad/webbing; webbing - pad (incl. carriers); webbing - hook; tail/Velcro/ring; bladder M3 tab - Velcro patch; tissue - bone (RBE2). Separation frictionless: bladder - cover (1 mm initial gap), bladder - webbing/pad. Separation with friction mu = 0.37 (owner Q5, Zhang & Mak 1999): pad - skin, rings - skin, cover - skin, bladder - skin, skin - skin self contact behind the knee (thigh vs calf) for swing |
| Pre-tension | owner option (a): ring tension thigh near 20.89 N, shank near 19.59 N, thigh far 13.3 N, calf far 9.4 N. Method: thermal shrink of the ring shells (MAT1 alpha + TEMP/TEMPD, TEMPERATURE(LOAD)), dT calibrated so the ring tension (shell membrane force x width) reaches the target in the donning step |
| Gravity | OFF. Inertia OFF (quasi-static) |
| Knee depth | d_h = 65 mm only |
| Hold | = peak frame 21 % (148 ms), no extra hold step |
| Units | mm, N, MPa, tonne/mm3 (rho kg/m3 x 1e-12) |

Contact card format (from an Inventor-generated deck, 05_Simulation_FEA\Models\FEA_model\w6-sym\InCAD\FEA\upgy9os2k.nas - huge file,
grep only): BSSEG,sid,g1,g2,g3,(g4 or blank),... segments (tria: 4th blank); BSCONP,ID,SLAVE_SID,MASTER_SID,SFAC(1.0),,FRIC(field 6),TYPE(field 7),...
Inventor wrote TYPE 2 "AUTO", 3, 4 for different contact kinds; the meaning of the TYPE codes is NOT verified - verify with a tiny 2-block
test (pull apart: bonded keeps them together) before use. Earlier working frictionless decks used "BSCONP,1,11,21,,,0." (no TYPE).
Case control CONTACT = ALL and BCRESULTS = ALL are NOT recognised (WARNING T2104). Find the right contact-result request: grep the
parameter list printed in upgy9os2k.OUT (lines ~300-400, e.g. CONTACT... params) and test. Contact results may only be in the .FNO;
fno2op2.dll exists in the solver folder. If no contact output can be obtained, recover skin pressure from GPFORCE / element
stresses of the skin layer and state it.
Reference pipeline that worked on this solver (Oct 2026): 05_Simulation_FEA\Runs\Simulation_p6.6\scripts\deck66.py, mesh66.py, post66.py,
queue66.ps1 (read for patterns: NLPARM "NLPARM,k,nincs,,ITER,1,maxiter,PW,NO" + continuation eps; SPCD per subcase; PLOAD4 follower).
Known traps: SPCD is interpolated linearly inside a subcase -> rotate in steps <= 2.5 deg; run Nastran.exe directly (NastranCmd.exe is a shell);
never pass "" args from PowerShell; earlier runs failed when rigid halves closed on the bladder (> 20 deg) - here the leg is soft.

## 3. Load / gait sequence (one run = one multi-subcase deck)
D1 donning: theta 0, p 0 (contacts settle). D2: pre-tension (thermal shrink) at theta 0.
S1: stance frames 1, 3, 6, 9, 12 % with p = 0: theta = -1.92, -0.76, 0.01, 0.88, 2.59 deg.
W (window option 2, every 1 % frame) - frame / ms / theta deg / p20 / p27 (kPa):
13/92/3.28/6.9/6.9  14/99/3.93/13.0/13.0  15/106/4.50/15.2/18.6  16/113/4.95/16.7/22.5  17/120/5.29/17.8/24.1  18/127/5.53/18.8/25.4
19/134/5.68/19.4/26.2  20/141/5.76/19.8/26.8  21/148/5.78/20.0/27.0  22/155/5.75/19.9/26.9  23/162/5.68/19.6/26.5  24/169/5.59/19.2/25.9
25/176/5.48/18.6/25.1  26/183/5.37/17.9/24.1  27/190/5.25/17.1/23.0  28/197/5.15/16.2/21.9  29/204/5.05/15.3/20.7  30/212/4.98/14.4/19.5
31/219/4.91/13.5/18.3  32/226/4.84/12.6/17.1  33/233/4.79/11.8/15.2  34/240/4.73/10.9/11.2  35/247/4.68/7.0/7.0  36/254/4.63/2.8/2.8
(p = min(alpha*deficit, M_pat)/k, k = 206994 mm3, alpha_max 0.1255 / 0.1694; source Biomech O2 Waveform_Opt2 + M1-M7 v10 Eq. 20-21.)
Window option 1 (runs R5/R6, no cap, frames 9..44 every 1 %): p = alpha*deficit/k; theta and deficit per frame from O2 Waveform_Opt2
(text dump: <TEMP> lines 180-280:
columns: % stance | time ms | ... | deficit col 7 | M_pat col 6 | ... | knee flexion col 14). Check: 9 % = 63 ms 0.88 deg 5.0 kPa; 21 % 20.0; 44 % 310 ms 4.06 deg 3.8.
R (release/vent): frames 37, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 87 (87 % = 613 ms): theta 4.57, 4.36, 3.99, 3.74, 3.68, 3.78, 4.06, 4.65,
5.63, 7.10, 9.25, 10.43 deg; p from the offset value to the residual 2.4 kPa at 37 % and held at 2.4 kPa (worst allowed residual).
TO: frames 90, 95, 100: theta 12.83, 19.13, 27.81 deg, p 2.4. SW: 27.8 -> 65 -> 78 deg in 2.5 deg steps, p 2.4. SW-R (optional): 78 -> 0 in 5 deg steps.
If a subcase does not converge: bisect / more increments / smaller angle steps; never change a design value; log it.

## 4. Runs (one at a time)  [assembly 08 NOT run]
R1 main: opt 2, 20 kPa, relaxed, full sequence. R2: same, contracted. R3/R4: opt 2, 27 kPa, relaxed/contracted, D->R. R5/R6: opt 1, 20 kPa,
relaxed/contracted, D->R. R7: opt 2, 20 kPa, relaxed, pad E 0.276, D->21 %. Mesh study M1/M2/M3 (coarse/medium/fine; device ~3/2/1.5 mm,
tissue ~6-15 / 4-12 / 3-10 mm, adapted to RAM) on R1 D->21 %; converged when knee Mz, mean skin pressure under the bladder and ring tension
change <= 5 % between the two finest meshes. If RAM/time do not allow all runs, keep the priority R1, mesh study, R2, R3, R5, R7, R4, R6, and state it.

## 5. Outputs (request all; export to CSV/XLSX in R\05_Results\Tables)
DISPLACEMENT, STRESS (von Mises, principal; shells top/bottom), STRAIN, SPCFORCES (thigh control node = thigh load; shank control node R6 =
KNEE MOMENT about the knee axis), MPCFORCES, FORCE (shell resultants -> ring tension), GPFORCE, ESE, OLOAD, contact pressure/force/slip/gap
(if available), intermediate output for all increments (NLPARM INTOUT=ALL where supported), convergence history (.OUT), mass (PARAM,GRDPNT,0),
mesh quality stats (aspect ratio, Jacobian, min angle - computed by script). Derived by script from Nastran output (not hand calc): device
moment about the knee axis (also from contact forces on the shank side if available), mean/peak skin pressure under the bladder, under each
ring, posterior-knee zone (y 0 .. -20 mm below the patella line - use y in [-40, +20] on the back), cavity volume of the bladder vs step
(from displaced inner nodes), ring tension per ring, device slip along the leg, net shank force in X (ACL rule DR-B6-1).
Native files to R\05_Results\Native_Nastran. Images to R\05_Results\Images (matplotlib renders of the deformed mesh with contours per key step;
CAD views from Inventor via API Camera.SaveAsBitmap if possible). Summary sheet: R\05_Results\Tables\summary_all_runs.xlsx.

## 6. Pass / fail (owner Q14)
Bladder inside p <= 20 / 27 kPa (input). Skin contact mean under the bladder <= 24 / 36 kPa (the biomechanics lead B7 row 19), peaks reported.
Posterior-knee zone local peak <= 24 / 36 kPa. Rings: local peak <= 19 kPa during the pulse; donning mean <= 11 kPa (peak vs 1.6 x mean).
Residual 2.4 kPa (input). Bladder wall von Mises <= 22.2/2 = 11.1 MPa. Cover <= 74.4/2 = 37.2 MPa. Webbing T <= 5300 N. Velcro: band
tension <= 65.5 N. Hooks <= 5.68 MPa (pre-tension) / 14.2 MPa (pulse). ACL: net forward shank force ~ 0; no device torque at theta <= 0.
Compare: knee Mz vs hand calc 4.14 N.m (20 kPa) / 5.59 N.m (27 kPa) (M1-M7 v10 W-3, d_h 65); ring tension vs v10 Table G-1; mu_req 0.218.

## 7. Report (later phase): Word .docx with native OMML equations in R\07_Report (python-docx + OMML XML), all chapters of the owner's
request, chapter "Errors encountered", [n] citations with real file names. No PDF.
