# -*- coding: utf-8 -*-
"""Multi-subcase SOL 106 (NLSTATIC) deck for full asseymbly 07 on the Inventor Nastran solver (ADS NASTRAN 20.2).

Run definition: --run R1 --opt 2 --plim 20 --tissue relaxed --padE 0.0965 --seq FULL|D|D-21|D-R|D-SW [--vref]
Physics (BRIEF sec. 2/3, decisions 13 Nov):
  * PARAM,LGDISP,1 (large displacement, follower pressure); each subcase continues from the previous one.
  * Bones rigid: tissue grids on the bone bores (r = 15) SPC 123; thigh bore fixed; shank bore driven by SPCD to the exact
    rigid rotation about the knee axis (Z through X = r(0) - 65 = 4.06, Y = 0); flexion theta > 0 = shank towards +X.
    (RBE2 is linear in this solver, error log E-11.)  Knee moment = sum (x - H) x F_spc over the shank bore (post_a07.py).
  * Air pressure: PLOAD4 (THRU ranges) on ALL bladder shell elements, normals outward -> +p inflates (test pr_mat1).
  * Pre-tension: rings (MAT8, A1 = alpha along the hoop only) cooled by dT_k per ring from subcase D2 on (TEMPERATURE(LOAD)).
  * Contacts (BSCONP TYPE 1 = separation, verified by the c_* tests): pad bottom / seats <-> skin and every ring's skin part
    <-> skin with mu 0.37 (SFAC 0.01, E-21); bladder <-> cover and bladder <-> pad top (base) frictionless.  Bonded joints are
    shared nodes (webbing-pad, hook-webbing, flange-pad/webbing, cover wall-pad, carrier stack-pad, tab-stack, flap).
  * Gravity / inertia off.
Usage: python -P deck_a07.py --mesh <mesh.pkl> --out <deck.nas> --run R1 --opt 2 --plim 20 --tissue relaxed --seq D-21 [--calib file.json]"""
import argparse
import csv
import json
import math
import os
import pickle

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TISSUE = {"relaxed": (0.00275, 0.0275), "contracted": (0.2, 2.0)}
ALPHA_RING = 1.0e-3
TREF = 20.0
MU_SKIN = 0.37
SFAC_SKIN = None        # None = by tissue state (error log E-21, E-30, E-36)
SFAC_BY_TISSUE = {"contracted": 0.01, "relaxed": 0.01}   # SFAC 1 diverged in D1 for the contracted tissue too (E-36)
SFAC_DEV = 1.0          # bladder-cover / bladder-base (solver default penalty)
# option 2 window: frame, ms, theta, p20, p27 (BRIEF sec. 3, Biomech O2 Waveform_Opt2 + M1-M7 v10 Eq. 20-21)
W2 = [(13, 92, 3.28, 6.9, 6.9), (14, 99, 3.93, 13.0, 13.0), (15, 106, 4.50, 15.2, 18.6), (16, 113, 4.95, 16.7, 22.5),
      (17, 120, 5.29, 17.8, 24.1), (18, 127, 5.53, 18.8, 25.4), (19, 134, 5.68, 19.4, 26.2), (20, 141, 5.76, 19.8, 26.8),
      (21, 148, 5.78, 20.0, 27.0), (22, 155, 5.75, 19.9, 26.9), (23, 162, 5.68, 19.6, 26.5), (24, 169, 5.59, 19.2, 25.9),
      (25, 176, 5.48, 18.6, 25.1), (26, 183, 5.37, 17.9, 24.1), (27, 190, 5.25, 17.1, 23.0), (28, 197, 5.15, 16.2, 21.9),
      (29, 204, 5.05, 15.3, 20.7), (30, 212, 4.98, 14.4, 19.5), (31, 219, 4.91, 13.5, 18.3), (32, 226, 4.84, 12.6, 17.1),
      (33, 233, 4.79, 11.8, 15.2), (34, 240, 4.73, 10.9, 11.2), (35, 247, 4.68, 7.0, 7.0), (36, 254, 4.63, 2.8, 2.8)]
S1 = [(1, 7, -1.92), (3, 21, -0.76), (6, 42, 0.01), (9, 63, 0.88), (12, 85, 2.59)]
REL = [(37, 4.57), (40, 4.36), (45, 3.99), (50, 3.74), (55, 3.68), (60, 3.78), (65, 4.06), (70, 4.65), (75, 5.63), (80, 7.10),
       (85, 9.25), (87, 10.43)]
TOFF = [(90, 12.83), (95, 19.13), (100, 27.81)]
P_RES = 2.4
DTH_MAX = 2.5
NINC_D = 10
SKIP = []
VENT = False
MU_RING = None          # None = MU_SKIN; relaxed runs: 0.0 (error log E-26)


def f(v):
    s = "%.7g" % float(v)
    if "." not in s:
        s = s.replace("e", ".e") if "e" in s else s + "."
    return s


def opt1_frames(plim):
    rows = []
    with open(os.path.join(ROOT, "00_Plan_and_Decisions", "waveform_O2_opt1.csv")) as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("stance"):
                continue
            a = line.strip().split(",")
            rows.append((int(a[0]), float(a[1]), float(a[2]), float(a[4])))
    d21 = [r[2] for r in rows if r[0] == 21][0]
    return [(r[0], r[1], r[3], plim * r[2] / d21) for r in rows if 9 <= r[0] <= 44]


def sequence(opt, plim, seq, vref=False):
    """list of steps: dict(name, kind, frame, ms, theta, p, ninc, therm)"""
    st = [dict(name="D1 donning (25 % tightening)", kind="D", frame=0, ms=0.0, theta=0.0, p=0.0, ninc=NINC_D, therm=0.25),
          dict(name="D2 pre-tension", kind="D", frame=0, ms=0.0, theta=0.0, p=0.0, ninc=2 * NINC_D, therm=True)]
    if seq == "D":
        return st
    if seq == "MINI":          # check deck: flex vented to the 21 % angle, inflate to the peak there, vent again (VREF)
        th21 = [w for w in W2 if w[0] == 21][0][2]
        st.append(dict(name="flex vented to %.2f deg" % th21, kind="S", frame=21, ms=148.0, theta=th21, p=0.0, ninc=3, therm=True))
        st.append(dict(name="W 21%% inflate %d kPa" % plim, kind="W", frame=21, ms=148.0, theta=th21, p=float(plim), ninc=8, therm=True))
        vref = True
        seq = "MINI_DONE"
    if seq == "MINI_DONE":
        win = []
    elif opt == 2:
        for fr, ms, th in S1:
            st.append(dict(name="S1 %d%%" % fr, kind="S", frame=fr, ms=float(ms), theta=th, p=0.0, ninc=2, therm=True))
        win = [(fr, ms, th, (p20 if plim == 20 else p27)) for fr, ms, th, p20, p27 in W2]
    else:
        for fr, ms, th in S1[:3]:
            st.append(dict(name="S1 %d%%" % fr, kind="S", frame=fr, ms=float(ms), theta=th, p=0.0, ninc=2, therm=True))
        win = opt1_frames(plim)
    for fr, ms, th, p in win:
        rising = p >= st[-1]["p"] - 1e-9
        st.append(dict(name="W %d%%" % fr, kind="W", frame=fr, ms=float(ms), theta=th, p=p, ninc=4 if rising else 2, therm=True))
        if seq == "D-21" and fr == 21:
            break
    if seq not in ("D-21", "MINI_DONE"):
        lastw = st[-1]["frame"]
        for fr, th in REL:
            if fr <= lastw:
                continue
            st.append(dict(name="R %d%%" % fr, kind="R", frame=fr, ms=fr * 7.05, theta=th, p=P_RES, ninc=3, therm=True))
        if seq in ("FULL", "D-SW"):
            for fr, th in TOFF:
                st.append(dict(name="TO %d%%" % fr, kind="TO", frame=fr, ms=fr * 7.05, theta=th, p=P_RES, ninc=4, therm=True))
            a0 = TOFF[-1][1]
            for a, b in ((a0, 65.0), (65.0, 78.0)):
                n = int(math.ceil((b - a) / DTH_MAX))
                for k in range(1, n + 1):
                    th = a + (b - a) * k / n
                    st.append(dict(name="SW %.1f deg" % th, kind="SW", frame=100, ms=0.0, theta=th, p=P_RES, ninc=4, therm=True))
    if vref:
        last = st[-1]
        st.append(dict(name="VREF vented at %.2f deg" % last["theta"], kind="VREF", frame=last["frame"], ms=last["ms"],
                       theta=last["theta"], p=0.0, ninc=4, therm=True))
    # split angle jumps > DTH_MAX into sub-steps (SPCD is linear inside a subcase)
    out = []
    for s_ in st:
        if out:
            d = s_["theta"] - out[-1]["theta"]
            n = int(math.ceil(abs(d) / DTH_MAX - 1e-9))
            for k in range(1, n):
                t = out[-1]["theta"]
                q = dict(s_)
                q["name"] = s_["name"] + " sub %d/%d" % (k, n)
                q["theta"] = out[-1]["theta"] + (s_["theta"] - out[-1]["theta"]) / (n - k + 1)
                q["p"] = out[-1]["p"] + (s_["p"] - out[-1]["p"]) / (n - k + 1)
                q["kind"] = s_["kind"] + "_sub"
                out.append(q)
        out.append(s_)
    return out


def ranges(ids):
    ids = sorted(set(int(i) for i in ids))
    out = []
    a = b = ids[0]
    for i in ids[1:]:
        if i == b + 1:
            b = i
        else:
            out.append((a, b))
            a = b = i
    out.append((a, b))
    return out


def set_card(sid, ids):
    parts = ["%d THRU %d" % (a, b) if b > a else "%d" % a for a, b in ranges(ids)]
    lines, cur = [], "SET %d = " % sid
    for k, p in enumerate(parts):
        add = p + ("," if k < len(parts) - 1 else "")
        if len(cur) + len(add) > 70:
            lines.append(cur)
            cur = "  "
        cur += add
    lines.append(cur)
    return lines


def write(mesh_pkl, out, run="R1", opt=2, plim=20, tissue="relaxed", padE=0.0965, seq="D-21", vref=False, calib=None,
          maxiter=25, nb_pad=6, title=None, extra_param=()):
    m = pickle.load(open(mesh_pkl, "rb"))
    X, EL, S, meta = m["X"], m["el"], m["S"], m["meta"]
    H = meta["H"]
    steps = sequence(opt, plim, seq, vref)
    sfac_skin = SFAC_SKIN if SFAC_SKIN is not None else SFAC_BY_TISSUE[tissue]
    if VENT:                                   # vented baseline run: same kinematics, p = 0 (passive knee moment M0(theta))
        for s_ in steps:
            s_["p"] = 0.0
    dT = {"thigh_far": -30.0, "thigh_near": -30.0, "shank_near": -30.0, "shank_far": -30.0}
    if calib:
        c = json.load(open(calib))
        dT.update(c.get(tissue, c))
    L = []
    w = L.append
    nid = lambda i: int(i) + 1            # node index -> GRID id
    eid = lambda i: int(i) + 1            # element index -> EID
    # ---------------------------------------------------------------- output sets
    ring_e = [e for r in S["rings"].values() for e in r["e"]]
    hook_e = [e for h in S["hooks"].values() for e in h["e"]]
    bl_e = S["bl_body"] + S["bl_cap"]
    cov_e = S["cov_body"] + S["cov_cap"] + S["cov_flange"]
    shells = ring_e + hook_e + bl_e + cov_e + S["tab_e"] + S["flap_e"]
    dev_nodes = set()
    for e in shells + S["pad_e"] + S["seat_e"] + S["stack_e"]:
        dev_nodes.update(EL[e][2])
    skin_nodes = set(n for fc, th, y in S["skin"] for n in fc)
    bore = S["bore_thigh"] + S["bore_shank"]
    w("SOL 106")
    w("CEND")
    w("TITLE = %s" % (title or "full asseymbly 07 %s opt%d %dkPa %s padE %g seq %s" % (run, opt, plim, tissue, padE, seq)))
    w("ECHO = NONE")
    L += set_card(1, [nid(n) for n in dev_nodes | skin_nodes])
    L += set_card(2, [nid(n) for n in bore])
    L += set_card(3, [eid(e) for e in shells + S["stack_e"]])
    L += set_card(4, [eid(e) for e in bl_e + cov_e])
    L += set_card(5, [eid(e) for e in ring_e + hook_e + cov_e])
    L += set_card(6, [nid(n) for n in S["bl_nodes"]])
    w("DISPLACEMENT(PRINT) = 1")
    w("SPCFORCES(PRINT) = 2")
    w("STRESS(PRINT) = 3")
    w("STRAIN(PRINT) = 4")
    w("FORCE(PRINT) = 5")
    w("ESE(PRINT) = 3")
    w("OLOAD(PRINT) = 6")
    w("TEMPERATURE(INITIAL) = 1")
    for k, s_ in enumerate(steps, start=1):
        w("SUBCASE %d" % k)
        w("  LABEL = %s th=%.2f p=%.2fkPa" % (s_["name"], s_["theta"], s_["p"]))
        w("  SPC = 1")
        w("  LOAD = %d" % (1000 + k))
        w("  NLPARM = %d" % k)
        w("  TEMPERATURE(LOAD) = %d" % (1 if not s_["therm"] else (2 if s_["therm"] is True or s_["therm"] >= 1.0 else 3)))
    w("BEGIN BULK")
    w("PARAM,UNITS,MM")
    w("PARAM,LGDISP,1")
    w("PARAM,AUTOSPC,YES")
    w("PARAM,GRDPNT,0")
    for kv in extra_param:
        w("PARAM,%s" % kv)
    for k, s_ in enumerate(steps, start=1):
        w("NLPARM,%d,%d,,ITER,1,%d,PW,NO\n,0.01,0.01,0.001\n,10" % (k, s_["ninc"], maxiter))
    # ---------------------------------------------------------------- materials / properties
    A10, D1 = TISSUE[tissue]
    w("$ tissue neo-Hookean (MATHP MID A10 A01 D1 RHO), %s" % tissue)
    w("MATHP,1,%s,0.,%s,1.e-9" % (f(A10), f(D1)))
    w("PSOLID,1,1,0")
    w("MAT1,2,%s,,0.33,%s" % (f(padE), f(203.9e-12)))
    w("PSOLID,2,2,0")
    w("$ rings: MAT8 orthotropic shell, thermal expansion along the hoop (element x) only")
    w("MAT8,3,498.,498.,0.35,184.4,184.4,184.4,%s\n,%s,0.,%s" % (f(576e-12), f(ALPHA_RING), f(TREF)))
    w("PSHELL,3,3,3.18,3,,3")
    rho_clo = (576.0 * 3.18 * 2 + 109.0 * 1.5) / 7.86
    w("MAT8,4,498.,498.,0.35,184.4,184.4,184.4,%s\n,%s,0.,%s" % (f(rho_clo * 1e-12), f(ALPHA_RING), f(TREF)))
    w("PSHELL,4,4,7.86,4,0.139,4")          # closure = 3 separate layers: bending 12I/t^3 = (2 x 3.18^3 + 1.5^3) / 7.86^3
    w("MAT1,5,2760.,,0.37,%s" % f(1410e-12))
    w("PSHELL,5,5,4.,5,,5")
    w("MAT1,6,498.,,0.35,%s" % f((576.0 * 3.18 + 109.0 * 1.5) / 4.68 * 1e-12))
    w("PSOLID,6,6,0")
    w("MAT1,7,7.2,,0.49,%s" % f(1120e-12))
    w("PSHELL,7,7,2.,7,,7")
    w("PSHELL,8,7,2.,7,,7")
    w("MAT1,9,498.,,0.35,%s" % f(1105e-12))
    w("PSHELL,9,9,0.43,9,,9")
    w("PSHELL,10,9,0.43,9,,9")
    # ---------------------------------------------------------------- grids / elements
    for i, x in enumerate(X):
        w("GRID,%d,,%s,%s,%s" % (i + 1, f(x[0]), f(x[1]), f(x[2])))
    for i, (typ, pid, n, grp) in enumerate(EL):
        g = [str(nid(v)) for v in n]
        if typ == "CHEXA":
            w("CHEXA,%d,%d,%s\n,%s" % (i + 1, pid, ",".join(g[:6]), ",".join(g[6:])))
        else:
            w("%s,%d,%d,%s" % (typ, i + 1, pid, ",".join(g)))
    # ---------------------------------------------------------------- constraints
    for grp in (S["bore_thigh"], S["bore_shank"]):
        ids = [nid(v) for v in grp]
        for c in range(0, len(ids), 6):
            w("SPC1,1,123,%s" % ",".join(map(str, ids[c:c + 6])))
    # ---------------------------------------------------------------- temperatures
    w("TEMPD,1,%s" % f(TREF))
    w("TEMPD,2,%s" % f(TREF))
    tset = {}
    for nm, r in S["rings"].items():
        for n in r["nodes"]:
            tset[nid(n)] = TREF + dT[nm]
    items = sorted(tset.items())
    w("TEMPD,3,%s" % f(TREF))
    for c in range(0, len(items), 3):
        w("TEMP,2,%s" % ",".join("%d,%s" % (g, f(t)) for g, t in items[c:c + 3]))
        w("TEMP,3,%s" % ",".join("%d,%s" % (g, f(TREF + 0.25 * (t - TREF))) for g, t in items[c:c + 3]))
    # ---------------------------------------------------------------- contacts
    def bsseg(sid, faces):
        g = [str(nid(n)) for fc in faces for n in (list(fc) + ([-1] if len(fc) == 3 else []))]
        g = ["0" if v == "0" else v for v in g]
        lines = ["BSSEG,%d,%s" % (sid, ",".join(g[:7]))]
        for c in range(7, len(g), 8):
            lines.append("," + ",".join(g[c:c + 8]))
        w("\n".join(lines))
    pairs = []
    skin = S["skin"]
    Xc = np.asarray(X)

    def cells(name, sl, ms, key, cy, cs, margin, mu, sfac):
        """split one contact into patches: slave faces binned on a (y, s) grid of cy x cs mm, master faces within the
        cell + margin.  The solver builds slave x master segment pairs per BSCONP, so patches keep the contact element
        count (and RAM) small; a slave face belongs to exactly one patch."""
        cy, cs = cy * CELL, cs * CELL
        sk = [key(Xc[fc].mean(0)) for fc in sl]
        mk = [key(Xc[fc].mean(0)) for fc in ms]
        bins = {}
        for fc, (y, s2) in zip(sl, sk):
            bins.setdefault((int(math.floor(y / cy)), int(math.floor(s2 / cs))), []).append(fc)
        for (iy, isx), faces in sorted(bins.items()):
            ya, yb, sa, sb = iy * cy - margin, (iy + 1) * cy + margin, isx * cs - margin, (isx + 1) * cs + margin
            mm = [fc for fc, (y, s2) in zip(ms, mk) if ya <= y <= yb and sa <= s2 <= sb]
            pairs.append(("%s_%d_%d" % (name, iy, isx), faces, mm, mu, sfac))

    CELL = max(0.6, min(1.0, meta["h"] / 5.0))       # patch size follows the device mesh size (contact elements ~ constant per patch)

    def skin_key(c):
        return (c[1], math.atan2(c[2], c[0]) * 75.0)
    skin_f = [fc for fc, th, y in skin]
    cells("pad_skin", [p[0] for p in S["pad_bottom"]], skin_f, skin_key, 25.0, 30.0, 8.0, MU_SKIN, sfac_skin)
    for nm, r in S["rings"].items():
        cells("ring_skin_" + nm, r["skin"], skin_f, skin_key, 30.0, 40.0, 8.0, MU_RING if MU_RING is not None else MU_SKIN, sfac_skin)
    YD = meta["YD"]

    def bl_key(c):
        u = c[0] - (meta_r(c[1]) + 9.18)
        return (c[1], math.atan2(c[2], u - 22.0) * 25.0)
    bl_f = [EL[e][2] for e in bl_e]
    cv_f = [EL[e][2] for e in S["cov_body"] + S["cov_cap"]]
    cv_f = [fc[::-1] for fc in cv_f]                        # master normals face the bladder (inward)
    cells("bladder_cover", bl_f, cv_f, bl_key, 20.0, 20.0, 6.0, 0.0, SFAC_DEV)
    # base slaves: bladder elements whose centroid lies in the lower 14 mm of the bladder section
    base_sl = [EL[e][2] for e in bl_e if Xc[EL[e][2]].mean(0)[0] - (meta_r(Xc[EL[e][2]].mean(0)[1]) + 9.18) < 14.0]
    cells("bladder_base", base_sl, [fc[::-1] for fc in S["base_master"]], lambda c: (c[1], c[2]), 25.0, 25.0, 6.0, 0.0, SFAC_DEV)
    pairs = [p for p in pairs if not any(p[0].startswith(k) for k in SKIP)]
    info_pairs = []
    for k, (nm, sl, ms, mu, sfac) in enumerate(pairs, start=1):
        if not sl or not ms:
            continue
        bsseg(100 + 2 * k, sl)
        bsseg(101 + 2 * k, ms)
        w("BSCONP,%d,%d,%d,%s,,%s,1" % (k, 100 + 2 * k, 101 + 2 * k, f(sfac), f(mu)))
        info_pairs.append((k, nm, len(sl), len(ms), mu, sfac))
    nce = sum(p[2] * p[3] for p in info_pairs)
    # ---------------------------------------------------------------- loads per subcase
    shank = S["bore_shank"]
    bl_ids = [eid(e) for e in bl_e]
    for k, s_ in enumerate(steps, start=1):
        sid = 1000 + k
        th = math.radians(s_["theta"])
        c, s = math.cos(th), math.sin(th)
        for n in shank:
            x = Xc[n] - H
            u = [c * x[0] - s * x[1] - x[0], s * x[0] + c * x[1] - x[1], 0.0]
            for d in range(3):
                w("SPCD,%d,%d,%d,%s" % (sid, nid(n), d + 1, f(u[d])))
        if s_["p"] > 0:
            for a, b in ranges(bl_ids):
                if b > a:
                    w("PLOAD4,%d,%d,%s,,,,THRU,%d" % (sid, a, f(s_["p"] / 1000.0), b))
                else:
                    w("PLOAD4,%d,%d,%s" % (sid, a, f(s_["p"] / 1000.0)))
    w("ENDDATA")
    open(out, "w").write("\n".join(L) + "\n")
    info = dict(run=run, opt=opt, plim=plim, tissue=tissue, padE=padE, seq=seq, steps=steps, dT=dT, H=H, mesh=os.path.abspath(out[:-4] + "_mesh.pkl"),
                pairs=info_pairs, alpha=ALPHA_RING, mu=MU_SKIN, mu_ring=(MU_RING if MU_RING is not None else MU_SKIN), sfac=sfac_skin)
    pickle.dump(info, open(out[:-4] + "_info.pkl", "wb"))
    import shutil
    shutil.copyfile(mesh_pkl, out[:-4] + "_mesh.pkl")          # the run keeps its own mesh (meshes are regenerated)
    with open(out[:-4] + "_steps.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["subcase", "name", "kind", "frame_pct", "time_ms", "theta_deg", "p_kPa", "ninc", "thermal"])
        for k, s_ in enumerate(steps, start=1):
            wr.writerow([k, s_["name"], s_["kind"], s_["frame"], s_["ms"], round(s_["theta"], 4), round(s_["p"], 4), s_["ninc"], s_["therm"]])
    print("%s: subcases %d grids %d elements %d contact pairs %d, slave x master segment products %d" % (
        os.path.basename(out), len(steps), len(X), len(EL), len(info_pairs), nce))


_GEO = None


def meta_r(y):
    global _GEO
    if _GEO is None:
        import sys
        gd = r"<PROJECT>\03_Mechanical_Design\Design_Reports\m1-m7\_cad_v8_scripts"
        a0 = sys.argv
        sys.argv = ["geo8.py", "A150"]
        sys.path.insert(0, gd)
        import geo8
        sys.argv = a0
        _GEO = geo8
    return _GEO.r(y)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run", default="R1")
    ap.add_argument("--opt", type=int, default=2)
    ap.add_argument("--plim", type=int, default=20)
    ap.add_argument("--tissue", default="relaxed")
    ap.add_argument("--padE", type=float, default=0.0965)
    ap.add_argument("--seq", default="D-21")
    ap.add_argument("--vref", action="store_true")
    ap.add_argument("--calib", default=None)
    ap.add_argument("--maxiter", type=int, default=25)
    ap.add_argument("--param", action="append", default=[])
    ap.add_argument("--sfac", type=float, default=None)
    ap.add_argument("--mu", type=float, default=None)
    ap.add_argument("--nincD", type=int, default=None)
    ap.add_argument("--skip", default="")
    ap.add_argument("--vent", action="store_true")
    ap.add_argument("--mu_ring", type=float, default=None)
    a = ap.parse_args()
    if a.sfac is not None:
        SFAC_SKIN = a.sfac
    if a.mu is not None:
        MU_SKIN = a.mu
    SKIP = [k for k in a.skip.split(",") if k]
    MU_RING = a.mu_ring
    VENT = a.vent
    if a.nincD is not None:
        NINC_D = a.nincD
    write(a.mesh, a.out, a.run, a.opt, a.plim, a.tissue, a.padE, a.seq, a.vref, a.calib, a.maxiter, extra_param=a.param)
