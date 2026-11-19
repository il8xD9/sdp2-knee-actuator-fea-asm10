"""diagnostic: does the device bend with the knee?  For each subcase: rotation of the bladder's thigh-end and shank-end
sections (best-fit of the bladder nodes in |y| 40..90) about Z, the bladder length change along its top and base lines,
and the skin rotation at the same y.  Usage: python -P diag_bend.py <run.OUT>"""
import sys, os, pickle, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import post_a07 as P
out = sys.argv[1]
base = out[:-4]
m = pickle.load(open(base + "_mesh.pkl", "rb"))
X = np.asarray(m["X"]); S = m["S"]; EL = m["el"]
res, seen = P.parse_out(out)
bl = np.array(sorted(S["bl_nodes"]))
skin = np.array(sorted(set(n for fc, th, y in S["skin"] for n in fc)))
def sec_rot(nodes, Xd, ya, yb):
    sel = [n for n in nodes if ya <= X[n, 1] <= yb]
    a = X[sel][:, :2]; b = Xd[sel][:, :2]
    a0 = a - a.mean(0); b0 = b - b.mean(0)
    H = a0.T @ b0
    ang = math.degrees(math.atan2(H[0, 1] - H[1, 0], H[0, 0] + H[1, 1]))
    return ang
def line_len(nodes, Xd, top):
    # nodes of the bladder on the posterior-most (top) or leg-side (base) line near z = 0
    sel = [n for n in nodes if abs(X[n, 2]) < 4.0 and abs(X[n, 1]) < 85.0]
    xs = X[sel]
    # split by u = x - r(y): top = largest x per y, base = smallest
    from collections import defaultdict
    d = defaultdict(list)
    for n in sel:
        d[round(X[n, 1], 1)].append(n)
    pts = []
    for y in sorted(d):
        ns = d[y]
        n = max(ns, key=lambda k: X[k, 0]) if top else min(ns, key=lambda k: X[k, 0])
        pts.append(n)
    P0 = X[pts]; P1 = Xd[pts]
    L0 = np.linalg.norm(np.diff(P0, axis=0), axis=1).sum(); L1 = np.linalg.norm(np.diff(P1, axis=0), axis=1).sum()
    return L0, L1
print("sub  rot_bl_thigh  rot_bl_shank  bend_bl  rot_skin_th  rot_skin_sh  bend_skin  dL_top  dL_base")
for sub in sorted(res):
    D = res[sub]["disp"]
    if not D:
        continue
    Xd = X.copy()
    for g, v in D.items():
        Xd[g - 1] += v[:3]
    rt = sec_rot(bl, Xd, 40, 90); rs = sec_rot(bl, Xd, -90, -40)
    st = sec_rot(skin, Xd, 40, 90); ss = sec_rot(skin, Xd, -90, -40)
    Lt0, Lt1 = line_len(bl, Xd, True); Lb0, Lb1 = line_len(bl, Xd, False)
    print("%3d  %10.3f  %10.3f  %8.3f  %10.3f  %10.3f  %8.3f  %7.2f  %7.2f" % (sub, rt, rs, rs - rt, st, ss, ss - st, Lt1 - Lt0, Lb1 - Lb0))
