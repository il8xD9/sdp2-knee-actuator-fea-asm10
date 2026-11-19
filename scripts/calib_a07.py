# -*- coding: utf-8 -*-
"""Pre-tension calibration (owner option (a), D-Q7/D-Q8): update the ring cooling dT_k so that the mean hoop tension of the
free strap on the skin (front part, outside the pad / cover-flange laminate) of every ring at the end of the donning step D2 reaches its target.  T is close to proportional to dT (shrink strain alpha dT goes almost
entirely into tissue indentation; the ring's own elastic strain is ~0.05 %), so a secant / proportional update is used.
Targets: thigh near 20.89 N, shank near 19.59 N, thigh far 13.3 N, calf far 9.4 N (M1-M7 v10 Table G-1 and D-Q7).
Usage: python -P calib_a07.py <D-run _results.csv> <calib.json> <tissue> [--sub 2]"""
import csv
import json
import os
import pickle
import sys

TARGET = {"thigh_near": 20.89, "shank_near": 19.59, "thigh_far": 13.3, "shank_far": 9.4}


def main(res_csv, calib, tissue, sub=2):
    rows = list(csv.DictReader(open(res_csv)))
    row = [r for r in rows if int(r["subcase"]) == sub]
    if not row or not row[0].get("T_thigh_near_front_N"):
        print("calibration skipped: subcase %d not converged in %s" % (sub, res_csv))
        return
    row = row[0]
    info = pickle.load(open(res_csv.replace("_results.csv", "_info.pkl"), "rb"))
    dT_old = info["dT"]
    c = json.load(open(calib)) if os.path.exists(calib) else {}
    hist = c.setdefault("history", [])
    new = {}
    for nm, T0 in TARGET.items():
        T = float(row["T_%s_front_N" % nm])          # free strap on the skin (front), = p R b of Table G-1
        prev = [h for h in hist if h["tissue"] == tissue and h["ring"] == nm]
        if prev and abs(prev[-1]["T"] - T) > 1e-6 and abs(prev[-1]["dT"] - dT_old[nm]) > 1e-9:
            # secant on the last two points
            d1, T1 = prev[-1]["dT"], prev[-1]["T"]
            dn = dT_old[nm] + (T0 - T) * (dT_old[nm] - d1) / (T - T1)
        else:
            dn = dT_old[nm] * T0 / T if T > 1e-6 else dT_old[nm] * 2.0
        dn = max(min(dn, -0.5), 4.0 * dT_old[nm]) if dT_old[nm] < 0 else dn
        hist.append(dict(tissue=tissue, ring=nm, dT=dT_old[nm], T=T, target=T0))
        new[nm] = round(dn, 3)
        print("%-11s dT %8.3f -> T %7.3f N (target %5.2f, error %+6.1f %%)  next dT %8.3f" % (nm, dT_old[nm], T, T0, 100 * (T - T0) / T0, dn))
    c[tissue] = new
    json.dump(c, open(calib, "w"), indent=1)


if __name__ == "__main__":
    sub = int(sys.argv[sys.argv.index("--sub") + 1]) if "--sub" in sys.argv else 2
    main(sys.argv[1], sys.argv[2], sys.argv[3], sub)
