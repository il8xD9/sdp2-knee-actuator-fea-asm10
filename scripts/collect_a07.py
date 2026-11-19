# -*- coding: utf-8 -*-
r"""Phase 3 collector: all finished runs in 04_Runs -> 05_Results (tables, images, plots) + a JSON summary for the report builder.
Usage: python -P collect_a07.py --tag v1      (writes 05_Results\Tables\v1, 05_Results\Images\v1; refuses to overwrite an existing
       tag unless the tag starts with 'draft')
Device moment = M_knee(run) - M_knee(vented twin) at the same subcase (R1-R1V, R2-R2V); R3/R5/R7 use R1V, R4/R6 use R2V
(matched by frame, else interpolated in theta = approximate, flagged). Hand calc M = p k, k = 206994 mm3 (M1-M7 v10)."""
import argparse
import csv
import glob
import json
import math
import os
import shutil
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
K_MM3 = 206994.0
LIM = {20: dict(skin=24.0, post=24.0), 27: dict(skin=36.0, post=36.0)}
RING_PEAK, RING_DON = 19.0, 11.0
VM_BL, VM_COV, HOOK_D, HOOK_W = 11.1, 37.2, 5.68, 14.2
VELCRO_T, WEB_T = 65.5, 5300.0
TARGET_T = {"thigh_near": 20.89, "shank_near": 19.59, "thigh_far": 13.3, "shank_far": 9.4}
RINGS = ["thigh_near", "shank_near", "thigh_far", "shank_far"]
ORDER = ["CHK_MINI_K", "CHK_FAB", "CHK_FAB2", "CHK_FAB3", "CHK_FAB4", "CAL_relaxed_1", "CAL_contracted_1",
         "R2", "R2V", "R4", "R6", "MS_M1C", "R1", "R1V", "R3", "R5", "R7", "MS_M1", "MS_M2"]
TWIN = {"R1": "R1V", "R2": "R2V", "R3": "R1V", "R5": "R1V", "R7": "R1V", "R4": "R2V", "R6": "R2V", "MS_M1": None, "MS_M2": None}
DESC = {
    "CHK_MINI_K": "check: contracted, plate-stiff cover (12I/t3 = 1), D1-D2-flex 5.78-inflate 20 kPa-VREF",
    "CHK_FAB": "check: as MINI_K, cover + flange bending 0.003",
    "CHK_FAB2": "check: as FAB, flange bending 1.0",
    "CHK_FAB3": "check: as MINI_K, orthotropic cover body + flange (E_leg 1 %)",
    "CHK_FAB4": "check: as FAB3, isotropic flange (= production cover)",
    "CAL_relaxed_1": "pre-tension calibration, relaxed tissue (D1-D2)",
    "CAL_contracted_1": "pre-tension calibration, contracted tissue (D1-D2)",
    "R1": "option 2, 20 kPa, relaxed, D -> release", "R1V": "vented twin of R1 (p = 0)",
    "R2": "option 2, 20 kPa, contracted, D -> release", "R2V": "vented twin of R2 (p = 0)",
    "R3": "option 2, 27 kPa, relaxed, D -> release", "R4": "option 2, 27 kPa, contracted, D -> release",
    "R5": "option 1, 20 kPa, relaxed, D -> release", "R6": "option 1, 20 kPa, contracted, D -> release",
    "R7": "option 2, 20 kPa, relaxed, pad E 0.276 MPa, D -> 21 % + VREF",
    "MS_M1": "mesh study M1 (finer), R1 D -> 21 % + VREF", "MS_M2": "mesh study M2 (finest), R1 D -> 21 % + VREF",
    "MS_M1C": "mesh study: mesh M1 (finer), contracted, option 2 20 kPa, D -> 21 % + VREF (compare R2 on M0)"}
MESH_STUDY = [("MS_M1C", "R2")]
MS_KEYS = ["M_knee_ext_Nm", "p_under_bladder_mean_kPa", "p_posterior_knee_peak_kPa", "T_thigh_near_front_N", "T_shank_near_front_N",
           "T_thigh_far_front_N", "T_shank_far_front_N", "V_bladder_mid_cm3", "vm_max_bladder_MPa"]


def mesh_study(runs):
    out = []
    for fine, coarse in MESH_STUDY:
        if fine not in runs or coarse not in runs:
            continue
        cr = [x for x in runs[coarse]["rows"] if x["converged"]]
        for x in runs[fine]["rows"]:
            if not x["converged"]:
                continue
            m = [y for y in cr if y["name"] == x["name"] and y["kind"] == x["kind"]]
            if not m:
                continue
            y = m[0]
            for k in MS_KEYS:
                a_, b_ = y.get(k), x.get(k)
                if a_ is None or b_ is None:
                    continue
                out.append(dict(fine=fine, coarse=coarse, step=x["name"], kind=x["kind"], quantity=k, coarse_value=a_, fine_value=b_,
                                diff_pct=(100.0 * (b_ - a_) / abs(a_)) if abs(a_) > 1e-9 else None))
    return out
COL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def fnum(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def load_runs():
    runs = {}
    for name in ["SMOKE_K"] + ORDER:
        if name in runs:
            continue
        d = os.path.join(R, "04_Runs", name)
        res = glob.glob(os.path.join(d, "*_results.csv"))
        if not res:
            continue
        rows = list(csv.DictReader(open(res[0], encoding="utf-8-sig")))
        for r_ in rows:
            for k in list(r_):
                if k not in ("name", "kind", "converged"):
                    v = fnum(r_[k])
                    r_[k] = v
            r_["converged"] = str(r_.get("converged")).strip().lower() == "true"
            if r_.get("T_thigh_near_front_N") is None:      # no result tables in the .OUT for this step (e.g. R2 85 %, E-53)
                r_["converged"] = False
        rt = {}
        rtf = os.path.join(d, "runtime.txt")
        if os.path.exists(rtf):
            for tok in open(rtf).read().split():
                if "=" in tok:
                    a, b = tok.split("=", 1)
                    rt[a] = b
        plog = glob.glob(os.path.join(d, "*_post_log.txt"))
        head = open(plog[0], encoding="utf-8", errors="ignore").readline().strip() if plog else ""
        steps = glob.glob(os.path.join(R, "02_Nastran_Model", name, "*_steps.csv")) or glob.glob(os.path.join(d, "*_steps.csv"))
        nsteps = len(list(csv.DictReader(open(steps[0])))) if steps else None
        runs[name] = dict(name=name, dir=d, csv=res[0], rows=rows, runtime=rt, post_head=head, nsteps=nsteps,
                          base=os.path.basename(res[0])[:-12], desc=DESC.get(name, ""))
    return runs


def plim_of(run):
    ps = [r_["p_kPa"] for r_ in run["rows"] if r_["p_kPa"] is not None]
    return 27 if ps and max(ps) > 23.5 else 20


def device_moment(runs):
    out = {}
    for name, run in runs.items():
        tw = TWIN.get(name)
        if not tw or tw not in runs:
            continue
        base = [r_ for r_ in runs[tw]["rows"] if r_["converged"]]
        rows = []
        for r_ in run["rows"]:
            if not r_["converged"] or r_["M_knee_ext_Nm"] is None:
                continue
            match = [b for b in base if b["kind"] == r_["kind"] and b["frame"] == r_["frame"] and b["theta"] is not None
                     and r_["theta"] is not None and abs(b["theta"] - r_["theta"]) < 1e-3]
            approx = False
            if match:
                m0 = match[-1]["M_knee_ext_Nm"]
                fx0 = match[-1]["Fshank_x_N"]
                v0 = match[-1]["V_bladder_mid_cm3"]
            else:
                pts = sorted((b["theta"], b["M_knee_ext_Nm"], b["Fshank_x_N"], b["V_bladder_mid_cm3"]) for b in base
                             if b["kind"] in ("S", "W", "R", "S_sub") and b["theta"] is not None)
                if not pts or r_["theta"] is None:
                    continue
                th = np.array([p[0] for p in pts])
                m0 = float(np.interp(r_["theta"], th, [p[1] for p in pts]))
                fx0 = float(np.interp(r_["theta"], th, [p[2] for p in pts]))
                v0 = float(np.interp(r_["theta"], th, [p[3] for p in pts]))
                approx = True
            p = r_["p_kPa"] or 0.0
            rows.append(dict(subcase=int(r_["subcase"]), name=r_["name"], kind=r_["kind"], frame=r_["frame"], ms=r_["ms"],
                             theta=r_["theta"], p_kPa=p, M_run=r_["M_knee_ext_Nm"], M_vented=m0,
                             M_device=r_["M_knee_ext_Nm"] - m0, M_hand=p * K_MM3 * 1e-6,
                             dFx_device=(r_["Fshank_x_N"] - fx0) if (r_["Fshank_x_N"] is not None and fx0 is not None) else None,
                             dV_cm3=(r_["V_bladder_mid_cm3"] - v0) if (r_["V_bladder_mid_cm3"] is not None and v0 is not None) else None,
                             twin=tw, approx=approx))
        out[name] = rows
    # check runs: inflated subcase vs vented before / VREF
    for name, run in runs.items():
        rr = run["rows"]
        w = [r_ for r_ in rr if r_["kind"] == "W" and r_["converged"]]
        v = [r_ for r_ in rr if r_["kind"] == "VREF" and r_["converged"]]
        if w and v and name not in out:
            # inflated step = the last W step before VREF (VREF is vented at the same angle); with one W step (check runs) the
            # vented step just before it is a second reference; with several W steps (mesh study) only VREF is at the same angle
            wl = [r_ for r_ in w if r_["subcase"] < v[0]["subcase"]][-1]
            if len(w) == 1:
                before = [r_ for r_ in rr if r_["converged"] and r_["subcase"] < wl["subcase"]][-1]
            else:
                before = v[0]
            out[name] = [dict(subcase=int(wl["subcase"]), name=wl["name"], kind="W", frame=wl["frame"], ms=wl["ms"],
                              theta=wl["theta"], p_kPa=wl["p_kPa"], M_run=wl["M_knee_ext_Nm"],
                              M_vented=before["M_knee_ext_Nm"], M_device=wl["M_knee_ext_Nm"] - before["M_knee_ext_Nm"],
                              M_device_vref=wl["M_knee_ext_Nm"] - v[0]["M_knee_ext_Nm"], M_hand=wl["p_kPa"] * K_MM3 * 1e-6,
                              dFx_device=wl["Fshank_x_N"] - v[0]["Fshank_x_N"],
                              dV_cm3=wl["V_bladder_mid_cm3"] - v[0]["V_bladder_mid_cm3"] if len(w) > 1 else
                              wl["V_bladder_mid_cm3"] - before["V_bladder_mid_cm3"],
                              twin="own vented steps" if len(w) == 1 else "own VREF", approx=False)]
    return out


def mx(rows, key, kinds=None):
    vals = [r_[key] for r_ in rows if r_["converged"] and r_.get(key) is not None and (kinds is None or r_["kind"] in kinds)]
    return (max(vals), vals) if vals else (None, [])


def passfail(runs, dm):
    pf = []
    for name, run in runs.items():
        if name.startswith("CAL"):
            continue
        rows = run["rows"]
        lim = LIM[plim_of(run)]
        W = ("W",)
        def add(item, val, limit, ok_le=True, note=""):
            if val is None:
                pf.append(dict(run=name, item=item, value=None, limit=limit, verdict="n/a", note=note or "no converged step"))
                return
            ok = val <= limit if ok_le else val >= limit
            pf.append(dict(run=name, item=item, value=val, limit=limit, verdict="PASS" if ok else "FAIL", note=note))
        add("skin mean under bladder, max over pulse (kPa)", mx(rows, "p_under_bladder_mean_kPa", W)[0], lim["skin"])
        add("skin peak under bladder, max over pulse (kPa) [reported]", mx(rows, "p_under_bladder_peak_kPa", W)[0], lim["skin"],
            note="limit applies to the mean; peak reported")
        add("posterior-knee zone peak, max over pulse (kPa)", mx(rows, "p_posterior_knee_peak_kPa", W)[0], lim["post"])
        rp = [mx(rows, "p_ring_%s_peak_kPa" % k, W)[0] for k in RINGS]
        rp = [v for v in rp if v is not None]
        add("ring contact peak, max over pulse (kPa)", max(rp) if rp else None, RING_PEAK,
            note="single-node peaks at the ring edges (mesh-dependent edge singularity of a sharp shell edge on soft tissue)")
        rd = [mx(rows, "p_ring_%s_mean_kPa" % k, ("D",))[0] for k in RINGS]
        rd = [v for v in rd if v is not None]
        add("ring contact mean in donning, max (kPa)", max(rd) if rd else None, RING_DON)
        add("bladder von Mises max (MPa)", mx(rows, "vm_max_bladder_MPa")[0], VM_BL)
        add("cover body von Mises max (MPa)", mx(rows, "vm_max_cover_MPa")[0], VM_COV)
        add("cover flange von Mises max (MPa) [reported]", mx(rows, "vm_max_cover_flange_MPa")[0], VM_COV,
            note="flange strip shares nodes with the ring shells (E-29: local artefact)")
        add("hooks von Mises at pre-tension (MPa)", mx(rows, "vm_max_hooks_MPa", ("D",))[0], HOOK_D)
        add("hooks von Mises during pulse (MPa)", mx(rows, "vm_max_hooks_MPa", W)[0], HOOK_W)
        tf = [mx(rows, "T_%s_front_N" % k)[0] for k in RINGS]
        tf = [v for v in tf if v is not None]
        add("Velcro band tension (front free strap) max (N)", max(tf) if tf else None, VELCRO_T)
        tm = [mx(rows, "T_%s_max_N" % k)[0] for k in RINGS]
        tm = [v for v in tm if v is not None]
        add("webbing tension local max (N)", max(tm) if tm else None, WEB_T)
        d = [x for x in dm.get(name, []) if x["kind"] == "W"]
        if d:
            fx = [abs(x["dFx_device"]) for x in d if x["dFx_device"] is not None]
            pf.append(dict(run=name, item="ACL: |net forward shank force from the device|, max over pulse (N)",
                           value=max(fx) if fx else None, limit=None, verdict="report", note="DR-B6-1: should be ~0"))
            mfe = max(x["M_device"] for x in d)
            pf.append(dict(run=name, item="device knee moment, max over pulse (N.m)", value=mfe,
                           limit=max(x["M_hand"] for x in d), verdict="PASS" if mfe >= 0.9 * max(x["M_hand"] for x in d) else "FAIL",
                           note="limit = hand calc p k at the peak; FAIL = FEA does not confirm the hand-calc torque"))
        s = [x for x in dm.get(name, []) if x["theta"] is not None and x["theta"] <= 0]
        if s:
            pf.append(dict(run=name, item="device moment at theta <= 0 (N.m), max |.|", value=max(abs(x["M_device"]) for x in s),
                           limit=None, verdict="report", note="p = 0 at theta <= 0 by the waveform"))
    return pf


def style_ax(ax, xl, yl, title):
    ax.set_xlabel(xl, color=INK2, fontsize=9); ax.set_ylabel(yl, color=INK2, fontsize=9)
    ax.set_title(title, color=INK, fontsize=10.5, loc="left")
    ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#b5b4ae")
    ax.tick_params(colors=INK2, labelsize=8.5)


def plots(runs, dm, img):
    figs = {}
    prod = [n for n in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "MS_M1", "MS_M2") if n in dm and dm[n]]
    # 1 device moment vs stance %
    if prod:
        fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
        for i, n in enumerate(prod):
            d = [x for x in dm[n] if x["kind"] in ("S", "W", "R") and x["frame"] is not None]
            if not d:
                continue
            ax.plot([x["frame"] for x in d], [x["M_device"] for x in d], "-o", color=COL[i % 8], lw=2, ms=4, label="%s FEA" % n)
            ax.plot([x["frame"] for x in d], [x["M_hand"] for x in d], "--", color=COL[i % 8], lw=1.2, alpha=0.8,
                    label="%s hand calc p k" % n)
        style_ax(ax, "stance (%)", "device knee extension moment (N.m)", "Device moment: FEA (run - vented twin) vs hand calculation")
        ax.legend(fontsize=7.5, ncol=2, frameon=False)
        fig.tight_layout(); p = os.path.join(img, "device_moment_vs_stance.png"); fig.savefig(p); plt.close(fig)
        figs["device_moment"] = p
    # 2 check runs bar chart
    chk = [n for n in ("CHK_MINI_K", "CHK_FAB4") if n in dm]
    if chk:
        fig, ax = plt.subplots(figsize=(6.0, 3.0), dpi=200)
        labs, vals, cols = [], [], []
        for n in chk:
            x = dm[n][0]
            labs += ["%s\nvs vented before" % n, "%s\nvs VREF" % n]
            vals += [x["M_device"], x.get("M_device_vref", 0.0)]
            cols += [COL[0], COL[0]]
        labs.append("hand calc\np k at 20 kPa"); vals.append(dm[chk[0]][0]["M_hand"]); cols.append(COL[1])
        ax.bar(range(len(vals)), vals, color=cols, width=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + (0.06 if v >= 0 else -0.06), "%.2f" % v, ha="center", va=("bottom" if v >= 0 else "top"), fontsize=8, color=INK)
        ax.set_xticks(range(len(vals))); ax.set_xticklabels(labs, fontsize=7.5)
        ax.axhline(0, color="#8a8984", lw=0.8)
        ax.set_ylim(min(0, min(vals)) - 0.6, max(vals) * 1.12)
        style_ax(ax, "", "moment at 21 %, 5.78 deg (N.m)", "Device moment from inflation at the peak frame (check runs)")
        ax.grid(False, axis="x")
        fig.tight_layout(); p = os.path.join(img, "check_runs_device_moment.png"); fig.savefig(p); plt.close(fig)
        figs["check_moment"] = p
    # 3 skin pressure vs stance (mean + posterior peak) for production runs
    show = [n for n in ("R1", "R2", "R3", "R4", "R5", "R6") if n in runs]
    if show:
        fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
        for i, n in enumerate(show):
            d = [r_ for r_ in runs[n]["rows"] if r_["converged"] and r_["kind"] in ("S", "W", "R")]
            ax.plot([r_["frame"] for r_ in d], [r_["p_under_bladder_mean_kPa"] for r_ in d], "-o", color=COL[i % 8], lw=2, ms=4,
                    label="%s mean under bladder" % n)
            ax.plot([r_["frame"] for r_ in d], [r_["p_posterior_knee_peak_kPa"] for r_ in d], ":", color=COL[i % 8], lw=1.5,
                    label="%s posterior-knee peak" % n)
        ax.axhline(24, color="#d03b3b", lw=1.2); ax.text(ax.get_xlim()[0], 24.4, "limit 24 kPa (20 kPa runs)", fontsize=7.5, color=INK2)
        style_ax(ax, "stance (%)", "skin contact pressure (kPa)", "Skin pressure under the bladder and in the posterior-knee zone")
        ax.legend(fontsize=7, ncol=2, frameon=False)
        fig.tight_layout(); p = os.path.join(img, "skin_pressure_vs_stance.png"); fig.savefig(p); plt.close(fig)
        figs["skin"] = p
        # 4 ring tension (front free strap) for the first production run
        n = show[0]
        d = [r_ for r_ in runs[n]["rows"] if r_["converged"]]
        fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
        for i, k in enumerate(RINGS):
            ax.plot(range(len(d)), [r_["T_%s_front_N" % k] for r_ in d], "-o", color=COL[i], lw=2, ms=3.5, label=k.replace("_", " "))
            ax.axhline(TARGET_T[k], color=COL[i], lw=0.9, ls="--")
        ax.set_xticks(range(len(d))); ax.set_xticklabels([("%s" % (int(r_["frame"]) if r_["kind"] not in ("D",) else r_["name"][:2]))
                                                          for r_ in d], fontsize=6.5, rotation=90)
        style_ax(ax, "step (D = donning, then stance %)", "ring tension, front free strap (N)",
                 "%s ring tension per step (dashed = pre-tension target)" % n)
        ax.legend(fontsize=7.5, ncol=4, frameon=False)
        fig.tight_layout(); p = os.path.join(img, "ring_tension_%s.png" % n); fig.savefig(p); plt.close(fig)
        figs["rings"] = p
        # 5 bladder volume vs stance
        fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=200)
        for i, n in enumerate(show):
            d = [r_ for r_ in runs[n]["rows"] if r_["converged"] and r_["kind"] in ("D", "S", "W", "R")]
            ax.plot(range(len(d)), [r_["V_bladder_mid_cm3"] for r_ in d], "-o", color=COL[i % 8], lw=2, ms=3.5, label=n)
        style_ax(ax, "step index", "bladder mid-surface volume (cm3)", "Bladder volume at each step")
        ax.legend(fontsize=7.5, ncol=3, frameon=False)
        fig.tight_layout(); p = os.path.join(img, "bladder_volume.png"); fig.savefig(p); plt.close(fig)
        figs["volume"] = p
    return figs


def write_xlsx(path, runs, dm, pf, mesh_q, errs, ms=()):
    wb = Workbook()
    hdr = Font(bold=True); fill = PatternFill("solid", fgColor="D9E2F3")
    def sheet(title, header, rows, first=False):
        ws = wb.active if first else wb.create_sheet(title[:31])
        ws.title = title[:31]
        ws.append(header)
        for c in ws[1]:
            c.font = hdr; c.fill = fill; c.alignment = Alignment(wrap_text=True, vertical="top")
        for r_ in rows:
            ws.append([("" if v is None else (ILLEGAL_CHARACTERS_RE.sub(" ", v) if isinstance(v, str) else v)) for v in r_])
        ws.freeze_panes = "A2"
        for i, h in enumerate(header, start=1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = max(10, min(45, len(str(h)) + 2))
        return ws
    sheet("Summary", ["run", "description", "subcases converged / planned", "runtime s", "peak MB", "post-processor header"],
          [[n, r_["desc"], "%d / %s" % (sum(1 for x in r_["rows"] if x["converged"]), r_["nsteps"]),
            r_["runtime"].get("seconds"), r_["runtime"].get("peakMB"), r_["post_head"]] for n, r_ in runs.items()], first=True)
    keys = ["run", "subcase", "name", "kind", "frame", "ms", "theta", "p_kPa", "M_run", "M_vented", "M_device", "M_device_vref",
            "M_hand", "dFx_device", "dV_cm3", "twin", "approx"]
    sheet("Device_moment", keys, [[n] + [x.get(k) for k in keys[1:]] for n, d in dm.items() for x in d])
    sheet("PassFail", ["run", "item", "value", "limit", "verdict", "note"],
          [[x["run"], x["item"], x["value"], x["limit"], x["verdict"], x["note"]] for x in pf])
    for n, r_ in runs.items():
        cols = list(r_["rows"][0].keys()) if r_["rows"] else []
        sheet("run_" + n, cols, [[x.get(c) for c in cols] for x in r_["rows"]])
    if ms:
        kk = ["fine", "coarse", "step", "kind", "quantity", "coarse_value", "fine_value", "diff_pct"]
        sheet("Mesh_study", kk, [[x[k] for k in kk] for x in ms])
    if mesh_q:
        sheet("Mesh_quality", mesh_q[0], mesh_q[1:])
    if errs:
        sheet("Error_log", errs[0], errs[1:])
    wb.save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    tdir = os.path.join(R, "05_Results", "Tables", a.tag)
    idir = os.path.join(R, "05_Results", "Images", a.tag)
    if os.path.exists(tdir) and not a.tag.startswith("draft"):
        sys.exit("tag %s exists - never overwrite delivered results; use a new tag" % a.tag)
    for d in (tdir, idir):
        os.makedirs(d, exist_ok=True)
    runs = load_runs()
    dm = device_moment(runs)
    pf = passfail(runs, dm)
    mesh_q = []
    mq = os.path.join(R, "02_Nastran_Model", "mesh_quality_M0.csv")
    if os.path.exists(mq):
        mesh_q = list(csv.reader(open(mq)))
    errs = list(csv.reader(open(os.path.join(R, "06_Error_Log", "error_log.csv"), encoding="utf-8", errors="ignore")))
    figs = plots(runs, dm, idir)
    copied = {}
    for n, r_ in runs.items():
        for png in glob.glob(os.path.join(r_["dir"], "*.png")):
            dst = os.path.join(idir, "%s__%s" % (n, os.path.basename(png)))
            shutil.copy2(png, dst)
            copied.setdefault(n, []).append(dst)
        shutil.copy2(r_["csv"], os.path.join(tdir, "%s_results.csv" % n))
    for lv in ("M0", "M1", "M2"):
        v = os.path.join(R, "02_Nastran_Model", "mesh_%s_view.png" % lv)
        if os.path.exists(v):
            shutil.copy2(v, os.path.join(idir, "mesh_%s_view.png" % lv)); copied.setdefault("mesh", []).append(os.path.join(idir, "mesh_%s_view.png" % lv))
    xl = os.path.join(tdir, "summary_all_runs_%s.xlsx" % a.tag)
    ms = mesh_study(runs)
    write_xlsx(xl, runs, dm, pf, mesh_q, errs, ms)
    with open(os.path.join(tdir, "device_moment_all.csv"), "w", newline="") as fh:
        keys = ["run", "subcase", "name", "kind", "frame", "ms", "theta", "p_kPa", "M_run", "M_vented", "M_device", "M_device_vref",
                "M_hand", "dFx_device", "dV_cm3", "twin", "approx"]
        w = csv.writer(fh); w.writerow(keys)
        for n, d in dm.items():
            for x in d:
                w.writerow([n] + [x.get(k) for k in keys[1:]])
    with open(os.path.join(tdir, "passfail_all.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["run", "item", "value", "limit", "verdict", "note"])
        for x in pf:
            w.writerow([x["run"], x["item"], x["value"], x["limit"], x["verdict"], x["note"]])
    js = dict(tag=a.tag, runs={n: dict(desc=r_["desc"], runtime=r_["runtime"], post_head=r_["post_head"], nsteps=r_["nsteps"],
                                         base=r_["base"], rows=r_["rows"]) for n, r_ in runs.items()},
              device_moment=dm, passfail=pf, figs=figs, mesh_study=ms, copied=copied, xlsx=xl, mesh_quality=mesh_q, errors=errs)
    json.dump(js, open(os.path.join(tdir, "collect_%s.json" % a.tag), "w"), indent=1, default=str)
    print("runs:", ", ".join(runs)); print("device moment:", {n: len(d) for n, d in dm.items()}); print("tables:", tdir); print("images:", idir)
