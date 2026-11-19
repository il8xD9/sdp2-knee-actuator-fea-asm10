# -*- coding: utf-8 -*-
r"""Word report v3 - FEA of full asseymbly 10 (route a), IDEALISED hand-calculation reference (HC set, 0-60 kPa), 16-17 Nov 2026.
Inputs: 04_Runs\<run>\*_results.csv, runtime.txt, .LOG; 05_Results\Tables\v3_HC (cycle_a10.py); 05_Results\Images\v3_HC
(figs_hc_v3.py); 00_Plan_and_Decisions\decisions_2026-11-15.txt; 06_Error_Log\error_log.csv.
Usage: python -P build_report_a10_hc.py [--draft]   -> 07_Report\FEA_asm10_routeA_HandcalcReference_v3.docx (draft: _draft)"""
import argparse, csv, os, re, shutil, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(HERE); sys.path.insert(0, HERE)
from build_report_a07 import Doc, r, fr, sb, sp, par, f2          # same document style and OMML helpers as reports v1 / v2
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

V8 = os.path.dirname(R); V2 = os.path.dirname(V8)
CADP = os.path.join(V8, "Route a - thigh strap 150 - side vents (main)", "Pictures")
IMG = os.path.join(R, "05_Results", "Images", "v3_HC"); TAB = os.path.join(R, "05_Results", "Tables", "v3_HC")
K = 0.20699; KMM3 = 206990.0
ANG = [("3.00", "CHK_FB"), ("7.28", "HC_A7.3"), ("8.63", "HC_A8.6"), ("9.78", "HC_A9.8"), ("13.00", "HC_A13.0"),
       ("16.00", "HC_A16.0"), ("19.00", "HC_A19.0")]
CYC = ["HCC_P0", "HCC_P20", "HCC_PROJ", "HCC_P40", "HCC_P60"]
LIM_BL, LIM_COV = 11.1, 37.2

REFS = [
    ("v12", "03_Mechanical_Design\\Design_Reports\\M1-M7 work v12.docx - hand calculation, Part E: Model A (E.2) and Model B "
            "(E.3, Eq. 43) M = p k, k = 206 990 mm3 at d_h = 65 mm; assumptions of Model B."),
    ("brief", "simulation_3_assymbly_10\\00_Plan_and_Decisions\\BRIEF_v3_handcalc_match.md - approved brief of report v3 "
              "(allowed sources, limits table sec. 7, report content sec. 8)."),
    ("dec", "simulation_3_assymbly_10\\00_Plan_and_Decisions\\decisions_2026-11-15.txt - every decision D-A10-* with reason "
            "and effect of the alternatives (Appendix A)."),
    ("err", "simulation_3_assymbly_10\\06_Error_Log\\error_log.csv - every error, warning, stall and non-convergence (Appendix B)."),
    ("cad10", "03_Mechanical_Design\\CAD\\last v2\\last v8\\Route a - thigh strap 150 - side vents (main)\\full asseymbly 10.iam "
              "(actuator-V11, cover.09, side vents); copy and md5 in 01_CAD_copy / 00_Plan_and_Decisions."),
    ("cad11", "03_Mechanical_Design\\CAD\\last v2\\last v9\\Route a - thigh strap 150 - knee joint (main)\\README_CAD_v11_knee_joint.txt "
              "- knee joint: shank group hinged on the knee axis X 4.0573, Y 0; mitred K-shapes; CAD k = 205 345 mm3."),
    ("o2", "02_Biomechanics\\...\\Biomech_Constraints_Option2_PatientRange_13-36_v3.xlsx (Biomech O2 waveform) - knee angle and "
           "project pressure per stance frame; copied as 00_Plan_and_Decisions\\waveform_O2_opt1.csv and the W2 table of deck_a07.py."),
    ("nas", "Autodesk Inventor Nastran 2026 solver Nastran.exe (SOL 106); parameter list and defaults in "
            "C:\\Program Files\\Autodesk\\Inventor Nastran 2026\\Nastran\\Editor.ini."),
    ("prev", "last v6\\simulation_2_assymbly_7\\07_Report\\FEA_asm07_routeA_Report_v2.docx and decisions_2026-11-13.txt - material "
             "data (TPU bladder E 7.2 MPa, nu 0.49; TPU-coated nylon 6.6 cover 498 MPa, fabric orthotropy D-FAB3 / D-FAB4)."),
    ("scr", "simulation_3_assymbly_10\\scripts - mesh_a07.py, deck_a07.py, seal_check_a10.py, run_queue.ps1, post_a07.py, "
            "cycle_a10.py, figs_hc_v3.py, build_report_a10_hc.py, gen_hc.sh."),
]
RN = {k: i + 1 for i, (k, _) in enumerate(REFS)}


def c(*k):
    return "[" + ", ".join(str(RN[x]) for x in k) + "]"


def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def load(run):
    f = os.path.join(R, "04_Runs", run, run + "_results.csv")
    if not os.path.exists(f): return None
    rows = list(csv.DictReader(open(f)))
    for x in rows:
        for k, v in list(x.items()):
            if k not in ("name", "kind"):
                fv = fl(v)
                if fv is not None or v == "": x[k] = fv
        x["converged"] = str(x.get("converged")) in ("True", "1", "1.0")
    return rows


def runtime(run):
    f = os.path.join(R, "04_Runs", run, "runtime.txt")
    if not os.path.exists(f): return None, None
    t = open(f, encoding="utf-8-sig").read()
    s = re.search(r"seconds=(\d+)", t); m = re.search(r"peakMB=(\d+)", t)
    return (int(s.group(1)) if s else None), (int(m.group(1)) if m else None)


def stab_range(run):
    f = os.path.join(R, "04_Runs", run, run + ".LOG")
    if not os.path.exists(f): return None
    last = {}; sc = None
    for line in open(f, errors="replace"):
        if "LOAD LEVEL FOR SUBCASE" in line:
            sc = int(line.split()[4])
        elif "DUE TO STABILIZATION" in line and sc is not None:
            try: last[sc] = float(line.split()[-1])
            except ValueError: pass
    return (min(last.values()), max(last.values())) if last else None


def csvrows(name):
    f = os.path.join(TAB, name)
    if not os.path.exists(f): return []
    rows = list(csv.DictReader(open(f)))
    for x in rows:
        for k, v in list(x.items()):
            fv = fl(v)
            if fv is not None: x[k] = fv
    return rows


def angle_data():
    out = []
    for a, run in ANG:
        rr = load(run)
        if rr is None:
            out.append(dict(angle=float(a), run=run, status="not run")); continue
        vb = [x for x in rr if x["kind"] == "S" and x["converged"]]
        m0 = vb[-1]["M_knee_ext_Nm"] if vb else None; v0 = vb[-1]["V_bladder_mid_cm3"] if vb else None
        for x in rr:
            if x["kind"] != "W" or x["p_kPa"] > 60: continue
            md = (x["M_knee_ext_Nm"] - m0) if (x["converged"] and m0 is not None) else None
            hc = K * x["p_kPa"]
            out.append(dict(angle=float(a), run=run, p=x["p_kPa"], conv=x["converged"], M=x["M_knee_ext_Nm"] if x["converged"] else None,
                            M0=m0, V0=v0, V=x["V_bladder_mid_cm3"] if x["converged"] else None, dev=md, hc=hc,
                            ratio=(md / hc if md is not None else None), vmb=x.get("vm_max_bladder_MPa"), vmc=x.get("vm_max_cover_MPa"),
                            it=x.get("iterations"), bis=x.get("bisections"), status="ok"))
        if not vb:
            out.append(dict(angle=float(a), run=run, status="vented flexion not converged"))
    return out


def decisions():
    f = os.path.join(R, "00_Plan_and_Decisions", "decisions_2026-11-15.txt")
    txt = open(f, encoding="utf-8", errors="replace").read().splitlines()
    out, cur = [], None
    for ln in txt:
        m = re.match(r"^(D-A10-[A-Z0-9]+)\s+(.*)$", ln)
        if m:
            if cur: out.append(cur)
            cur = [m.group(1), m.group(2).strip()]
        elif cur and ln.startswith("  "):
            cur[1] += " " + ln.strip()
        elif cur and not ln.strip():
            out.append(cur); cur = None
    if cur: out.append(cur)
    return out


def errors(first=60):
    f = os.path.join(R, "06_Error_Log", "error_log.csv")
    rows = list(csv.reader(open(f, encoding="utf-8", errors="replace")))[1:]
    out = []
    for x in rows:
        m = re.match(r"E-(\d+)", x[0] if x else "")
        if m and int(m.group(1)) >= first:
            out.append(x)
    return out


def short(t, n):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[:n - 3].rstrip() + "..."


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--draft", action="store_true"); a = ap.parse_args()
    out = os.path.join(R, "07_Report", "FEA_asm10_routeA_HandcalcReference_v3%s.docx" % ("_draft" if a.draft else ""))
    if os.path.exists(out) and not a.draft:
        sys.exit("exists - never overwrite a delivered report: " + out)
    for nm in ("asm10_iso.png", "actV11_iso.png", "asm10_device.png"):
        if os.path.exists(os.path.join(CADP, nm)): shutil.copy2(os.path.join(CADP, nm), os.path.join(IMG, "cad_" + nm))
    AD = angle_data(); CM = csvrows("cycle_moment.csv")
    RUNS = [run for _, run in ANG] + CYC
    LD = {run: load(run) for run in RUNS}
    D = Doc()

    # ================================================================= title
    D.P("SDP-2 (MMNB) soft knee exoskeleton - right leg, route (a), full asseymbly 10", bold=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    D.P("FEA of the inflatable knee actuator - idealised hand-calculation reference, 0-60 kPa", bold=True, size=16,
        align=WD_ALIGN_PARAGRAPH.CENTER)
    D.P("Report v3 (HC set) - Inventor Nastran SOL 106, large displacement, 16-17 Nov 2026", size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    p = D.P("IDEALISED REFERENCE: rigid leg halves on the knee hinge, bladder bonded to them, no tissue, no straps, no friction. "
            "These results check the hand calculation and the moment extraction; they are not the moment of the real device on a leg.",
            bold=True, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    D.P("Run folder: 03_Mechanical_Design\\CAD\\last v2\\last v8\\simulation_3_assymbly_10 (paths below are relative to it).",
        italic=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

    # ================================================================= 0 nomenclature
    D.H("Symbols, abbreviations and names used in this report")
    D.P("Every symbol, short name and run name used in the text, tables and figures is defined here once. Units: N, mm, MPa, "
        "kPa, N m, degrees (deg) unless stated.")
    sym = [["p", "gauge air pressure inside the bladder (above atmosphere)", "kPa"],
           ["θ (theta)", "knee flexion angle; + = knee bent (shank turned towards +x)", "deg"],
           ["k", "first moment of area of the bladder cavity section at the knee line about the knee axis = dV/dθ (hand calc: "
                 "206 990 mm3)", "mm3"],
           ["p k", "hand-calculation knee moment of Model B (0.207 N m per kPa)", "N m"],
           ["M_z", "knee extension moment in the hand calculation (about the knee axis z)", "N m"],
           ["M_knee", "knee moment from the FEA: sum of the shank-half reaction forces F times their lever (x - H) about the knee "
                      "centre, + = extension", "N m"],
           ["M vented, M(0, θ)", "M_knee of the vented bladder (p = 0) at the same knee angle = passive bending of the empty device", "N m"],
           ["M_dev", "device moment = M_knee(p, θ) - M_knee(0, θ): the part of the knee moment produced by the air pressure", "N m"],
           ["FEA / HC, ratio", "M_dev / (p k); 1.00 = FEA equals the hand calculation", "-"],
           ["V", "bladder volume enclosed by the shell mid-surface", "mL (= cm3)"],
           ["dV, dθ, dA, ρ", "change of volume; change of knee angle (rad); area element of the cavity section; its distance from the "
                             "knee axis", "mm3, rad, mm2, mm"],
           ["d_h", "distance of the knee axis in front of the back skin (hand calc 65 mm)", "mm"],
           ["H", "knee centre in the model: x = 4.0573 mm, y = 0 (the knee axis is the z line through H)", "mm"],
           ["x, y, z", "model axes: x posterior (towards the bladder), y along the leg (+ = thigh, - = shank, 0 = knee line), "
                       "z medial-lateral", "mm"],
           ["s(y)", "share of the knee rotation given to a band-floor grid: 0 at y = +25 (thigh side) to 1 at y = -25 (shank side)", "-"],
           ["E, E_leg, E_hoop", "Young's modulus; for the orthotropic fabric / fold band: along the leg and round the hoop", "MPa"],
           ["ν (nu), G, t, ρ_m", "Poisson's ratio; shear modulus; shell thickness; mass density", "-, MPa, mm, t/mm3"],
           ["vm", "von Mises equivalent stress (largest over the shell top and bottom surfaces)", "MPa"],
           ["FoS", "factor of safety = allowable stress / computed von Mises stress", "-"],
           ["U, U - p V", "elastic strain energy; potential energy of the pressurised bladder at fixed angle (lower = more stable)", "J"]]
    D.T(["Symbol", "Meaning", "Unit"], sym, "Symbols.", size=7.5, widths=[3.0, 12.0, 2.5])
    abb = [["FEA", "finite-element analysis"], ["HC", "hand calculation (M1-M7 work v12 " + c("v12") + ")"],
           ["Model A / Model B", "the two hand-calculation models of v12 Part E: A = lower bound (pad pushes, ring pulls back), "
                                 "B = rigid halves, M = p k (upper bound, checked here)"],
           ["CAD", "computer-aided design model (Autodesk Inventor)"],
           ["Core model", "the FEA model of this report: bladder + cover on two rigid leg halves, no tissue / pad / straps"],
           ["Fold band", "the 50 mm wide strip of bladder wall around the knee line (|y| < 25 mm) with 1 % axial modulus, standing in "
                         "for the fold (mitre) of the hand calculation"],
           ["Main / squeezed / relaxed fold state", "stable shapes of the folded bladder found by the solver at the same angle and "
                                                    "pressure: main = shape at the window onset; squeezed = less volume, more moment, "
                                                    "higher energy; relaxed = more volume, less moment, lower energy"],
           ["Stance %", "time from heel strike as a percentage of the stance phase of gait"],
           ["Window, onset, peak, offset", "assist window 13-36 % stance; onset 13 % (3.28 deg); peak knee angle 21 % (5.78 deg); "
                                           "offset 36 % (4.63 deg)"],
           ["Biomech O2", "the option-2 knee-angle and pressure waveform of the biomechanics hand-over " + c("o2")],
           ["Project profile (PROJ)", "the project pressure history of the O2 waveform: 6.9 kPa at 13 % -> 20.0 kPa at 21 % -> 2.8 kPa at 36 %"],
           ["Phase letters S / F / W / V", "S = vented flexion before the window; F = fill steps at 13 %; W = window step; "
                                           "V = vent phase (not used, stance limited to 36 %)"],
           ["VREF", "last step of a fixed-angle case: the bladder vented again at the case angle"],
           ["M0", "the finite-element mesh used (coarsest of the meshes M0 / M1 / M2 built for this device)"],
           ["TPU", "thermoplastic polyurethane (bladder: Elastollan 1185A; cover coating)"],
           ["SOL 106", "Nastran nonlinear static solution sequence"],
           ["LGDISP", "Nastran parameter for large displacement (geometry updated, pressure follows the deforming surface)"],
           ["SPC / SPCD", "single-point constraint (fixed degree of freedom) / prescribed displacement used to turn the shank half"],
           ["PLOAD4", "Nastran pressure load on shell faces (here the air pressure on all 2052 bladder shells)"],
           ["BSCONP", "Nastran surface-to-surface contact pair (here bladder <-> cover, frictionless)"],
           ["MAT1 / MAT8", "isotropic / orthotropic shell material card"],
           ["PSHELL", "shell property card (thickness, membrane and bending materials)"],
           ["CQUAD4 / CTRIA3", "4-node / 3-node shell elements"],
           ["MCID", "material coordinate system of a shell element (gives the fabric's leg direction)"],
           ["NLPARM", "Nastran nonlinear iteration control (increments, iterations, convergence tolerances, bisections)"],
           ["SLINESTABKSFACT", "Nastran slide-line contact stabilisation factor (here 1e-4)"],
           ["HEXREDORD", "Nastran option for reduced-order hexahedra (switched off)"],
           ["E5075 / E5076", "solver messages: load increment bisected / maximum number of bisections reached (step not converged)"],
           ["RAM", "working memory given to the solver (2000 MB)"],
           ["D-A10-xxx", "decision record in decisions_2026-11-15.txt (Appendix A)"],
           ["E-xx", "entry of the error log error_log.csv (Appendix B)"],
           ["[n]", "reference number (list at the end)"]]
    D.T(["Abbreviation / name", "Meaning"], abb, "Abbreviations and terms.", size=7.5, widths=[4.2, 13.3])
    runs_ = [["CHK_FB", "check run that fixed the final set-up; fixed angle 3 deg, 0-60 kPa (identical deck to HC_A3.0, used as the 3 deg case)"],
             ["CHK_STAB1 / STAB2 / BLEND / END / BED", "earlier check runs on 3 deg testing one fix each (Section 6)"],
             ["HC_A<angle>", "fixed-angle case of the hand-calc (HC) reference at <angle> deg (7.3 = 7.28, 8.6 = 8.63, 9.8 = 9.78)"],
             ["HCC_P<p>", "gait-cycle run of the HC reference at constant window pressure <p> kPa (P0 = vented)"],
             ["HCC_PROJ", "gait-cycle run with the project pressure profile"],
             ["B0, B0C, CHK_CORE", "first reference attempt (superseded, Section 6)"],
             ["RC_*, REAL_*", "real-case decks (soft tissue, straps, friction 0.37) - built, held, NOT run"]]
    D.T(["Run name", "Meaning"], runs_, "Run names.", size=7.5, widths=[4.8, 12.7])

    # ================================================================= 1 summary
    D.H("1. Summary")
    ok_ang = [x for x in AD if x.get("ratio") is not None]
    D.P("This report shows what was simulated, how the model was set up and made to converge, and what it gives. The question it "
        "answers is narrow on purpose: if the leg is replaced by two rigid halves turning about the knee axis and the bladder is "
        "glued to them - exactly the assumptions of the hand calculation (Model B, M = p k " + c("v12") + ") - does the finite-element "
        "model give the same knee moment? If it does, the hand calculation and the way the moment is read from the FEA are both "
        "confirmed, and any shortfall of the real device can be traced to the real-case effects (soft tissue, straps, slip), "
        "not to the formula.")
    rows = []
    for x in ok_ang:
        if x["p"] in (20.0, 40.0, 60.0):
            rows.append(["%.2f" % x["angle"], "%.0f" % x["p"], f2(x["dev"]), f2(x["hc"]), f2(x["ratio"]), "%+.0f %%" % (100 * (x["ratio"] - 1))])
    if rows:
        D.T(["Knee angle (deg)", "p (kPa)", "FEA device moment (N m)", "Hand calc p k (N m)", "FEA / HC", "Difference"], rows,
            "Key result - fixed-angle cases (bend the knee with the bladder vented, then inflate). Device moment = knee moment at p "
            "minus the vented moment at the same angle.", size=8.5, widths=[2.4, 1.6, 3.2, 3.0, 2.2, 2.2])
    cm21 = [x for x in CM if x.get("phase") == "W" and x.get("stance_pct") == 21 and x.get("run", "").startswith("HCC_") and
            x.get("ratio_FEA_to_hc") not in (None, "")]
    bl = []
    if ok_ang:
        r3 = [x["ratio"] for x in ok_ang if abs(x["angle"] - 3.0) < 0.01]
        rhi = [x for x in ok_ang if x["angle"] > 5]
        bl.append("At 3 deg the FEA reproduces the hand calculation within %s over 20-60 kPa (FEA / p k = %s). The linear "
                  "growth of the moment with pressure, which is the core of Model B, is confirmed." %
                  ("%.0f-%.0f %%" % (100 * (min(r3) - 1), 100 * (max(r3) - 1)) if r3 else "-", " / ".join(f2(v) for v in r3)))
        if rhi:
            bl.append("At larger angles the FEA moment is above p k (FEA / p k %s-%s at %s-%s deg). The reason is geometric, not an "
                      "error: the FEA bladder inflates to its cover and bulges in the fold band, so its effective first moment of "
                      "area k grows with angle, while the hand calculation keeps the k of the undeformed inner cavity (section 8)." %
                      (f2(min(x["ratio"] for x in rhi)), f2(max(x["ratio"] for x in rhi)),
                       "%.2f" % min(x["angle"] for x in rhi), "%.2f" % max(x["angle"] for x in rhi)))
    if cm21:
        bl.append("Over the gait window (13-36 % stance, knee 3.28-5.78 deg) the device moment at the peak frame (21 %) is " +
                  "; ".join("%s: %s N m = %s x p k" % (x["run"], f2(x["M_device_Nm"]), f2(x["ratio_FEA_to_hc"])) for x in cm21) + ".")
    bl.append("The moment does not depend on pressure alone: the folded bladder has more than one stable shape at the same angle and "
              "pressure (section 7.3). In the project-profile run the moment jumps between about 9 and 14 N m. The lower-energy "
              "shape is used for the comparison; the others are reported and marked.")
    bl.append("Bladder and cover stresses stay far below the material limits up to 60 kPa (section 7.5).")
    bl.append("Not done, by the owner's decision: pressures above 60 kPa, stance after 36 %, and the real case (soft tissue, straps, "
              "friction 0.37). The real-case decks are built and held, not run.")
    for t in bl: D.B(t)

    # ================================================================= 2 scope
    D.H("2. Task, scope and what changed during the work")
    D.P("The owner asked for an FEA whose assumptions match the hand calculation, labelled as an idealised reference " + c("brief") +
        ". The scope was set step by step by the owner during the runs (all recorded in " + c("dec") + "):")
    for t in ["CAD: full asseymbly 10 (side vents) " + c("cad10") + "; the inlet tube supplies the air, the two vent tubes are closed "
              "by valves until venting, no tube leaks (D-A10-SEAL, D-A10-SUPPLY).",
              "The actuator is centred on the knee axis and bends with the knee; the moment is taken about the knee centre "
              "(CAD v11 knee joint " + c("cad11") + ", D-A10-CADV11, D-A10-MOM).",
              "Gait cycle: the bladder fills by the onset at 13 % stance and holds the test pressure through the window 13-36 %; the "
              "knee follows the Biomech O2 waveform " + c("o2") + " (D-A10-CYC, D-A10-FILL13).",
              "Pressures: 0, 20, 40, 60 kPa and the project profile (6.9 -> 20 -> 2.8 kPa). Final pressure limited to 60 kPa by the owner "
              "(D-A10-P60); the 80 / 100 kPa decks were removed from the queue, not run.",
              "Fixed-angle cases: 3, 7.28, 8.63, 9.78, 13, 16, 19 deg (D-A10-ANG; 7.28 / 8.63 / 9.78 = window angles + 4 deg margin).",
              "Stance limited to 36 % (end of the window, owner); the later cycle runs use every 3rd stance frame to save time "
              "(D-A10-C36, D-A10-C3).",
              "Real case (soft tissue, straps, friction 0.37): held, not run (owner)."]:
        D.B(t)

    # ================================================================= 3 hand calc
    D.H("3. The hand calculation being checked")
    D.P("Model B of the hand calculation " + c("v12") + " treats the thigh and shank as rigid halves that turn about the knee axis. "
        "The bladder cavity is cut by the plane at the knee line; when the knee flexes by d theta the cavity loses volume k d theta. "
        "With a constant gauge pressure p, the virtual work of the air equals the work of the knee moment:")
    D.EQ(sb(r("M"), r("z")) + r(" = p ") + fr(r("dV"), r("d") + r("θ")) + r(" = p k,   k = ") + "<m:nary><m:naryPr><m:chr m:val=\"∫\"/><m:limLoc m:val=\"subSup\"/><m:subHide m:val=\"1\"/><m:supHide m:val=\"1\"/></m:naryPr><m:sub/><m:sup/><m:e>" + r("ρ dA") + "</m:e></m:nary>",
         "M_z knee extension moment (N m); p gauge pressure (Pa); V cavity volume; theta knee flexion (rad); rho distance of the "
         "area element dA of the cavity section at y = 0 from the knee axis. v12: k = 206 990 mm3 at d_h = 65 mm, so p k = 0.207 N m "
         "per kPa (4.14 N m at 20 kPa, 8.28 at 40, 12.42 at 60). CAD v11 gives k = 205 345 mm3 (-0.8 %) " + c("cad11") + ".")
    D.P("Model B assumptions: rigid halves; the bladder halves turn with them (no pad shear, no tissue deformation, no slip); no "
        "losses; constant pressure; quasi-static. Model B is the upper bound of the hand calculation (Model A, the lower bound, gives "
        "0.28 N m at 20 kPa) " + c("v12") + ". The FEA in this report reproduces Model B's world, so p k is the value it should meet.")

    # ================================================================= 4 model
    D.H("4. Model and set-up")
    D.H("4.1 Geometry", 2)
    D.P("The bladder (actuator-V11) and its fabric cover (cover.09) of full asseymbly 10 " + c("cad10") + " are meshed from the same "
        "build code that made the CAD (geo8.py / geo_A150.json via mesh_a07.py), because Inventor's own mesher failed on this assembly "
        "in the earlier work " + c("prev") + ". The three ports (inlet + two side vents) are modelled as closed wall: the valves are "
        "closed during inflation and the tubes carry no load (D-A10-SEAL, D-A10-TUBES). The knee axis is the Z line through "
        "X = 4.0573 mm, Y = 0 (65 mm in front of the back skin = d_h of the hand calculation); flexion turns the shank half towards +X.")
    D.F(os.path.join(IMG, "cad_asm10_iso.png"), "CAD full asseymbly 10 (route a, side vents) - the device whose bladder and cover are modelled.", 11)
    D.F(os.path.join(IMG, "cad_actV11_iso.png"), "Bladder actuator-V11 (CAD). Inlet on the top face, two vents on the sides - closed in the model.", 9)
    D.H("4.2 The core model (what is in, what is out)", 2)
    D.P("To match Model B, the model keeps only the parts the hand calculation has: the bladder, the cover and two rigid leg "
        "halves. Pad, webbing, hooks, Velcro, straps and soft tissue are left out (D-A10-CORE). The bladder floor and the cover "
        "sewing flange are bonded to the rigid halves outside a 50 mm fold band (|y| < 25 mm) around the knee line. In that band the "
        "bladder wall is given 1 % of its modulus along the leg (full modulus round the hoop), so it folds like the mitre of the "
        "hand calculation and carries no axial force across the crease; the band floor follows a smoothly bent copy of the leg "
        "surface (bonded, D-A10-FBOND).")
    D.F(os.path.join(IMG, "mesh_core_model.png"), "Core model mesh (M0): bladder (blue), fold band (orange), cover (grey, transparent). "
        "Undeformed, 0 deg.", 9.5)
    msh = [["Bladder body / end caps (CQUAD4 + CTRIA3, PSHELL 8)", "1824 / 228", "t 2.0 mm, mid-surface; mean edge 4.3 mm (1.8-5.6)"],
           ["  of which fold band |y| < 25 mm (PSHELL 12)", "513", "1 % axial modulus (MAT8 12)"],
           ["Cover body (PSHELL 9) / end caps (PSHELL 11) / sewing flange (PSHELL 10)", "1610 / 180 / 204", "t 0.43 mm; mean edge 4.5 mm"],
           ["Bladder-cover contact (BSCONP, frictionless)", "80 pairs", "117 577 slave x master segment products"],
           ["Grids / elements in the deck", "26 777 / 4046", "bladder grids 2026; bonded: floor 168 (78 in the band), flange 272"],
           ["Rigid halves", "836 thigh / 748 shank grids", "all degrees of freedom prescribed (SPC / SPCD)"]]
    D.T(["Item", "Count", "Note"], msh, "Mesh of the core model (mesh M0, from the run files).", size=8, widths=[7.5, 3.5, 6.5])
    D.H("4.3 Materials and properties", 2)
    mat = [["Bladder wall", "TPU (Elastollan 1185A)", "MAT1 7: E 7.2 MPa, nu 0.49, rho 1.12e-9 t/mm3", "PSHELL 8, t 2.0", c("prev")],
           ["Bladder fold band", "same TPU, folding", "MAT8 12: E_leg 0.072, E_hoop 7.2 MPa, nu12 0.0049, G 0.024 MPa", "PSHELL 12, t 2.0",
            "engineering choice D-A10-CORE"],
           ["Cover body", "TPU-coated nylon 6.6 fabric", "MAT8 11: E_leg 4.98, E_hoop 498 MPa, nu12 0.0035, G 4.98 MPa; bending MAT1 9",
            "PSHELL 9, t 0.43", c("prev") + " D-FAB4"],
           ["Cover end caps, flange, end-facing body", "same fabric", "MAT1 9: E 498 MPa, nu 0.35 (isotropic)", "PSHELL 10 / 11, t 0.43",
            "D-A10-ENDISO"],
           ["Leg halves", "-", "rigid (prescribed motion)", "-", "Model B"]]
    D.T(["Part", "Material", "Model data", "Property", "Source"], mat, "Materials. Units N, mm, MPa, t.", size=7.5,
        widths=[3.0, 3.0, 6.3, 2.6, 2.6])
    D.P("Stress limits used for the factor of safety " + c("brief") + ": bladder wall von Mises 11.1 MPa, cover 37.2 MPa.")
    D.H("4.4 Boundary conditions and kinematics", 2)
    for t in ["Thigh half fixed. Shank half rotated about the knee axis by prescribed displacements (SPCD) - the exact rigid rotation, "
              "so the bladder end on the shank turns with the knee.",
              "Bladder floor and cover flange: bonded to the halves (shared prescribed motion) outside the band; inside the band the "
              "floor grids turn by theta x s(y), s = 0 at y = +25 (thigh) to 1 at y = -25 (shank).",
              "Knee moment: sum over the shank-half reactions of (x - H) x F about the knee centre H = (4.0573, 0), z component, "
              "+ = extension (post_a07.py).",
              "Gravity and inertia off (quasi-static, as the hand calculation)."]:
        D.B(t)
    D.EQ(sb(r("M"), r("dev")) + par(r("p, θ")) + r(" = ") + sb(r("M"), r("knee")) + par(r("p, θ")) + r(" − ") + sb(r("M"), r("knee")) + par(r("0, θ")) +
         r(",    ratio = ") + fr(sb(r("M"), r("dev")), r("p k")),
         "Device moment = what the air adds to the moment of the vented (0 kPa) device at the same knee angle; the vented part is the "
         "passive bending of the empty bladder and cover. In the cycles M(0, theta) comes from run HCC_P0 at the same frame; after the "
         "peak angle it is read from the loading branch of HCC_P0 by angle (D-A10-P0BR, E-126).")
    D.H("4.5 Pressure loading", 2)
    D.P("Air pressure is a follower load (PLOAD4) on all 2052 bladder shells; seal_check_a10.py confirms for every deck a closed shell "
        "(0 free edges) with pressure on every bladder element and on nothing else. Pressure is prescribed (regulated supply, vents "
        "closed), as in Model B (D-A10-SUPPLY).")
    D.H("4.6 Load sequences", 2)
    seq = [["Fixed-angle case (CHK_FB = 3 deg, HC_A*)", "flex vented to the angle (sub-steps <= 2.5 deg) -> 20 -> 40 -> 60 kPa -> vented (VREF)",
            "M(p) - M(vented, same angle) vs p k"],
           ["Cycle HCC_P0 / P20", "stance 1-50 % every 1 %: vented flexion 1-12 %, fill in 5 steps at 13 %, window 13-36 % at p, vent 37-50 %",
            "reported to 36 % only"],
           ["Cycle HCC_PROJ", "as P20 to 36 % with the project profile p(t) (6.9 at 13 % -> 20.0 at 21 % -> 2.8 kPa at 36 %)", "41 subcases"],
           ["Cycle HCC_P40 / P60", "frames 3, 6, 9, 12 (vented), fill at 13, then 13, 15, 18, 21, 24, 27, 30, 33, 36 %", "18 subcases"]]
    D.T(["Run type", "Sequence", "Note"], seq, "Load sequences. Knee angle per frame from the Biomech O2 waveform " + c("o2") +
        ": 3.28 deg at 13 %, peak 5.78 deg at 21 %, 4.63 deg at 36 %.", size=7.5, widths=[4.0, 9.0, 4.0])
    D.H("4.7 Solver settings", 2)
    D.P("Inventor Nastran 2026, SOL 106 nonlinear static, PARAM LGDISP 1 (large displacement, follower pressure), each subcase starting "
        "from the previous one " + c("nas") + ". NLPARM: 2-8 increments per subcase, ITER, stiffness update every iteration, at most 25 "
        "iterations, convergence on displacement, load and work (0.01 / 0.01 / 0.001), up to 10 bisections. Slide-line stabilisation "
        "PARAM SLINESTABKSFACT 1e-4 (D-A10-STAB). Full-integration hexes (HEXREDORD OFF). Run one job at a time with RAM 2000 MB and 4 "
        "processors on a 7.7 GB PC; a watchdog stops a run whose load level does not advance for 45 min (run_queue.ps1).")

    # ================================================================= 5 assumptions
    D.H("5. Assumptions - hand calculation and FEA side by side")
    asm = [["Leg", "two rigid halves on the knee hinge", "same (rigid, prescribed rotation)", "same"],
           ["Knee axis", "Z through O, d_h 65 mm", "Z through X 4.0573, Y 0 (= d_h 65)", "same"],
           ["Bladder attachment", "halves of the cavity turn with thigh / shank", "floor and flange bonded outside the fold band", "same"],
           ["Crease", "mitre at the bisector, wall carries nothing across", "50 mm band with 1 % axial modulus; floor follows a smooth bend", "close (band instead of a sharp mitre)"],
           ["Cavity section k", "inner cavity, undeformed, 206 990 mm3", "mid-surface of a 2 mm wall, inflates to the cover", "NOT the same - FEA k larger, grows with p and angle"],
           ["Pressure", "constant, uniform", "prescribed, uniform, follower", "same"],
           ["Cover", "not in the formula", "fabric cover, frictionless contact with the bladder", "FEA adds the cover"],
           ["Tissue, pad, straps, friction", "none", "none", "same (real case not run)"],
           ["Dynamics", "quasi-static", "static, path-following", "same"],
           ["Passive bending of the empty device", "zero", "computed (vented run) and subtracted", "handled by the device-moment definition"]]
    D.T(["Item", "Hand calc (Model B)", "FEA core model", "Match"], asm, "Assumptions compared.", size=7.5, widths=[3.2, 4.6, 5.6, 4.1])
    D.P("Engineering assumptions added by the FEA (each with its reason in Appendix A): fold-band modulus 1 % (D-A10-CORE); band width "
        "50 mm (D-A10-CORE); contact stabilisation 1e-4 (D-A10-STAB); isotropic end-facing cover elements (D-A10-ENDISO); bonded band "
        "floor (D-A10-FBOND); vented baseline by angle after the peak (D-A10-P0BR); fold-state rule (D-A10-BR).")

    # ================================================================= 6 convergence story
    D.H("6. Making the model converge - problems, causes, fixes and evidence")
    D.P("The first reference runs (16 Nov night, B0 stack and the first core model) converged only to about 13-20 kPa. Each failure was "
        "traced in the solver logs before anything was changed, and each fix was tested alone on the 3 deg case. The table lists the "
        "chain; full entries are in Appendix B " + c("err") + ".")
    fx = [["E-64..E-66", "Full stack (pad + skin + straps) on rigid halves locked the crease, about 50 N m/deg", "pad links across the knee line", "core model (bladder + cover only)", "D-A10-CORE"],
          ["E-67..E-71", "Fill above ~15 kPa failed; fold band ballooned", "inflating the fold at small angles; no tension-only shell", "fill at 13 % only", "D-A10-FILL13"],
          ["E-108", "Stall: closed-contact share 14.8 / 14.9 / 15.0 % and displacement 11.153 / 11.158 mm alternate every iteration", "bladder-cover contact chatter in the band", "SLINESTABKSFACT 1e-4 (0.01 rejected: vented 6.16 vs 1.24 N m)", "D-A10-STAB"],
          ["E-109", "40 kPa failed: floor ballooned into a 7.4 mm slot at the knee line", "support missing under the band floor", "blended support (later replaced)", "D-A10-BLEND"],
          ["E-112", "Corner hinge at the shank-end cover (grids 25052/53, 25020)", "end-facing elements had an undefined fabric axis", "isotropic end-facing cover", "D-A10-ENDISO"],
          ["E-117", "80 kPa: floor ridge (rotation +-0.5 rad)", "support 4.2 mm below the floor", "rigid bed - rejected (new chatter at 34 kPa)", "D-A10-BED"],
          ["E-120", "-", "every floor-contact variant failed", "band floor bonded to a smoothly bent leg surface", "D-A10-FBOND"],
          ["E-123", "~70 kPa: cover end corner 25052", "free bottom edge of the cover end caps (also in the full model)", "accepted: above the 60 kPa range", "D-A10-P60"],
          ["E-124 / E-126", "HCC_P0 stopped at 24 %", "empty bladder snapped to another wrinkle shape when the knee reversed", "vented baseline from the loading branch by angle", "D-A10-P0BR"],
          ["E-129", "Converged runs with moment jumps of up to 5 N m", "several stable fold shapes", "fold-state flag; lower-energy shape used", "D-A10-BR"]]
    D.T(["Log", "Symptom", "Root cause", "Fix", "Decision"], fx, "Convergence problems and fixes.", size=7, widths=[1.8, 4.6, 3.9, 4.3, 2.4])
    fb = load("CHK_FB")
    if fb:
        rows = []; m0 = [x for x in fb if x["kind"] == "S" and x["converged"]][-1]["M_knee_ext_Nm"]
        for x in fb:
            if x["kind"] in ("S", "W"):
                d = (x["M_knee_ext_Nm"] - m0) if (x["converged"] and x["kind"] == "W") else None
                rows.append([x["name"], "yes" if x["converged"] else "NO", f2(x["M_knee_ext_Nm"]), f2(d), f2(K * x["p_kPa"]) if x["kind"] == "W" else "-",
                             f2(d / (K * x["p_kPa"])) if d is not None else "-", "%d / %d" % (x["iterations"] or 0, x["bisections"] or 0)])
        D.T(["Step", "Conv.", "M_knee (N m)", "Device (N m)", "p k (N m)", "Ratio", "Iter. / bisect."], rows,
            "Verification of the final set-up on the 3 deg case (CHK_FB; same deck as HC_A3.0). 80 kPa stopped at about 70 kPa (E-123).",
            size=8, widths=[4.5, 1.3, 2.2, 2.2, 2.0, 1.6, 2.2])

    # ================================================================= 7 runs + status
    D.H("7. Results")
    D.H("7.1 Run matrix and solver status", 2)
    st = []
    for run in RUNS:
        rr = LD.get(run)
        if rr is None:
            st.append([run, "not run", "-", "-", "-", "-", "-"]); continue
        sec, mb = runtime(run); sr = stab_range(run)
        nconv = sum(1 for x in rr if x["converged"])
        st.append([run, "%d / %d" % (nconv, len(rr)), "%.1f" % (sec / 3600.0) if sec else "-", str(mb or "-"),
                   "%d" % sum(int(x["iterations"] or 0) for x in rr), "%d" % sum(int(x["bisections"] or 0) for x in rr),
                   ("%.0f-%.0f" % sr) if sr else "-"])
    D.T(["Run", "Subcases converged", "Time (h)", "Peak RAM (MB)", "Iterations", "Bisections", "Stabilisation share of contact energy (%)"],
        st, "Solver status of every run of the final set-up (0-60 kPa). Not converged = the solver stopped (E5076) and the run ended "
        "there; the converged subcases are kept.", size=7.5, widths=[2.6, 2.4, 1.6, 2.0, 2.0, 2.0, 4.6])
    D.F(os.path.join(IMG, "solver_iterations.png"), "Newton iterations per subcase for every run (solver effort; 0 = not reached).", 16)
    D.P("Reading the stabilisation column: the contact stabilisation is a numerical spring that the solver adds on the slide line. A "
        "share of 13-36 % of the (very small) contact strain energy is large in relative terms, but its effect on the moment was "
        "measured directly: on the vented 3 deg case it adds 0.26 N m (1.24 -> 1.50 N m), and it cancels in the device moment except "
        "for its pressure-dependent part (D-A10-STAB). The value 0.01 was rejected because it acted as a structural spring.")

    # 7.2 angle cases
    D.H("7.2 Fixed-angle cases - FEA against p k", 2)
    rows = []
    for x in AD:
        if x.get("status") != "ok":
            rows.append(["%.2f" % x["angle"], x["run"], x.get("status"), "", "", "", "", "", ""]); continue
        rows.append(["%.2f" % x["angle"], x["run"], "%.0f" % x["p"], "yes" if x["conv"] else "NO", f2(x["M0"]), f2(x["M"]), f2(x["dev"]),
                     f2(x["hc"]), (f2(x["ratio"]) + " (%+.0f %%)" % (100 * (x["ratio"] - 1))) if x["ratio"] is not None else "-"])
    D.T(["Angle (deg)", "Run", "p (kPa)", "Conv.", "M vented (N m)", "M at p (N m)", "Device (N m)", "p k (N m)", "FEA / HC"], rows,
        "Fixed-angle cases, 20-60 kPa. Difference = (FEA - HC) / HC.", size=7.5, widths=[1.5, 2.0, 1.3, 1.2, 2.1, 2.0, 2.0, 1.9, 3.0])
    D.F(os.path.join(IMG, "angle_cases_moment.png"), "Left: device moment against pressure for each angle, FEA (solid) and hand "
        "calculation p k (dashed). Right: FEA / p k against knee angle; hollow markers = cycle frames 13-21 % (loading, main fold state).", 16.5)
    # 7.3 cycles
    D.H("7.3 Gait cycles - window 13-36 % stance", 2)
    D.P("The cycles apply the real knee-angle history of the stance phase with the bladder at the test pressure. Unlike the fixed-angle "
        "cases, the bladder is pressurised while the knee bends and straightens, so the fold of the bladder in the crease can settle "
        "in different shapes along the way.")
    keyf = (13, 15, 18, 21, 24, 27, 30, 33, 36)
    rows = []
    for run in CYC[1:]:
        for x in CM:
            if x.get("run") == run and x.get("phase") == "W" and x.get("stance_pct") in keyf:
                fs = x.get("fold_state")
                rows.append([run, "%d" % x["stance_pct"], f2(x["theta_deg"]), f2(x["p_kPa"], 1), f2(x["M_knee_Nm"]),
                             f2(x["M_vented_Nm"]), f2(x["M_device_Nm"]), f2(x["M_handcalc_Nm"]), f2(x["ratio_FEA_to_hc"]),
                             "main" if fs in (0, 0.0) else ("squeezed" if isinstance(fs, float) and fs > 0 else ("relaxed" if isinstance(fs, float) else "-")),
                             f2(x.get("V_bladder_mL"), 1)])
    D.T(["Run", "Stance %", "Angle (deg)", "p (kPa)", "M_knee", "M vented", "Device", "p k", "Ratio", "Fold state", "V (mL)"], rows,
        "Gait-cycle results at the key frames (moments in N m). Fold state: main = the shape at the window onset; squeezed = a "
        "higher-energy shape with less volume (not used for the ratio); relaxed = a lower-energy shape with more volume.",
        size=7, widths=[1.9, 1.2, 1.3, 1.2, 1.4, 1.5, 1.4, 1.3, 1.3, 1.7, 1.4])
    D.F(os.path.join(IMG, "cycles_moment.png"), "Left: device moment over the window for each cycle run, FEA markers (crosses = other "
        "fold state) and p k (dashed). Right: the inputs - bladder pressure per run and knee angle (dotted).", 16.5)
    D.F(os.path.join(IMG, "fold_states_proj.png"), "Evidence of the fold states in HCC_PROJ: at almost the same angle and pressure the "
        "solver finds a shape with about 7 mL less volume and about 5 N m more moment (shaded frames).", 13)
    D.P("What the fold states mean. Both shapes are converged static solutions with a positive-definite stiffness matrix (no negative "
        "terms on the factor diagonal). In the squeezed shape the bladder outer wall and the cover sit about 1.7 mm lower over "
        "y = -72..58 mm and the reactions at the bladder ends are about 45 % larger (diagnostics in E-129). That shape has more strain "
        "energy and less air volume, so its potential energy U - p V is higher: a real bladder, which is shaken by every step, would "
        "drop into the lower-energy shape. The solver switches shape in steps that need many iterations, so the switch is a numerical "
        "path effect. For this reason the device moment is quoted for the main shape; the others are kept in the tables, marked.")
    # 7.4 P-V
    D.H("7.4 Pressure and volume", 2)
    rows = []
    for a_, run in ANG:
        xs = [x for x in AD if x["run"] == run and x.get("status") == "ok"]
        if not xs: continue
        rows.append(["%s" % a_, f2(xs[0]["V0"], 1)] + [f2(next((x["V"] for x in xs if x["p"] == p_), None), 1) for p_ in (20.0, 40.0, 60.0)])
    if rows:
        D.T(["Angle (deg)", "V at 0 kPa (mL)", "V at 20 kPa", "V at 40 kPa", "V at 60 kPa"], rows,
            "Bladder mid-surface volume at fixed angle (the cavity volume plus half the wall).", size=8, widths=[2.5, 3.0, 3.0, 3.0, 3.0])
    D.F(os.path.join(IMG, "pressure_volume.png"), "Pressure - volume at fixed knee angle.", 12)
    D.P("The volume rises by about 40 mL from 0 to 20 kPa and by about 20 mL per further 20 kPa: the cover takes over the hoop load once "
        "the bladder has inflated against it. This growth is also why the FEA moment exceeds p k at larger angles - the section that "
        "the pressure acts on is larger than the undeformed cavity of the hand calculation.")
    # 7.5 stresses
    D.H("7.5 Stresses and factor of safety", 2)
    rows = []
    for run in RUNS:
        rr = LD.get(run)
        if not rr: continue
        w = [x for x in rr if x["converged"] and (x["p_kPa"] or 0) > 0 and (x["p_kPa"] or 0) <= 60.0001]
        if not w: continue
        vb = max(w, key=lambda x: x["vm_max_bladder_MPa"] or 0); vc = max(w, key=lambda x: x["vm_max_cover_MPa"] or 0)
        rows.append([run, "%s (%s kPa)" % (vb["name"], f2(vb["p_kPa"], 1)), f2(vb["vm_max_bladder_MPa"]), f2(LIM_BL / vb["vm_max_bladder_MPa"], 1),
                     f2(vc["vm_max_cover_MPa"]), f2(LIM_COV / vc["vm_max_cover_MPa"], 1)])
    D.T(["Run", "Step of the bladder maximum", "Bladder vm max (MPa)", "FoS bladder (11.1 MPa)", "Cover vm max (MPa)", "FoS cover (37.2 MPa)"],
        rows, "Largest von Mises stress (shell surfaces) in the converged pressurised steps up to 60 kPa, and FoS = limit / stress.",
        size=7.5, widths=[2.2, 4.8, 2.3, 2.6, 2.3, 2.6])
    D.P("Every factor of safety is well above 1. The peaks sit at the cover end corners and in the fold band - places where the "
        "idealised model concentrates load (bonded edges, sharp fold) - so they are upper estimates. Fatigue life is not given: no S-N "
        "data for the bladder TPU or the coated fabric exist in the allowed sources " + c("brief") + ".")
    D.H("7.6 Deformed shape", 2)
    D.F(os.path.join(IMG, "deformed_stress_21pct.png"), "Deformed bladder at the peak frame (21 % stance, 5.78 deg; true scale) coloured "
        "by bladder von Mises stress, cover transparent. Vented: the fold band wrinkles; pressurised: the bladder fills the cover.", 16.5)
    D.F(os.path.join(IMG, "section_midplane_21pct.png"), "Section near the mid-plane at 21 % stance: bladder (dots) and cover (crosses) "
        "vented and at 20 / 40 / 60 kPa, undeformed in grey. Shaded = fold band.", 10)

    # ================================================================= 8 discussion
    D.H("8. Discussion - why the FEA and the hand calculation differ where they differ")
    for t in ["At small angle the two agree (3 deg: +6 to +8 %). There the bladder section at the knee line is close to the undeformed "
              "cavity, and the FEA reads the moment the same way the formula defines it. This is the validation of Model B and of the "
              "moment extraction asked for in the brief " + c("brief") + ".",
              "The FEA k is larger than the hand-calc k. The FEA bladder is a mid-surface shell (half a wall thickness outside the inner "
              "cavity) that inflates against the cover; CHK_CORE showed about +7..+16 % in k from this alone (D-A10-Q4).",
              "The ratio grows with angle because the fold band, which is free to bulge, becomes part of the pressurised section as the "
              "crease closes. Model B assumes a sharp mitre that adds nothing. The FEA is therefore expected above p k at large angles "
              "while the bladder stays inside the cover.",
              "The ratio falls with pressure at a fixed angle (for example 20 -> 60 kPa in the cycles): the cover limits the bulge, so "
              "the extra section does not grow in proportion to p.",
              "The cycle values at 20 kPa (main shape: 1.17 at 13 % rising to 1.66 at 21 %) are larger than the fixed-angle value at "
              "3 deg because the bladder is inflated first and then bent; the order of loading changes the fold. The fixed-angle cases "
              "follow the hand calculation's order (bend, then pressurise) and are the cleaner comparison.",
              "Above about 13 deg the rigid halves begin to overlap near the crease (geom_check_v3: skin 7.5-11 mm, device top 13.5-20 mm, "
              "D-A10-ANG), so the idealised reference becomes increasingly unphysical; results there are reported only as computed."]:
        D.B(t)

    # ================================================================= 9 conclusions
    D.H("9. Conclusions")
    con = ["The hand calculation M = p k (Model B) is confirmed by an FEA that uses the same assumptions: at 3 deg the FEA gives "
           "1.06 / 1.06 / 1.08 x p k at 20 / 40 / 60 kPa, i.e. the moment is linear in pressure and has the right size.",
           "The moment extraction (reactions of the shank half about the knee centre, minus the vented state) is correct; any low "
           "moment found in the real-case runs (v1 / v2: about 0.1 N m at 20 kPa) is caused by the real-case effects, not by the "
           "formula or the post-processing.",
           "With the knee bent further the idealised device gives more than p k, because the inflated fold band adds section; Model B "
           "is therefore not an upper bound of the idealised geometry at larger angles - it is the value of the undeformed cavity.",
           "The folded bladder can sit in more than one stable shape; the moment of a real bladder near the crease is not unique to "
           "within roughly +-15 % at 20 kPa in the main and relaxed shapes, and a squeezed shape can carry far more. Tests should "
           "load the bladder repeatedly and report the spread.",
           "Stresses up to 60 kPa are far below the limits of both the bladder and the cover in this idealised set-up.",
           "Not covered: the real device on a soft leg (not run, owner), pressures above 60 kPa, and the vent phase after 36 %."]
    for i, t in enumerate(con, 1):
        D.P("%d. %s" % (i, t))

    # ================================================================= 10 limitations
    D.H("10. Limitations")
    for t in ["Idealised reference only: no tissue, pad, straps or friction; no skin pressure, strap force or slip results exist in this "
              "model (they belong to the real case).",
              "Mesh M0 only. A mesh study on the core model was not run (time and RAM: one job at a time on a 7.7 GB PC); the earlier "
              "real-case study M0 vs M1 changed the knee reaction by 4.4 % " + c("prev") + ".",
              "Fold band of 50 mm with 1 % axial modulus is a modelling choice to represent a fabric fold; a sharper or softer band changes "
              "the bulge and therefore the ratio at larger angles.",
              "Static solver: no dynamics, no air flow, no time to fill; pressures are prescribed.",
              "Contact stabilisation 1e-4 adds about 0.26 N m to the vented moment at 3 deg (cancels in the device moment except its "
              "pressure-dependent part).",
              "Multiple equilibria (fold states): the cycle moments depend on the loading path; the main-shape values are quoted.",
              "Cover end caps have a free bottom edge (as in the CAD); this limits the model to about 70 kPa (E-123) - outside the "
              "60 kPa range of this report.",
              "No fatigue: no S-N data in the allowed sources."]:
        D.B(t)

    # ================================================================= 11 next
    D.H("11. Recommended next steps")
    for t in ["Run the real case (decks built and sealed in 02_Nastran_Model\\_held_real_case; rebuild the cycles with --cyc_end 36 "
              "--cyc_step 3 first) when the owner approves, and compare it with these reference numbers frame by frame.",
              "Bench test: torque on a hinged rigid two-part leg phantom at 3-10 deg and 20-60 kPa, repeated several times per point, to "
              "measure the reference moment and the spread from fold states.",
              "If a sharper agreement at larger angles is wanted, add a hand-calculation term for the bulge of the fold band (section "
              "growth with p), or compare against k measured on the inflated CAD shape."]:
        D.B(t)

    # ================================================================= appendices
    D.H("Appendix A - Decisions (D-A10-*)")
    dec = decisions()
    D.T(["ID", "Decision, reason and effect of the alternatives (abridged; full text in " + c("dec") + ")"],
        [[i, short(t, 420)] for i, t in dec], "Decisions taken during the work.", size=6.5, widths=[2.3, 15.2])
    D.H("Appendix B - Error log (E-60 onwards)")
    er = errors(60)
    D.T(["ID", "Time", "Step", "Message / symptom", "Cause", "Fix"],
        [[x[0], x[1][5:], short(x[2], 40), short(x[3], 160), short(x[4], 160), short(x[5], 140)] for x in er if len(x) >= 6],
        "Errors, warnings and non-convergence logged in this run folder (abridged; full text and proof in " + c("err") + ").",
        size=6, widths=[1.2, 1.9, 2.4, 4.4, 4.2, 3.4])
    D.H("Appendix C - Delivered files")
    for t in ["07_Report\\FEA_asm10_routeA_HandcalcReference_v3.docx - this report.",
              "05_Results\\Tables\\v3_HC\\cycle_moment.csv, cycle_summary.csv, margin_moment.csv - collector output (cycle_a10.py "
              "--tag v3_HC --ref_cyc HCC --ref_ang HC --p0_load_branch --stance_max 36 --state_flag).",
              "05_Results\\Images\\v3_HC\\*.png - every figure of this report (figs_hc_v3.py; from the solver output files).",
              "04_Runs\\<run>\\ - native solver files (.nas, .LOG, .OUT, .FNO), <run>_results.csv / .xlsx, runtime.txt.",
              "00_Plan_and_Decisions\\decisions_2026-11-15.txt, 06_Error_Log\\error_log.csv, queue_log.txt.",
              "Superseded (kept, not used here): 05_Results\\Tables\\v3_B0 and the B0* / B0C* runs of the first reference attempt."]:
        D.B(t)
    D.H("References")
    for i, (_, t) in enumerate(REFS, 1):
        D.P("[%d] %s" % (i, t), size=8.5)
    D.d.save(out); print("written", out)


if __name__ == "__main__":
    main()
