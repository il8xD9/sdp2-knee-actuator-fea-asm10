# -*- coding: utf-8 -*-
r"""Word report (native OMML equations) for the gait FEA of route (a) full asseymbly 07, from collect_a07.py output.
Usage: python -P build_report_a07.py --tag v1   -> 07_Report\FEA_asm07_routeA_Report_v1.docx (refuses to overwrite unless 'draft')"""
import argparse
import json
import math
import os
import shutil
import sys

import numpy as np
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import parse_xml, OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
V6 = os.path.dirname(R)
CAD_ISO = os.path.join(V6, "Route a - thigh strap 150 (main)", "full asseymbly 07 - iso.png")
K_MM3 = 206994.0
M = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'

# ------------------------------------------------------------------ references [n] (real files)
REFS = [
    ("brief", "00_Plan_and_Decisions\\BRIEF.md - master brief of Simulation 2 (values, sequence, outputs, pass/fail)."),
    ("dec", "00_Plan_and_Decisions\\decisions_2026-11-13.txt - owner decisions D-Q4..D-Q11, D-FAB3, D-AUTO, D-FAB4, D-ORDER, D-RELAX."),
    ("status", "00_Plan_and_Decisions\\STATUS.md - pipeline status and verification notes (sections 1-11)."),
    ("err", "06_Error_Log\\error_log.csv - every error, warning and non-convergence (E-01 ...)."),
    ("v10", "03_Mechanical_Design\\Design_Reports\\M1-M7 work v10.docx - hand calculation: k = 206 994 mm3, M = p k "
            "(4.14 N.m at 20 kPa, 5.59 N.m at 27 kPa), ring targets, limits."),
    ("o2", "02_Biomechanics\\Team_Inputs\\Biomechanics_Handover\\01_Requirements_and_Inputs\\Clinical_Constraints_B1-B8_2026-11-12\\"
           "Biomech_Constraints_Option2_PatientRange_13-36_v3.xlsx - option-2 window 13-36 % stance, knee angle and pressure per frame."),
    ("b7", "02_Biomechanics\\Team_Inputs\\Biomech_B7_Tissue_Tolerance_v8.xlsx - skin pressure limits (24 / 36 kPa, ring 19 / 11 kPa)."),
    ("geo", "03_Mechanical_Design\\Design_Reports\\m1-m7\\_cad_v8_scripts\\geo8.py and geo_A150.json - the code that built the "
            "last v6 parts (exact geometry used for the mesh)."),
    ("cad", "03_Mechanical_Design\\CAD\\last v2\\last v6\\Route a - thigh strap 150 (main)\\full asseymbly 07.iam (copy in 01_CAD_copy, "
            "md5 of the originals in 00_Plan_and_Decisions)."),
    ("nas", "Autodesk Inventor Nastran 2026 solver Nastran.exe (ADS NASTRAN 20.2.0.23), C:\\Program Files\\Autodesk\\Inventor Nastran 2026\\Nastran; "
            "Documentation\\Verification_Manual.pdf."),
    ("pierrat", "Pierrat et al. 2014 (as cited in M1-M7 work v10 and BRIEF sec. 2): neo-Hookean leg tissue, G = 5.5 kPa relaxed / 400 kPa contracted."),
    ("zhang", "Zhang & Mak 1999 (owner answer Q5, decisions_2026-11-13.txt): skin friction coefficient mu = 0.37."),
    ("scripts", "scripts\\mesh_a07.py, deck_a07.py, run_queue.ps1, post_a07.py, diag_bend.py, collect_a07.py, build_report_a07.py (this run folder)."),
    ("tests", "04_Runs\\solver_test\\t6 (MATS1 NLELAST ignored on shells) and 04_Runs\\solver_test\\t7 (MAT8 + MCID orientation check)."),
]
RN = {k: i + 1 for i, (k, _) in enumerate(REFS)}


def c(*keys):
    return "[" + ", ".join(str(RN[k]) for k in keys) + "]"


# ------------------------------------------------------------------ OMML helpers
def r(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return '<m:r><m:t xml:space="preserve">%s</m:t></m:r>' % t


def fr(a, b):
    return "<m:f><m:num>%s</m:num><m:den>%s</m:den></m:f>" % (a, b)


def sb(a, b):
    return "<m:sSub><m:e>%s</m:e><m:sub>%s</m:sub></m:sSub>" % (a, b)


def sp(a, b):
    return "<m:sSup><m:e>%s</m:e><m:sup>%s</m:sup></m:sSup>" % (a, b)


def par(a, beg="(", end=")"):
    return '<m:d><m:dPr><m:begChr m:val="%s"/><m:endChr m:val="%s"/></m:dPr><m:e>%s</m:e></m:d>' % (beg, end, a)


def bar(a):
    return '<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e>%s</m:e></m:bar>' % a


# ------------------------------------------------------------------ document helpers
class Doc:
    def __init__(self):
        self.d = Document()
        s = self.d.sections[0]
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(2.0)
        st = self.d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        for lvl, size in ((1, 15), (2, 12.5), (3, 11)):
            h = self.d.styles["Heading %d" % lvl]
            h.font.name = "Calibri"; h.font.size = Pt(size); h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
            h.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        self.fig = 0; self.tab = 0; self.eq = 0

    def H(self, t, lvl=1):
        self.d.add_heading(t, lvl)

    def P(self, t="", bold=False, italic=False, size=None, align=None):
        p = self.d.add_paragraph()
        if t:
            run = p.add_run(t); run.bold = bold; run.italic = italic
            if size:
                run.font.size = Pt(size)
        if align is not None:
            p.alignment = align
        p.paragraph_format.space_after = Pt(4)
        return p

    def B(self, t):
        p = self.d.add_paragraph(style="List Bullet"); p.add_run(t); p.paragraph_format.space_after = Pt(2)
        return p

    def EQ(self, xml, where=None):
        self.eq += 1
        p = self.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p._p.append(parse_xml('<m:oMathPara %s><m:oMath>%s%s</m:oMath></m:oMathPara>' % (M, xml, r("        (%d)" % self.eq))))
        if where:
            q = self.d.add_paragraph(); rr = q.add_run(where); rr.font.size = Pt(8.5); rr.italic = True
            q.paragraph_format.space_after = Pt(6)
        return self.eq

    def shade(self, cell, hexcol):
        tcPr = cell._tc.get_or_add_tcPr()
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcol)
        tcPr.append(sh)

    def T(self, header, rows, caption, size=8, widths=None, verdict_col=None):
        self.tab += 1
        cp = self.P("Table %d. %s" % (self.tab, caption), bold=True, size=9); cp.paragraph_format.keep_with_next = True
        t = self.d.add_table(rows=1 + len(rows), cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, h in enumerate(header):
            cell = t.rows[0].cells[j]; cell.text = ""
            run = cell.paragraphs[0].add_run(str(h)); run.bold = True; run.font.size = Pt(size)
            self.shade(cell, "D9E2F3")
        for i, row in enumerate(rows, start=1):
            for j, v in enumerate(row):
                cell = t.rows[i].cells[j]; cell.text = ""
                run = cell.paragraphs[0].add_run("" if v is None else str(v)); run.font.size = Pt(size)
                if verdict_col is not None and j == verdict_col:
                    if str(v) == "PASS":
                        self.shade(cell, "D5EFD5")
                    elif str(v) == "FAIL":
                        self.shade(cell, "F6D2D2")
        if widths:
            for row in t.rows:
                for j, w in enumerate(widths):
                    row.cells[j].width = Cm(w)
        self.d.add_paragraph().paragraph_format.space_after = Pt(2)
        return self.tab

    def F(self, path, caption, width=15.5):
        if not path or not os.path.exists(path):
            self.P("[figure not available: %s]" % (os.path.basename(path) if path else caption), italic=True)
            return None
        self.fig += 1
        p = self.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(path, width=Cm(width)); p.paragraph_format.keep_with_next = True
        self.P("Figure %d. %s" % (self.fig, caption), italic=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        return self.fig


def f2(v, n=2):
    return "-" if v is None else ("%.*f" % (n, v))


def rows_of(J, run):
    return J["runs"].get(run, {}).get("rows", [])


def conv(J, run):
    rr = rows_of(J, run)
    return sum(1 for x in rr if x["converged"]), J["runs"].get(run, {}).get("nsteps")


def dvdtheta(J, run):
    """slope of the vented bladder volume with knee angle (mL/rad) from the vented frames of a run/twin."""
    pts = [(x["theta"], x["V_bladder_mid_cm3"]) for x in rows_of(J, run)
           if x["converged"] and x["kind"] in ("S", "S_sub", "W", "R") and (x["p_kPa"] or 0) == 0 and x["theta"] is not None
           and x["V_bladder_mid_cm3"] is not None]
    if len(pts) < 2:
        return None
    th = np.radians([p[0] for p in pts]); v = np.array([p[1] for p in pts])
    if np.ptp(th) < 1e-6:
        return None
    return float(np.polyfit(th, v, 1)[0])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tag", required=True); a = ap.parse_args()
    J = json.load(open(os.path.join(R, "05_Results", "Tables", a.tag, "collect_%s.json" % a.tag)))
    out = os.path.join(R, "07_Report", "FEA_asm07_routeA_Report_%s.docx" % a.tag)
    if os.path.exists(out) and not a.tag.startswith("draft"):
        sys.exit("report %s exists - never overwrite a delivered report; use a new tag" % out)
    img = os.path.join(R, "05_Results", "Images", a.tag)
    if os.path.exists(CAD_ISO):
        shutil.copy2(CAD_ISO, os.path.join(img, "cad_full_asseymbly_07_iso.png"))
    DM = J["device_moment"]; PF = J["passfail"]; runs = J["runs"]
    prod = [n for n in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "MS_M1", "MS_M2") if n in runs]
    chk = [n for n in ("CHK_MINI_K", "CHK_FAB", "CHK_FAB2", "CHK_FAB3", "CHK_FAB4") if n in runs]
    D = Doc()

    # ============================================================ title
    D.P("SDP-2 (MMNB) soft knee exoskeleton - right leg", bold=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    D.P("Gait FEA of route (a) full asseymbly 07 (last v6) with the Inventor Nastran solver", bold=True, size=16,
        align=WD_ALIGN_PARAGRAPH.CENTER)
    D.P("Report %s - nonlinear static (SOL 106, large displacement), multi-subcase gait sequence" % a.tag, size=11,
        align=WD_ALIGN_PARAGRAPH.CENTER)
    D.P("Run folder: 03_Mechanical_Design\\CAD\\last v2\\last v6\\simulation_2_assymbly_7 (all files referenced below are relative "
        "to it unless a full path is given).", italic=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    done = [n for n in prod if conv(J, n)[0] and conv(J, n)[0] == conv(J, n)[1]]
    part = [n for n in prod if n not in done]
    D.P("Runs included: check runs %s; production runs fully converged: %s; production runs partial / not finished: %s." %
        (", ".join(chk) or "none", ", ".join(done) or "none", ", ".join(part) or "none"), size=9)

    # ============================================================ 1 summary
    D.H("1. Summary of results")
    x4 = (DM.get("CHK_FAB4") or [None])[0]
    xm = (DM.get("CHK_MINI_K") or [None])[0]
    s = []
    if x4:
        s.append("With the flexible fabric cover (production set-up, CHK_FAB4) the inflation of the bladder to 20 kPa at the peak frame "
                 "(21 %% stance, 5.78 deg) changes the solver's knee reaction by %s N.m (against the vented state just before) and %s N.m "
                 "(against the vented reference VREF), against the hand-calculation value p k = %s N.m %s." %
                 (f2(x4["M_device"]), f2(x4.get("M_device_vref")), f2(x4["M_hand"]), c("v10")))
    for n in prod:
        d = [x for x in DM.get(n, []) if x["kind"] == "W"]
        if d:
            pk = max(d, key=lambda x: x["p_kPa"])
            s.append("Production run %s (%s): device moment at the pressure peak (%s %% stance, %s kPa) = %s N.m vs hand calc %s N.m; "
                     "largest device moment over the pulse = %s N.m." %
                     (n, runs[n]["desc"], f2(pk["frame"], 0), f2(pk["p_kPa"], 1), f2(pk["M_device"]), f2(pk["M_hand"]),
                      f2(max(x["M_device"] for x in d))))
    kn = []
    for n in prod:
        rr = [x for x in rows_of(J, n) if x["converged"]]
        W = [x for x in rr if x["kind"] == "W"]
        d = [x for x in DM.get(n, []) if x["kind"] == "W"]
        if not W or not d:
            continue
        def mxk(rows_, k):
            v = [x[k] for x in rows_ if x.get(k) is not None]
            return max(v) if v else None
        pk = max(d, key=lambda x: x["p_kPa"])
        vv = [x["V_bladder_mid_cm3"] for x in rr if x.get("V_bladder_mid_cm3") is not None]
        kn += [[n, "Device knee extension moment at the pressure peak (FEA / hand p k)", "%s / %s N.m" % (f2(pk["M_device"]), f2(pk["M_hand"]))],
               [n, "Device moment, max over the pulse 13-36 %", "%s N.m" % f2(max(x["M_device"] for x in d))],
               [n, "Net forward shank force from the device, max |.| (ACL)", "%s N" % f2(max(abs(x["dFx_device"]) for x in d if x["dFx_device"] is not None))],
               [n, "Skin pressure under the bladder: mean max / peak max (pulse)", "%s / %s kPa (limit 24 on the mean)" %
                (f2(mxk(W, "p_under_bladder_mean_kPa"), 1), f2(mxk(W, "p_under_bladder_peak_kPa"), 1))],
               [n, "Posterior-knee zone peak (pulse)", "%s kPa (limit 24)" % f2(mxk(W, "p_posterior_knee_peak_kPa"), 1)],
               [n, "Bladder / cover body / hooks von Mises max", "%s / %s / %s MPa (limits 11.1 / 37.2 / 14.2)" %
                (f2(mxk(rr, "vm_max_bladder_MPa"), 2), f2(mxk(rr, "vm_max_cover_MPa"), 2), f2(mxk(rr, "vm_max_hooks_MPa"), 2))],
               [n, "Bladder volume: vented / at the pressure peak", "%s / %s cm3" % (f2(vv[0], 1), f2(max(vv), 1))],
               [n, "Device slip along the leg, max |.|", "%s mm" % f2(mxk(rr, "slip_y_maxabs_mm"), 1)]]
    if kn:
        D.T(["Run", "Quantity", "FEA result"], kn, "Key results of the production runs.", size=8.5, widths=[1.5, 8.5, 7.0])
    for t_ in s:
        D.B(t_)
    D.B("Main finding: the FEA does NOT confirm the hand-calculated extension moment. The solver shows that knee flexion hardly changes "
        "the bladder volume in this model (the soft pad and soft tissue let the leg rotate under the device), so by the energy rule "
        "M = p dV/dtheta the inflation can only produce a small moment. The solver result and the energy check agree with each other "
        "(section 6); the hand calculation assumes the full k = 206 994 mm3 per radian %s." % c("v10"))
    scope = prod if prod else ["CHK_FAB4"]
    fails = sorted(set("%s (%s)" % (x["item"], x["run"]) for x in PF if x["run"] in scope and x["verdict"] == "FAIL"))
    passes = sorted(set(x["item"].split(",")[0].split(" (")[0] for x in PF if x["run"] in scope and x["verdict"] == "PASS"))
    D.B("Checks that pass in %s: %s." % (", ".join(scope), "; ".join(passes) or "none"))
    D.B("Checks that fail: %s. Ring contact peaks are single-node values on the ring edges (sharp shell edge on soft tissue, "
        "mesh-dependent). Full list: section 7; every problem met on the way: section 9 %s." % ("; ".join(fails) or "none", c("err")))

    # ============================================================ 2 task and mechanism
    D.H("2. Task, mechanism and what had to be found")
    D.P("The device adds knee extension torque in early stance, from 13 to 36 %% of stance with the peak at 21 %% (148 ms) %s. The "
        "actuator is a moulded TPU air bladder (actuator-V8, route a, assembly 07): 66 x 44 mm outside, 2 mm wall, 170 mm in contact "
        "with the leg, lying lengthwise across the back of the knee, held by the pad (streches.10), four webbing rings with Velcro "
        "and POM hooks, and a thin fabric cover (cover.06, 0.43 mm, 1 mm gap) %s. Pressure p inside the bladder pushes forward "
        "into the back of the thigh and the calf; acting behind the knee axis (d_h = 65 mm in front of the back skin) it gives the "
        "hand-calculation moment %s:" % (c("o2"), c("cad", "geo"), c("v10")))
    D.EQ(sb(r("M"), r("hand")) + r(" = p k,   k = 206 994 ") + sp(r("mm"), r("3")) +
         r(",   ") + sb(r("M"), r("hand")) + par(r("20 kPa")) + r(" = 4.14 N\u00b7m,   ") + sb(r("M"), r("hand")) + par(r("27 kPa")) +
         r(" = 5.59 N\u00b7m"), "p = bladder gauge pressure (MPa = N/mm2), k = volume change of the bladder per radian of knee flexion "
         "(M1-M7 v10).")
    D.P("The simulation has to find %s: the knee extension moment Mz as the solver reaction about the knee axis at the shank control "
        "node, produced by the inflation itself (no applied torque); mean and peak skin pressure under the bladder; the posterior-knee "
        "zone peak; ring pressure (peak <= 19 kPa in the pulse, mean <= 11 kPa in donning); ring tension; bladder volume per step; "
        "sliding of the device; the net forward force on the shank (ACL rule, ~0) and no device torque at theta <= 0; von Mises stress "
        "in the bladder (<= 11.1 MPa), cover (<= 37.2 MPa) and hooks (<= 5.68 / 14.2 MPa)." % c("brief", "b7"))

    # ============================================================ 3 model
    D.H("3. Model set-up")
    D.H("3.1 Geometry and why the mesh was written by script", 2)
    D.P("Inventor's own mesher failed on assembly 07 (empty meshes of the thin parts, then 'Meshing Failed', E-02..E-05 %s). The mesh "
        "was therefore written by script (scripts\\mesh_a07.py) from the code that built the CAD parts, geo8.py + geo_A150.json %s, "
        "so the geometry is that of last v6 assembly 07 %s; the Inventor Nastran solver Nastran.exe solves the deck %s." %
        (c("err"), c("geo"), c("cad"), c("nas")))
    D.F(os.path.join(img, "cad_full_asseymbly_07_iso.png"), "CAD: full asseymbly 07, route (a), thigh strap 150 (iso view) %s." % c("cad"), 11)
    D.F(os.path.join(img, "mesh_M0_view.png"), "Production mesh M0 written by mesh_a07.py (pad, rings, hooks, bladder, cover on the leg).", 15)
    mq = J.get("mesh_quality") or []
    if mq:
        def mfmt(i, v):
            if i == 0:
                return v
            if v in ("nan", ""):
                return "-"
            x = float(v)
            return "%d" % x if x == int(x) and mq[0][i] in ("elements", "AR_gt10", "jac_lt_0_2") else f2(x, 3)
        D.T(mq[0], [[mfmt(i, v) for i, v in enumerate(rw)] for rw in mq[1:]],
            "Mesh M0 quality per part (02_Nastran_Model\\mesh_quality_M0.csv): aspect ratio, scaled Jacobian, shell angles.", size=7)
    D.H("3.2 Materials", 2)
    D.T(["Part", "Element", "Material model and values", "Source"],
        [["Leg tissue (leg-tissue.02)", "CHEXA", "neo-Hookean MATHP: relaxed G 5.5 kPa, contracted G 400 kPa, K = 10 G, rho 1000 kg/m3", c("pierrat", "dec")],
         ["Bones", "RBE2", "rigid: control node to the bone bore nodes; thigh fixed, shank rotated about the knee axis (SPCD)", c("brief")],
         ["Pad streches.10", "CHEXA", "E 0.0965 MPa, nu 0.33 (R7: E 0.276 MPa), rho 203.9", c("brief")],
         ["Webbing rings, tails, carriers", "CQUAD4 t 3.18", "MAT8 E 498 MPa, nu 0.35, thermal expansion along the hoop only (pre-tension)", c("brief")],
         ["Hooks hook.05 / .06", "CQUAD4 t 4", "POM E 2760 MPa, nu 0.37", c("brief")],
         ["Bladder actuator-V8", "CQUAD4/CTRIA3 t 2 (mid-surface)", "MAT1 E 7.2 MPa, nu 0.49, large displacement", c("brief")],
         ["Cover body cover.06", "CQUAD4 t 0.43", "membrane MAT8: E_hoop 498 MPa, E_leg = G12 = 4.98 MPa (1 %); bending MAT1 498 MPa", c("dec")],
         ["Cover sewing flange / end caps", "CQUAD4 t 0.43", "isotropic MAT1 E 498 MPa, nu 0.35", c("dec")]],
        "Materials used in the production decks.", size=7.5)
    D.P("Tissue strain energy (Nastran MATHP form, first order) %s:" % c("nas"))
    D.EQ(r("W = ") + sb(r("A"), r("10")) + par(sb(bar(r("I")), r("1")) + r(" \u2212 3")) + r(" + ") + sb(r("D"), r("1")) +
         sp(par(r("J \u2212 1")), r("2")) + r(",   ") + sb(r("A"), r("10")) + r(" = ") + fr(r("G"), r("2")) + r(",   ") +
         sb(r("D"), r("1")) + r(" = ") + fr(r("K"), r("2")) + r(",   K = 10 G"),
         "relaxed: A10 = 0.00275 MPa, D1 = 0.0275 MPa; contracted: A10 = 0.2 MPa, D1 = 2.0 MPa.")
    D.P("Cover membrane (decision D-FAB3/D-FAB4 %s): a woven fabric cannot carry compression along the leg - it wrinkles. A static "
        "solver cannot follow wrinkles (sections 4 and 9), so the cover body is given a low modulus along the leg and keeps its full "
        "modulus around the bladder, where it holds the bladder in:" % c("dec"))
    D.EQ(sb(r("E"), r("leg")) + r(" = ") + sb(r("G"), r("12")) + r(" = r ") + sb(r("E"), r("hoop")) +
         r(",   r = 0.01,   ") + sb(r("E"), r("hoop")) + r(" = 498 MPa,   ") + sb(r("\u03bd"), r("12")) + r(" = 0.35 r"),
         "material axis 1 = leg axis (CORD2R 91 as MCID on every cover-body element), verified by solver test t7.")
    D.H("3.3 Contacts, pre-tension and loads", 2)
    D.P("Contacts %s: bonded (shared nodes) cover flanges and cap edges to pad and webbing, webbing to pad and hooks; frictionless "
        "separation bladder-cover (1 mm gap) and bladder-pad/webbing; friction mu = 0.37 %s for pad-skin, ring-skin, cover-skin and "
        "bladder-skin (relaxed runs: ring-skin frictionless for convergence, E-26). Gravity and inertia are off (quasi-static) %s." %
        (c("brief"), c("zhang"), c("dec")))
    D.P("Pre-tension (owner option a %s): thermal shrink of the ring shells along the hoop, calibrated so the free-strap tension reaches "
        "the targets 20.89 / 19.59 / 13.3 / 9.4 N (thigh near / shank near / thigh far / shank far):" % c("dec"))
    D.EQ(sb(r("\u03b5"), r("hoop")) + r(" = \u03b1 \u0394T,   T = ") + sb(r("N"), r("x")) + r(" w"),
         "alpha = thermal expansion of the ring along the hoop (element x), Delta T calibrated per ring (02_Nastran_Model\\calib_dT.json); "
         "N_x = shell membrane force per width (N/mm), w = ring width.")
    D.P("Bladder pressure is a follower PLOAD4 on the inner walls; the shank is rotated by SPCD in steps <= 2.5 deg; the option-2 "
        "waveform gives p per frame %s:" % c("o2", "v10"))
    D.EQ(r("p = ") + fr(r("min") + par(r("\u03b1 \u00b7 deficit, ") + sb(r("M"), r("pat"))), r("k")),
         "alpha_max 0.1255 (20 kPa cap) / 0.1694 (27 kPa cap): 6.9 -> 20.0 -> 2.8 kPa over 13-36 % stance.")
    D.P("Sequence per production run %s: D1 donning, D2 pre-tension, stance frames 1-12 %% at p = 0, the window 13-36 %% frame by "
        "frame, release to the 2.4 kPa residual (frames 37-87 %%), then (full runs only) toe-off and swing." % c("brief"))
    D.H("3.4 Knee moment and device moment", 2)
    D.P("The knee moment is the solver reaction (SPCFORCE) about the knee axis at the shank control node. Because the leg tissue "
        "itself resists the prescribed flexion, the device moment is the difference to the same run with the bladder vented:")
    D.EQ(sb(r("M"), r("device")) + par(r("f")) + r(" = ") + sb(r("M"), r("run")) + par(r("f")) + r(" \u2212 ") +
         sb(r("M"), r("vented")) + par(r("f")),
         "f = gait frame; vented twin R1V (relaxed) / R2V (contracted), or the vented steps of a check run (vented before / VREF).")
    D.P("Energy check (virtual work of the bladder pressure on the knee rotation):")
    D.EQ(sb(r("M"), r("device")) + r(" \u2248 p ") + fr(r("dV"), r("d\u03b8")),
         "dV/dtheta from the bladder volume of the vented steps; the hand calculation uses dV/dtheta = k.")

    # ============================================================ 4 verification and checks
    D.H("4. Verification, solver tests and check runs")
    D.T(["Test", "What it checks", "Result"],
        [["solver_test t1..t5 (phase 1)", "MATHP NLSTATIC, contact cards, follower pressure", "passed (STATUS.md)"],
         ["solver_test t6", "tension-only fabric via MATS1 NLELAST on shells", "ignored by the solver (pull and push both 12.20 N) -> not usable"],
         ["solver_test t7", "MAT8 + MCID material axis on CQUAD4, SOL 106 LGDISP", "leg stretch 0.9328 mm (hand 0.934), hoop 0.00933 mm (hand 0.0093), "
          "same in side-wall and top-panel planes and with rotated node order"],
         ["deck regression", "new deck options leave older decks unchanged", "fab.nas, fab3.nas, fab4.nas reproduced with 0 differences"]],
        "Solver tests %s." % c("tests", "status"), size=8)
    rows = []
    for n in chk:
        cc, ns = conv(J, n)
        dmx = (DM.get(n) or [None])[0]
        rows.append([n, runs[n]["desc"], "%d / %s" % (cc, ns), runs[n]["runtime"].get("seconds", "-"),
                     f2(dmx["M_device"]) if dmx else "-", f2(dmx.get("M_device_vref")) if dmx else "-"])
    D.T(["Run", "Set-up", "converged / planned", "time (s)", "M_device vs vented before (N.m)", "vs VREF (N.m)"], rows,
        "Check runs (contracted tissue, D1-D2-flex to 5.78 deg-inflate 20 kPa-VREF).", size=7.5)
    D.P("Why four cover variants: the plate-stiff cover of CHK_MINI_K kept the whole device straight (bladder bend 0.1 deg while "
        "the skin under it bends 3.65 deg, E-39), so the bladder was never squeezed. Lowering the cover bending to a fabric value "
        "(CHK_FAB, CHK_FAB2) made the 0.43 mm sheet wrinkle and the static solver stopped in the pre-tension step (E-41..E-46). The "
        "orthotropic membrane (CHK_FAB3) removed the wrinkling; with the flange kept isotropic (CHK_FAB4) every step converged "
        "(E-47..E-51). In CHK_FAB4 the bladder bends 1.4 deg with a 3.66 deg skin bend.")
    D.F(J["figs"].get("check_moment"), "Device moment from inflation at the peak frame in the check runs vs the hand calculation.", 14)
    for n in ("CHK_FAB4",):
        for nm in ("history", "map_sub06"):
            pth = [p for p in J["copied"].get(n, []) if nm in os.path.basename(p)]
            if pth:
                D.F(pth[0], "%s: %s (post_a07.py render from the Nastran output)." % (n, "step history" if nm == "history"
                                                                                    else "skin contact pressure at 20 kPa, 21 %"), 15)

    # ============================================================ 5 production results
    D.H("5. Production results")
    if not prod:
        D.P("No production run has finished yet; this issue of the report contains the check runs only.", italic=True)
    rows = []
    for n in prod:
        cc, ns = conv(J, n)
        rows.append([n, runs[n]["desc"], "%d / %s" % (cc, ns), runs[n]["runtime"].get("seconds", "no runtime record - run ended by "
                     "the PC restart at 13:22 (E-53)" if n == "R2" else "-"), runs[n]["runtime"].get("peakMB", "-")])
    if rows:
        D.T(["Run", "Case", "converged / planned subcases", "time (s)", "peak RAM (MB)"], rows, "Production runs (mesh M0 unless MS_*).", size=8)
        TGT = [("thigh_near", 20.89), ("shank_near", 19.59), ("thigh_far", 13.3), ("shank_far", 9.4)]
        tr = []
        for n in prod:
            d2 = [x for x in rows_of(J, n) if x["kind"] == "D" and x["converged"]]
            if d2:
                x = d2[-1]
                tr.append([n] + ["%s (%+.0f %%)" % (f2(x.get("T_%s_front_N" % k), 1), 100 * (x["T_%s_front_N" % k] - t) / t)
                                 if x.get("T_%s_front_N" % k) is not None else "-" for k, t in TGT])
        if tr:
            D.T(["Run", "thigh near (target 20.89 N)", "shank near (19.59 N)", "thigh far (13.3 N)", "shank far (9.4 N)"], tr,
                "Ring tension reached at the end of pre-tension D2 (front free strap) vs the targets (one calibration iteration, "
                "contracted; the rings interact through the pad, so the error is not removed in one step - stated, not hidden).", size=8)
    for n in prod:
        d = [x for x in DM.get(n, []) if x["kind"] in ("S", "W", "R")]
        if not d:
            continue
        D.H("5.%d %s - %s" % (prod.index(n) + 1, n, runs[n]["desc"]), 2)
        rr = {int(x["subcase"]): x for x in rows_of(J, n)}
        tr = []
        for x in d:
            q = rr.get(int(x["subcase"]), {})
            tr.append([f2(x["frame"], 0), f2(x["theta"]), f2(x["p_kPa"], 1), f2(x["M_device"]), f2(x["M_hand"]),
                       f2(x["dFx_device"]), f2(q.get("p_under_bladder_mean_kPa"), 1), f2(q.get("p_under_bladder_peak_kPa"), 1),
                       f2(q.get("p_posterior_knee_peak_kPa"), 1), f2(q.get("V_bladder_mid_cm3"), 1), f2(q.get("slip_y_maxabs_mm"), 1)])
        D.T(["stance %", "theta deg", "p kPa", "M_device N.m", "p k N.m", "dFx shank N", "skin mean kPa", "skin peak kPa",
             "post. knee peak kPa", "V cm3", "slip max mm"], tr,
            "%s per frame (device = run minus vented twin %s%s)." % (n, d[0]["twin"], ", theta-interpolated" if any(x["approx"] for x in d) else ""),
            size=7)
        for nm in ("history",):
            pth = [p for p in J["copied"].get(n, []) if nm in os.path.basename(p)]
            if pth:
                D.F(pth[0], "%s step history (post_a07.py)." % n, 15)
        okSub = set(int(x["subcase"]) for x in rows_of(J, n) if x["converged"])
        maps = sorted(p for p in J["copied"].get(n, []) if "map_sub" in os.path.basename(p)
                      and int(os.path.basename(p).split("map_sub")[-1][:2]) in okSub)
        for p in maps[:3]:
            D.F(p, "%s skin contact pressure, %s (post_a07.py render)." % (n, os.path.basename(p).split("map_")[-1][:-4]), 15)
    MSr = J.get("mesh_study") or []
    D.H("5.%d Mesh study" % (len(prod) + 1), 2)
    if MSr:
        fine = MSr[0]["fine"]; cc, ns = conv(J, fine)
        D.P("%s (%s) - %d / %s subcases converged - compared with %s (mesh M0) at the same steps. Brief criterion: knee moment, mean "
            "skin pressure under the bladder and ring tension change <= 5 %% between the two finest meshes %s." %
            (fine, runs[fine]["desc"], cc, ns, MSr[0]["coarse"], c("brief")))
        keep = [x for x in MSr if x["step"].startswith("D2") or x["step"].startswith("W 21")]
        D.T(["step", "quantity", "M0", "M1", "change %", "<= 5 %"],
            [[x["step"], x["quantity"], f2(x["coarse_value"], 3), f2(x["fine_value"], 3), f2(x["diff_pct"], 1),
              ("yes" if x["diff_pct"] is not None and abs(x["diff_pct"]) <= 5 else "no")] for x in keep],
            "Mesh study %s (M1) vs %s (M0) at the end of pre-tension and at the peak frame; all steps in the Mesh_study sheet of "
            "summary_all_runs_%s.xlsx." % (fine, MSr[0]["coarse"], a.tag), size=7)
        wf = [x for x in MSr if x["step"].startswith("W 21")]
        mk = [x for x in wf if x["quantity"] == "M_knee_ext_Nm"]
        dmf = (DM.get(fine) or [None])[0]
        dmc = [x for x in DM.get(MSr[0]["coarse"], []) if x["kind"] == "W" and abs((x["frame"] or 0) - 21) < 0.1]
        ok = sorted(set(x["quantity"] for x in wf if x["diff_pct"] is not None and abs(x["diff_pct"]) <= 5))
        nok = sorted(set(x["quantity"] for x in wf if x["diff_pct"] is not None and abs(x["diff_pct"]) > 5))
        D.P("Result of the mesh study at the peak frame (21 %%): the knee reaction changes by %s %% between M0 and M1; the device "
            "moment is %s N.m on M1 (inflated minus its own VREF) and %s N.m on M0 (R2 minus R2V), i.e. ~0 on both meshes against "
            "4.14 N.m - the main finding does not depend on the mesh. Within 5 %%: %s. Not within 5 %%: %s - the contact-pressure and "
            "ring-tension values are mesh-dependent (penalty contact on very soft tissue, see section 8) and are reported as M0 values "
            "with this uncertainty; all of them stay far below their limits on both meshes except the ring-edge peak." %
            (f2(mk[0]["diff_pct"], 1) if mk else "-", f2(dmf.get("M_device_vref")) if dmf else "-",
             f2(dmc[0]["M_device"]) if dmc else "-", ", ".join(ok) or "none", ", ".join(nok) or "none"))
    else:
        D.P("The mesh-study run (MS_M1C: mesh M1, contracted tissue, D -> 21 %% + VREF) has not finished yet; results are given on "
            "mesh M0 only (decision D-ORDER %s)." % c("dec"), italic=True)
    for key, cap in (("device_moment", "Device moment vs stance: FEA (solid) and hand calculation p k (dashed)."),
                     ("skin", "Skin contact pressure under the bladder (mean) and posterior-knee zone peak vs stance."),
                     ("rings", "Ring tension (front free strap) per step; dashed = pre-tension targets."),
                     ("volume", "Bladder mid-surface volume per step.")):
        if J["figs"].get(key):
            D.F(J["figs"][key], cap, 15.5)

    # ============================================================ 6 comparison with hand calc
    D.H("6. Comparison with the hand calculation (M1-M7 v10)")
    rows = []
    for n in chk + prod:
        d = [x for x in DM.get(n, []) if x["kind"] == "W"]
        if not d:
            continue
        pk = max(d, key=lambda x: x["p_kPa"])
        tw = {"R1": "R1V", "R2": "R2V", "R3": "R1V", "R5": "R1V", "R7": "R1V", "R4": "R2V", "R6": "R2V"}.get(n, n)
        sl = dvdtheta(J, tw)
        rows.append([n, f2(pk["p_kPa"], 1), f2(pk["theta"]), f2(pk["M_device"]), f2(pk["M_hand"]),
                     f2(sl / 1000.0 * 1e3, 1) if sl is not None else "-", f2(K_MM3 / 1000.0, 1),
                     f2(pk["p_kPa"] * 1e-3 * abs(sl) * 1e3 * 1e-3, 2) if sl is not None else "-"])
    if rows:
        D.T(["Run", "p kPa", "theta deg", "M_device FEA N.m", "M_hand = p k N.m", "dV/dtheta FEA (mL/rad, vented)", "k hand (mL/rad)",
             "p |dV/dtheta| N.m"], rows, "FEA vs hand calculation at the pressure peak, with the energy check.", size=7.5)
    D.P("Reading the table: the hand calculation assumes that every radian of knee flexion removes k = 207 mL from the bladder, "
        "i.e. that the back skin of thigh and calf rotates about the knee axis and squeezes the whole bladder. In the FEA the "
        "vented bladder volume changes much less with the knee angle (column 6), because the device does not follow the leg fully: "
        "the 6 mm pad (E 0.0965 MPa) shears, the skin slides under it (mu 0.37) and the soft tissue deforms around the bones. With "
        "dV/dtheta small, the moment the pressure can do work against is small (column 8), and the solver reaction (column 4) is of the "
        "same order - the two FEA numbers check each other. The difference to the hand calculation is therefore a modelling result, "
        "not a convergence problem: for the hand-calculation moment the bladder must be squeezed by the knee rotation, which needs "
        "a stiffer coupling between device and leg than this model has (see the limitations in section 8).")

    # ============================================================ 7 pass / fail
    D.H("7. Pass / fail (owner Q14 limits %s)" % c("brief", "b7"))
    rows = [[x["run"], x["item"], f2(x["value"], 3), f2(x["limit"], 2) if x["limit"] is not None else "-", x["verdict"], x["note"]]
            for x in PF if x["run"] in [n for n in ("CHK_MINI_K", "CHK_FAB4") if n in runs] + prod]
    D.T(["Run", "Check", "FEA value", "Limit", "Verdict", "Note"], rows, "Pass / fail per run (max over the converged steps).", size=6.5,
        verdict_col=4)

    # ============================================================ 8 discussion and limitations
    D.H("8. Idealisations and limitations (state with the results)")
    for t_ in [
        "Cover: orthotropic membrane (E_leg = 1 %% of E_hoop) instead of a tension-only fabric (not available on shells in this solver, "
        "test t6); the flange and end caps stay isotropic. The 1 %% ratio is a modelling choice, not a measured value %s." % c("dec"),
        "Contact penalty: the pad sinks into the skin (median penetration about 6 mm in pre-tension, E-36); skin pressures are "
        "therefore smeared over a larger area and the mean values are the reliable ones; single-node peaks at shell edges are not.",
        "Relaxed runs use frictionless ring-skin contact for convergence (E-26); pad-skin keeps mu 0.37.",
        "Quasi-static: no inertia, no tissue viscoelasticity (no relaxation data in the project); hold = peak frame (D-Q11).",
        "Tissue is a continuous annulus across the 20 mm knee gap around 30 mm rigid bones; no joint capsule, no patella.",
        "Mesh M0 (RAM 7.7 GB); mesh study on M1 with contracted tissue (MS_M1C, section 5); mesh M2 not run (RAM).",
        "Relaxed tissue (G 5.5 kPa): the pre-tension step does not converge with the production contact settings (E-52), so the "
        "relaxed runs R1, R1V, R3, R5, R7 were not run (decisions D-ORDER, D-RELAX %s). The quadriceps are active in early stance, "
        "so contracted tissue is the relevant state for the 13-36 %% pulse; all production results are for contracted tissue." % c("dec"),
        "Option-1 run R6 has no vented twin of its own: its device moment uses R2V interpolated in knee angle (approximate, flagged "
        "in its table). R2 lost its last release frame (87 %%) to a PC restart (E-53); R6 was restarted once after an external stop (E-56).",
        "Ring pre-tension: one calibration iteration; the reached tensions differ from the targets (table in section 5) because the "
        "rings interact through the pad.",
        "Ring tension 'max' values of several hundred N are local values at the closure / hook overlap shells; the front free-strap "
        "value is the ring tension used for calibration and Velcro checks."]:
        D.B(t_)

    # ============================================================ 9 errors
    D.H("9. Errors encountered")
    D.P("All entries of 06_Error_Log\\error_log.csv %s (exact message, step, cause, fix, proof file). Long texts are shortened here; "
        "the CSV and the Error_log sheet of summary_all_runs_%s.xlsx hold the full text." % (c("err"), a.tag))
    errs = J.get("errors") or []
    if errs:
        hdr = errs[0]
        ix = {h: i for i, h in enumerate(hdr)}
        def g(rw, k, n=220):
            v = rw[ix[k]] if k in ix and ix[k] < len(rw) else ""
            v = "".join(ch if (ch >= " " or ch == "\n") else " " for ch in v)
            return v if len(v) <= n else v[:n - 3] + "..."
        D.T(["ID", "Step", "Exact message", "Cause", "Fix"], [[g(rw, "id", 8), g(rw, "step", 60), g(rw, "exact_message", 160),
                                                            g(rw, "cause", 220), g(rw, "fix", 200)] for rw in errs[1:] if rw],
            "Error log.", size=6.5, widths=[1.0, 2.6, 4.2, 4.6, 4.6])

    # ============================================================ 10 references, 11 files
    D.H("10. References")
    for i, (_, t_) in enumerate(REFS, start=1):
        D.P("[%d] %s" % (i, t_), size=9)
    D.H("11. Delivered files")
    for t_ in ["05_Results\\Tables\\%s\\summary_all_runs_%s.xlsx (Summary, Device_moment, PassFail, one sheet per run, Mesh_quality, "
               "Error_log) and the CSV files next to it." % (a.tag, a.tag),
               "05_Results\\Images\\%s\\ (plots, contour maps, mesh views, CAD view)." % a.tag,
               "04_Runs\\<run>\\ native Nastran files (.nas deck copy, .OUT, .LOG, .FNO, .RSF) of every run; 02_Nastran_Model\\<run>\\<run>.nas decks.",
               "06_Error_Log\\error_log.csv, queue_log.txt; 00_Plan_and_Decisions\\ (BRIEF, decisions, STATUS).",
               "scripts\\ (mesh, deck, queue, post-processing, collector, this report builder)."]:
        D.B(t_)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    D.d.save(out)
    print("report:", out, "figures", D.fig, "tables", D.tab, "equations", D.eq)


if __name__ == "__main__":
    main()
