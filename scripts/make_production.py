# -*- coding: utf-8 -*-
r"""Write the production decks R1..R7 and the mesh-study decks into 02_Nastran_Model\<run>\<run>.nas and the queue list
02_Nastran_Model\queue_production.txt (BRIEF sec. 4 priority: R1, mesh study, R2, R3, R5, R7, R4, R6).
Usage: python -P make_production.py --level M0 [--study M0,M1,M2] [--calib 02_Nastran_Model\calib_dT.json]"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
PY = sys.executable
RUNS = [  # id, opt, plim, tissue, padE, seq, vref
    ("R1", 2, 20, "relaxed", 0.0965, "FULL", False),
    ("R2", 2, 20, "contracted", 0.0965, "FULL", False),
    ("R3", 2, 27, "relaxed", 0.0965, "D-R", False),
    ("R4", 2, 27, "contracted", 0.0965, "D-R", False),
    ("R5", 1, 20, "relaxed", 0.0965, "D-R", False),
    ("R6", 1, 20, "contracted", 0.0965, "D-R", False),
    ("R7", 2, 20, "relaxed", 0.276, "D-21", True),
    ("R1V", 2, 20, "relaxed", 0.0965, "FULL", False),       # vented baseline of R1 (p = 0): passive knee moment M0(theta)
    ("R2V", 2, 20, "contracted", 0.0965, "FULL", False),    # vented baseline of R2
]
ORDER = ["R1", "R1V", "MS", "R2", "R2V", "R3", "R5", "R7", "R4", "R6"]


def mesh(level):
    p = os.path.join(R, "02_Nastran_Model", "mesh_%s.pkl" % level)
    if not os.path.exists(p):
        subprocess.check_call([PY, "-P", os.path.join(HERE, "mesh_a07.py"), "--level", level])
    return p


def deck(run, meshp, opt, plim, tissue, padE, seq, vref, calib):
    d = os.path.join(R, "02_Nastran_Model", run)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, run + ".nas")
    cmd = [PY, "-P", os.path.join(HERE, "deck_a07.py"), "--mesh", meshp, "--out", out, "--run", run, "--opt", str(opt),
           "--plim", str(plim), "--tissue", tissue, "--padE", str(padE), "--seq", seq]
    if vref:
        cmd.append("--vref")
    if run.endswith("V"):
        cmd.append("--vent")
    if tissue == "relaxed":
        cmd += ["--mu_ring", "0.0"]          # relaxed tissue: ring-skin frictionless (error log E-26), pad-skin mu 0.37
    if calib and os.path.exists(calib):
        cmd += ["--calib", calib]
    subprocess.check_call(cmd)
    return os.path.relpath(out, R)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="M0")
    ap.add_argument("--study", default="M1,M2")          # M0 = production mesh: R1 itself (frames to 21 %) is the M0 point
    ap.add_argument("--calib", default=os.path.join(R, "02_Nastran_Model", "calib_dT.json"))
    ap.add_argument("--only", default="")
    ap.add_argument("--fast", action="store_true", help="R1/R2 and their vented twins only to the end of release (D-R) - fits a night")
    a = ap.parse_args()
    if a.fast:
        RUNS[:] = [(r[0], r[1], r[2], r[3], r[4], ("D-R" if r[5] == "FULL" else r[5]), r[6]) for r in RUNS]
    mp = mesh(a.level)
    lines = {}
    for run, opt, plim, tissue, padE, seq, vref in RUNS:
        if a.only and run not in a.only.split(","):
            continue
        lines[run] = [deck(run, mp, opt, plim, tissue, padE, seq, vref, a.calib)]
    ms = []
    for lv in [v for v in a.study.split(",") if v]:
        if a.only and "MS" not in a.only.split(","):
            break
        ms.append(deck("MS_" + lv, mesh(lv), 2, 20, "relaxed", 0.0965, "D-21", True, a.calib))
    lines["MS"] = ms
    q = os.path.join(R, "02_Nastran_Model", "queue_production.txt")
    with open(q, "w") as fh:
        fh.write("# production queue (priority order BRIEF sec. 4); one deck per line, relative to the run folder R\n")
        for k in ORDER:
            for ln in lines.get(k, []):
                fh.write(ln + "\n")
    print("queue:", q)
