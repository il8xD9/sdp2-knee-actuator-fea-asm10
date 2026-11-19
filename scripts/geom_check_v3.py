# -*- coding: utf-8 -*-
"""v3 geometry check for the rigid-leg reference (B0): when the shank half turns rigidly about the knee axis, how far does its
posterior skin (and the bladder space above it) move into the thigh half?  Evidence for the B0 angle choice (decision D-V3-65).
Uses the mesh skin grids (mesh_M0.pkl, built from geo8.py / geo_A150.json) - no new data.
Usage: python -P geom_check_v3.py [mesh.pkl]"""
import math
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
mp = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "02_Nastran_Model", "mesh_M0.pkl")
m = pickle.load(open(mp, "rb"))
X = np.asarray(m["X"])
S = m["S"]
H = np.asarray(m["meta"]["H"])
sk = sorted(set(n for fc, th, y in S["skin"] for n in fc))
P = X[sk]
post = P[(np.abs(P[:, 2]) < 2.0) & (P[:, 0] > 0)]              # posterior skin line (sagittal plane, back of the leg)
thigh = post[post[:, 1] >= 0]
thigh = thigh[np.argsort(thigh[:, 1])]
shank = post[post[:, 1] < 0]
BL_TOP = 9.18 + 44.0                                            # pad 6 + webbing 3.18 + bladder 44 mm above the skin (CAD)
K_HAND = 206.99                                                 # mL/rad, v12 Table E-1 (d_h 65)
V0 = 423.4                                                      # cm3, vented bladder mid-surface volume (FEA R2, D2)
out = []
for th_deg in (0.7, 3.28, 5.78, 10.43, 15.0, 20.0, 30.0, 45.0, 65.0):
    t = math.radians(th_deg)
    c, s = math.cos(t), math.sin(t)
    worst, ymax = 0.0, 0.0
    for p in shank:
        x, y = p[0] - H[0], p[1] - H[1]
        xr, yr = c * x - s * y + H[0], s * x + c * y + H[1]
        if yr <= 0:
            continue
        rth = np.interp(yr, thigh[:, 1], thigh[:, 0])           # thigh posterior skin x at that y
        d = rth - xr                                            # > 0: the turned shank skin lies inside the thigh tissue
        if d > worst:
            worst, ymax = d, yr
    y_skin = 65.0 * math.tan(t / 2.0)                           # rigid halves overlap |y| < y_skin at the skin line
    y_top = (65.0 + BL_TOP) * math.tan(t / 2.0)                 # ... and |y| < y_top at the device top (bladder space)
    out.append((th_deg, y_skin, y_top, K_HAND * t, 100.0 * K_HAND * t / V0))
print("theta_deg, overlap_y_skin_mm, overlap_y_device_top_mm, k_theta_mL, k_theta_pct_of_V0")
for r in out:
    print("%.2f, %.1f, %.1f, %.1f, %.0f" % r)
with open(os.path.join(ROOT, "05_Results", "geom_check_v3.csv"), "w") as fh:
    fh.write("theta_deg,overlap_y_skin_mm,overlap_y_device_top_mm,k_theta_mL,k_theta_pct_of_V0\n")
    for r in out:
        fh.write("%.2f,%.1f,%.1f,%.1f,%.0f\n" % r)
