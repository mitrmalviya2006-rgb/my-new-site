#!/usr/bin/env python3
"""
Minimal truss motorcycle chassis generator (prototype).

x = forward, y = left, z = up, origin = swingarm pivot centre, units mm.
The engine is the real 349 cc single from ../engine-design. This script reads its
interface.json (clearance boxes, mount points, mass, centre of gravity), places the
crank axis at ENGINE_ORIGIN and hangs it from nodes E (front-upper) and F (rear-upper).
Change ENGINE_ORIGIN or MOUNT_Y below and rerun; rigidity, forces and clearance are re-checked.

Run:  python frame.py          (needs numpy, cadquery, ezdxf; run engine-design/build.py first)
Out:  frame.step frame.dxf cutlist.csv results.json preview_data.json
"""
import csv
import itertools
import json
import math
import os
import sys

import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ parameters
G = 9.81
E_MOD = 210e3          # N/mm2
YIELD = 250.0          # N/mm2 (mild steel ERW, conservative)
SF_MIN = 2.0
TUBES = {              # key: (OD, wall) mm
    "S": (19.0, 1.6),  # secondary
    "M": (28.0, 2.0),  # main
    "H": (50.0, 3.0),  # steering head tube
}
RHO = 7.85e-6          # kg/mm3
CLEAR = 10.0           # mm gap between tube surface and engine clearance boxes

# ---- real engine (from ../engine-design/interface.json)
ENGINE_DIR = os.path.join(os.path.dirname(OUT), "engine-design")
ENGINE_ORIGIN = np.array([300.0, 0.0, -20.0])   # crank axis in the vehicle frame (same height as the wheel axles)
MOUNT_Y = 152.0        # |y| of engine-mount nodes E and F: outside the alternator bulge (|y| 126) with tube clearance
ENGINE_EXTRA_KG = 9.0  # exhaust, radiator + hoses, ECU, wiring: hangs on the engine, not designed here
DRIVETRAIN_KG = 20.0   # allowance for the future clutch + gearbox/CVT behind the engine (not designed)
SPACER_OD, SPACER_ID = 24.0, 13.0   # mount spacer between engine ear and frame plate (M12 bolt)
EAR_OUTER_Y = 82.0     # |y| of the outer face of the engine mount ears


def load_engine():
    path = os.path.join(ENGINE_DIR, "interface.json")
    if not os.path.exists(path):
        raise SystemExit("missing %s: run engine-design/build.py first" % path)
    with open(path) as fh:
        d = json.load(fh)
    boxes = {}
    for name, b in d["boxes"].items():
        boxes[name] = {ax: (b[ax][0] + ENGINE_ORIGIN[i], b[ax][1] + ENGINE_ORIGIN[i]) for i, ax in enumerate("xyz")}
    env = {ax: (min(b[ax][0] for b in boxes.values()), max(b[ax][1] for b in boxes.values())) for ax in "xyz"}
    return d, boxes, env


ENGINE_IF, ENGINE_BOXES, ENGINE = load_engine()      # ENGINE = overall envelope of all boxes
_MP = ENGINE_IF["mounts"]
E_XZ = (ENGINE_ORIGIN[0] + _MP["upper"]["x"], ENGINE_ORIGIN[2] + _MP["upper"]["z"])   # front-upper mount
F_XZ = (ENGINE_ORIGIN[0] + _MP["rear"]["x"], ENGINE_ORIGIN[2] + _MP["rear"]["z"])     # rear-upper mount
ENGINE_CG = ENGINE_ORIGIN + np.array(ENGINE_IF["cg"])
ENGINE_KG = ENGINE_IF["mass_wet_kg"] + ENGINE_EXTRA_KG
_fE = (ENGINE_CG[0] - F_XZ[0]) / (E_XZ[0] - F_XZ[0])      # share of the engine weight carried by the front mounts
M_E = ENGINE_KG * _fE / 2                                  # kg on each E node
M_F = ENGINE_KG * (1 - _fE) / 2 + DRIVETRAIN_KG / 2        # kg on each F node (drivetrain allowance sits behind the engine)

WHEEL_R = 300.0
FRONT_AXLE = np.array([840.0, 0.0, -20.0])
REAR_AXLE = np.array([-560.0, 0.0, -20.0])
FRONT_CONTACT = np.array([840.0, 0.0, -320.0])
SHOCK_LOWER = np.array([-300.0, 0.0, 0.0])
RAKE = math.radians(25.0)
STEER_AXIS = np.array([-math.sin(RAKE), 0.0, math.cos(RAKE)])  # up and back

# rider / bike layout targets (170-180 cm rider, neutral ergonomic)
HIP = (-60.0, 0.0, 540.0)
PEG = (300.0, 0.0, 10.0)
GRIP = (520.0, 0.0, 680.0)


def build_nodes():
    N = {
        "HT": (598.0, 0.0, 427.0),
        "HB": (658.0, 0.0, 300.0),
        "M": (-20.0, 0.0, 400.0),
    }
    for s, sfx in ((1, "L"), (-1, "R")):
        N["C" + sfx] = (-120.0, s * 130.0, 430.0)   # seat rear
        N["S" + sfx] = (150.0, s * 130.0, 430.0)    # seat front / tank
        N["D" + sfx] = (0.0, s * 160.0, 0.0)        # swingarm pivot
        N["E" + sfx] = (E_XZ[0], s * MOUNT_Y, E_XZ[1])    # engine front-upper mount (hole axis along y)
        N["F" + sfx] = (F_XZ[0], s * MOUNT_Y, F_XZ[1])    # engine rear-upper mount (hole axis along y)
        N["P" + sfx] = (300.0, s * 235.0, 10.0)     # footpeg
    return {k: np.array(v) for k, v in N.items()}


CENTRE = ("HT", "HB", "M")      # nodes on the centreline (no L/R suffix)


def base_members():
    """The 39 bars (= 3j-6 for 15 joints, isostatic) found for the real engine position.

    With the engine hung from E and F, no tube may cross the head (E-E, F-F and the S-E cross diagonals of the
    placeholder layout all cut through it, and E-D would pass 8 mm from node F). An annealing search over every
    allowed bar (clear of the engine boxes and of the airbox zone, no crossings, mirror-symmetric) with the real
    load cases converged on this set from four different random starts (see SPEC.md section 3).
    """
    m = [("HT", "HB"), ("DL", "DR"), ("CL", "CR")]
    per_side = [("HT", "S"), ("S", "C"),                 # top rail: head tube - tank/seat front - seat rear
                ("S", "E"), ("S", "F"),                  # two hangers carry the engine from the top rail
                ("HT", "E"), ("HB", "E"),                # fork-side down tubes to the front engine mount
                ("E", "F"),                              # ties the two engine mounts together
                ("F", "D"), ("C", "D"),                  # to the swingarm pivot
                ("M", "C"), ("M", "D"), ("M", "S"), ("M", "F"),   # shock top node braced four ways
                ("E", "P"), ("F", "P"), ("D", "P"), ("S", "P"), ("C", "P")]   # footpeg node braced five ways
    for sfx in "LR":
        for a, b in per_side:
            m.append(tuple(n if n in CENTRE else n + sfx for n in (a, b)))
    return m


# --------------------------------------------------------------- geometry utils
def seg_box_dist(p, q, box, n=400):
    """Smallest distance from segment p-q to an axis-aligned box (0 if it enters the box)."""
    lo = np.array([box["x"][0], box["y"][0], box["z"][0]])
    hi = np.array([box["x"][1], box["y"][1], box["z"][1]])
    t = np.linspace(0.0, 1.0, n)[:, None]
    pts = p[None, :] + (q - p)[None, :] * t
    d = np.maximum(np.maximum(lo[None, :] - pts, pts - hi[None, :]), 0.0)
    return float(np.linalg.norm(d, axis=1).min())


def seg_engine_dist(p, q):
    """Smallest distance from segment p-q to any of the engine clearance boxes."""
    return min(seg_box_dist(p, q, b) for b in ENGINE_BOXES.values())


# volume above the engine kept free of tubes for the airbox, injector, ECU and wiring (not designed here)
KEEP_OUT = {"airbox": {"x": (100.0, 440.0), "y": (-100.0, 100.0), "z": (275.0, 400.0)}}


def seg_seg_dist(p1, q1, p2, q2):
    """Smallest distance between two segments (Ericson, Real-Time Collision Detection)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = float(d1 @ d1), float(d2 @ d2), float(d2 @ r)
    c, b = float(d1 @ r), float(d1 @ d2)
    clamp = lambda x: min(1.0, max(0.0, x))
    den = a * e - b * b
    s = clamp((b * f - c * e) / den) if den > 1e-12 else 0.0
    t = (b * s + f) / e
    if t < 0.0:
        t, s = 0.0, clamp(-c / a)
    elif t > 1.0:
        t, s = 1.0, clamp((b - c) / a)
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t)))


def rigidity_rank(names, pos, edges):
    idx = {n: i for i, n in enumerate(names)}
    R = np.zeros((len(edges), 3 * len(names)))
    for k, (a, b) in enumerate(edges):
        d = pos[a] - pos[b]
        R[k, 3 * idx[a]:3 * idx[a] + 3] = d
        R[k, 3 * idx[b]:3 * idx[b] + 3] = -d
    return int(np.linalg.matrix_rank(R, tol=1e-6 * 800))


def fix_topology(names, pos, edges):
    """Add the fewest/shortest extra members needed for infinitesimal rigidity (rank = 3j-6)."""
    need = 3 * len(names) - 6
    rank = rigidity_rank(names, pos, edges)
    added = []
    have = {frozenset(e) for e in edges}
    r_clear = TUBES["M"][0] / 2 + CLEAR
    cands = []
    for a, b in itertools.combinations(names, 2):
        if frozenset((a, b)) in have:
            continue
        L = np.linalg.norm(pos[a] - pos[b])
        if not (150 <= L <= 800):
            continue
        if seg_engine_dist(pos[a], pos[b]) < r_clear:
            continue
        cands.append((L, a, b))
    cands.sort()

    def mirror(n):
        return n[:-1] + ("R" if n.endswith("L") else "L") if n.endswith(("L", "R")) else n

    while rank < need:
        hit = None
        for L, a, b in cands:
            if frozenset((a, b)) in have:
                continue
            pair = [(a, b)]
            ma, mb = mirror(a), mirror(b)
            if frozenset((ma, mb)) != frozenset((a, b)) and frozenset((ma, mb)) not in have:
                pair.append((ma, mb))
            r2 = rigidity_rank(names, pos, edges + added + pair)
            if r2 > rank:
                hit = (pair, r2)
                break
        if hit is None:
            raise RuntimeError("cannot reach rigidity; rank %d of %d" % (rank, need))
        for e in hit[0]:
            added.append(e)
            have.add(frozenset(e))
        rank = hit[1]
    return added, rank, need


# ------------------------------------------------------------------- loads
def masses(pos, members, sizes):
    m = {n: 0.0 for n in pos}
    for (a, b) in members:
        od, w = TUBES[sizes[(a, b)]]
        area = math.pi / 4 * (od ** 2 - (od - 2 * w) ** 2)
        mm = RHO * area * np.linalg.norm(pos[a] - pos[b])
        m[a] += mm / 2
        m[b] += mm / 2
    pts = {  # component masses in kg
        "EL": M_E, "ER": M_E, "FL": M_F, "FR": M_F,             # real engine + extras + drivetrain allowance
        "CL": 17.5 + 15, "CR": 17.5 + 15,                         # rider rear + misc
        "SL": 15 + 5, "SR": 15 + 5,                               # rider front + tank
        "PL": 12.5, "PR": 12.5,                                   # legs on pegs
        "HT": 10,                                                 # tank / fuel / instruments
    }
    for k, v in pts.items():
        m[k] += v
    return m


def front_to_head(F, pos):
    """Resolve a force at the front contact patch into forces on HT and HB bearings."""
    u = STEER_AXIS
    e1 = np.array([0.0, 1.0, 0.0])
    e2 = np.cross(u, e1)
    HT, HB = pos["HT"], pos["HB"]
    # unknowns: a1,a2 (HT perp), b1,b2 (HB perp), b3 (HB axial)
    A = np.zeros((5, 5))
    rhs = np.zeros(5)
    cols = [e1, e2, e1, e2, u]      # direction of each unknown (first two at HT, rest at HB)
    for j, d in enumerate(cols):
        A[0:3, j] = d
    L = HT - HB
    for j in range(2):
        mom = np.cross(L, cols[j])
        A[3, j] = mom @ e1
        A[4, j] = mom @ e2
    rhs[0:3] = F
    mom = np.cross(FRONT_CONTACT - HB, F)
    rhs[3] = mom @ e1
    rhs[4] = mom @ e2
    x = np.linalg.solve(A, rhs)
    return x[0] * e1 + x[1] * e2, x[2] * e1 + x[3] * e2 + x[4] * u


def case_loads(pos, mass, gfac, ax_g):
    """Nodal loads (N) for a self-equilibrated case. gfac = vertical g multiplier, ax_g = braking g."""
    f = {n: np.zeros(3) for n in pos}
    for n, m in mass.items():
        f[n] += np.array([m * ax_g * G, 0.0, -m * gfac * G])
    tot = sum(f.values())
    # moments about y of the nodal loads
    My = sum(pos[n][2] * f[n][0] - pos[n][0] * f[n][2] for n in f)
    Fx_f = -tot[0]
    # R_f, R_r from  sum Fz = 0, sum My = 0
    A = np.array([[1.0, 1.0],
                  [-FRONT_CONTACT[0], -REAR_AXLE[0]]])
    b = np.array([-tot[2],
                  -(My + FRONT_CONTACT[2] * Fx_f)])
    R_f, R_r = np.linalg.solve(A, b)
    road_f = np.array([Fx_f, 0.0, R_f])
    fht, fhb = front_to_head(road_f, pos)
    f["HT"] += fht
    f["HB"] += fhb
    # rear: wheel reaction R_r -> shock + pivot
    Mpos = np.array([pos["M"][0], pos["M"][2]])
    Q = np.array([SHOCK_LOWER[0], SHOCK_LOWER[2]])
    us = (Mpos - Q) / np.linalg.norm(Mpos - Q)

    def my(r, fvec):
        return r[1] * fvec[0] - r[0] * fvec[1]
    wheel = np.array([0.0, R_r])
    Mw = my(np.array([REAR_AXLE[0], REAR_AXLE[2]]), wheel)
    Ms = my(Q, -us)
    Fs = -Mw / Ms
    shock_on_frame = Fs * us
    pivot_on_frame = wheel + (-Fs * us)
    f["M"] += np.array([shock_on_frame[0], 0.0, shock_on_frame[1]])
    for sfx in "LR":
        f["D" + sfx] += 0.5 * np.array([pivot_on_frame[0], 0.0, pivot_on_frame[1]])
    info = {"R_front_N": float(R_f), "R_rear_N": float(R_r), "Fx_front_N": float(Fx_f),
            "shock_axial_N": float(Fs), "total_mass_kg": sum(mass.values())}
    return f, info


# --------------------------------------------------------------- truss solve
def solve_truss(names, pos, members, sizes, loads):
    idx = {n: i for i, n in enumerate(names)}
    nd = 3 * len(names)
    K = np.zeros((nd, nd))
    geo = []
    for (a, b) in members:
        od, w = TUBES[sizes[(a, b)]]
        A = math.pi / 4 * (od ** 2 - (od - 2 * w) ** 2)
        d = pos[b] - pos[a]
        L = np.linalg.norm(d)
        c = d / L
        k = E_MOD * A / L
        kk = k * np.outer(c, c)
        ia, ib = 3 * idx[a], 3 * idx[b]
        K[ia:ia + 3, ia:ia + 3] += kk
        K[ib:ib + 3, ib:ib + 3] += kk
        K[ia:ia + 3, ib:ib + 3] -= kk
        K[ib:ib + 3, ia:ia + 3] -= kk
        geo.append((c, L, A, od, w))
    fixed = []
    for dof in range(3):
        fixed.append(3 * idx["DL"] + dof)
    fixed += [3 * idx["DR"] + 0, 3 * idx["DR"] + 2, 3 * idx["HB"] + 2]
    free = [i for i in range(nd) if i not in fixed]
    Kff = K[np.ix_(free, free)]
    ev = np.linalg.eigvalsh(Kff)
    out = {"min_eig": float(ev.min())}
    res = {}
    for cname, f in loads.items():
        F = np.zeros(nd)
        for n, v in f.items():
            F[3 * idx[n]:3 * idx[n] + 3] = v
        u = np.zeros(nd)
        u[free] = np.linalg.solve(Kff, F[free])
        react = K @ u - F
        forces = []
        for (a, b), (c, L, A, od, w) in zip(members, geo):
            du = u[3 * idx[b]:3 * idx[b] + 3] - u[3 * idx[a]:3 * idx[a] + 3]
            forces.append(float(E_MOD * A / L * (du @ c)))
        res[cname] = {"forces": forces, "react_max": float(np.abs(react[fixed]).max()),
                      "u_max": float(np.abs(u).max())}
    out["cases"] = res
    out["geo"] = geo
    return out


def euler_pcr(od, w, L):
    I = math.pi / 64 * (od ** 4 - (od - 2 * w) ** 4)
    return math.pi ** 2 * E_MOD * I / L ** 2


def size_members(names, pos, members, mass_fn):
    sizes = {m: "S" for m in members}
    sizes[("HT", "HB")] = "H"
    sizes[("DL", "DR")] = "M"   # pivot tube: always the big one
    for it in range(8):
        mass = mass_fn(sizes)
        loads = {}
        info = {}
        for cname, (g, ax) in {"static": (1.0, 0.0), "bump_3g": (3.0, 0.0), "brake_1g": (1.0, 1.0)}.items():
            loads[cname], info[cname] = case_loads(pos, mass, g, ax)
        sol = solve_truss(names, pos, members, sizes, loads)
        changed = False
        for k, m in enumerate(members):
            if sizes[m] in ("H",):
                continue
            ok = {}
            for key in ("S", "M"):
                od, w = TUBES[key]
                A = math.pi / 4 * (od ** 2 - (od - 2 * w) ** 2)
                L = sol["geo"][k][1]
                good = True
                for cname in loads:
                    N = sol["cases"][cname]["forces"][k]
                    if abs(N) / A * SF_MIN > YIELD:
                        good = False
                    if N < 0 and abs(N) * SF_MIN > euler_pcr(od, w, L):
                        good = False
                ok[key] = good
            want = "S" if ok["S"] else "M"
            if sizes[m] == "M" and want == "S" and m == ("DL", "DR"):
                want = "M"
            if want != sizes[m] and not (sizes[m] == "M" and m == ("DL", "DR")):
                sizes[m] = want
                changed = True
        if not changed:
            break
    return sizes, loads, info, sol


# --------------------------------------------------------------- reporting
def member_table(names, pos, members, sizes, sol, loads):
    rows = []
    for k, (a, b) in enumerate(members):
        od, w = TUBES[sizes[(a, b)]]
        A = math.pi / 4 * (od ** 2 - (od - 2 * w) ** 2)
        L = sol["geo"][k][1]
        forces = {c: sol["cases"][c]["forces"][k] for c in loads}
        worst_t = max(forces.values())
        worst_c = min(forces.values())
        sf_y = YIELD / (max(abs(worst_t), abs(worst_c)) / A) if max(abs(worst_t), abs(worst_c)) > 1e-6 else float("inf")
        sf_b = (euler_pcr(od, w, L) / abs(worst_c)) if worst_c < -1e-6 else float("inf")
        rows.append({"id": "%s-%s" % (a, b), "a": a, "b": b, "size": sizes[(a, b)], "od": od, "wall": w,
                     "length": L, "forces": forces, "sf_yield": sf_y, "sf_buckle": sf_b})
    return rows


def cut_list(pos, rows):
    """Cut length = pierce point to pierce point on the mating tube; angle = included angle there."""
    at = {}
    for r in rows:
        at.setdefault(r["a"], []).append(r)
        at.setdefault(r["b"], []).append(r)
    out = []
    for r in rows:
        ends = []
        for node, other in ((r["a"], r["b"]), (r["b"], r["a"])):
            mine = pos[other] - pos[node]
            mine /= np.linalg.norm(mine)
            best = None
            for o in at[node]:
                if o is r:
                    continue
                on = o["b"] if o["a"] == node else o["a"]
                v = pos[on] - pos[node]
                v /= np.linalg.norm(v)
                ang = math.degrees(math.acos(max(-1, min(1, float(mine @ v)))))
                if best is None or (o["od"], -abs(ang - 90)) > (best[0], best[1]):
                    best = (o["od"], -abs(ang - 90), ang, o["id"])
            ends.append(best)
        cut = r["length"]
        for e in ends:
            if e and e[0] >= r["od"]:   # a tube is only coped onto an equal or larger tube
                rad = e[0] / 2
                cut -= rad / max(math.sin(math.radians(e[2])), 0.2)
        out.append({"id": r["id"], "size": "%gx%g" % (r["od"], r["wall"]), "centre_len": r["length"],
                    "cut_len": cut, "end_a_angle": ends[0][2] if ends[0] else "", "end_a_onto": ends[0][3] if ends[0] else "",
                    "end_b_angle": ends[1][2] if ends[1] else "", "end_b_onto": ends[1][3] if ends[1] else ""})
    return out


# ------------------------------------------------------------------ exports
def export_all(names, pos, rows, cuts, results):
    import cadquery as cq
    import ezdxf

    # ---- CSV
    with open(os.path.join(OUT, "cutlist.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "tube_ODxwall_mm", "centreline_length_mm", "cut_length_mm(axis pierce to pierce)",
                    "end_a_angle_deg", "end_a_coped_onto", "end_b_angle_deg", "end_b_coped_onto"])
        for c in cuts:
            w.writerow([c["id"], c["size"], "%.1f" % c["centre_len"], "%.1f" % c["cut_len"],
                        "%.1f" % c["end_a_angle"] if c["end_a_angle"] != "" else "", c["end_a_onto"],
                        "%.1f" % c["end_b_angle"] if c["end_b_angle"] != "" else "", c["end_b_onto"]])

    # ---- plates (flat patterns)
    PL = {"LUG": (70, 90, 6, 13), "PIVOT": (110, 150, 6, 20), "PEG": (50, 60, 6, 10), "SHOCK": (60, 80, 6, 12)}
    plate_at = []
    for sfx in "LR":
        s = 1 if sfx == "L" else -1
        for n in ("E", "F"):
            plate_at.append(("LUG", n + sfx, s))
        plate_at.append(("PIVOT", "D" + sfx, s))
        plate_at.append(("PEG", "P" + sfx, s))
    plate_at.append(("SHOCK", "M", 0))

    def plate_solid(kind, p, s):
        wd, ht, t, hole = PL[kind]
        y = p[1] - s * (TUBES["M"][0] / 2 + t / 2 + 1) if s else p[1]
        box = cq.Solid.makeBox(wd, t, ht, cq.Vector(p[0] - wd / 2, y - t / 2, p[2] - ht / 2))
        cyl = cq.Solid.makeCylinder(hole / 2, t + 2, cq.Vector(p[0], y - t / 2 - 1, p[2]), cq.Vector(0, 1, 0))
        return box.cut(cyl)

    # ---- STEP
    assy = cq.Assembly(name="truss_chassis")
    for r in rows:
        p, q = pos[r["a"]], pos[r["b"]]
        v = q - p
        L = np.linalg.norm(v)
        d = cq.Vector(*(v / L))
        outer = cq.Solid.makeCylinder(r["od"] / 2, L, cq.Vector(*p), d)
        inner = cq.Solid.makeCylinder(r["od"] / 2 - r["wall"], L, cq.Vector(*p), d)
        col = cq.Color(0.55, 0.57, 0.62, 1) if r["size"] != "H" else cq.Color(0.3, 0.3, 0.35, 1)
        assy.add(outer.cut(inner), name=r["id"], color=col)
    for kind, n, s in plate_at:
        assy.add(plate_solid(kind, pos[n], s), name="PLATE_%s_%s" % (kind, n), color=cq.Color(0.9, 0.55, 0.1, 1))
    # mount spacers: M12 bolt runs engine ear -> spacer -> frame lug plate -> nut (spacer length = gap between them)
    t_lug = PL["LUG"][2]
    for sfx in "LR":
        s = 1 if sfx == "L" else -1
        for n in ("E", "F"):
            p = pos[n + sfx]
            y_in = abs(p[1]) - (TUBES["M"][0] / 2 + t_lug / 2 + 1) - t_lug / 2       # inner face of the lug plate
            sp = cq.Solid.makeCylinder(SPACER_OD / 2, y_in - EAR_OUTER_Y, cq.Vector(p[0], s * EAR_OUTER_Y, p[2]), cq.Vector(0, s, 0))
            hole = cq.Solid.makeCylinder(SPACER_ID / 2, y_in - EAR_OUTER_Y + 2, cq.Vector(p[0], s * (EAR_OUTER_Y - 1), p[2]), cq.Vector(0, s, 0))
            assy.add(sp.cut(hole), name="SPACER_%s%s" % (n, sfx), color=cq.Color(0.9, 0.55, 0.1, 1))
    # the real engine goes here (import ../engine-design/engine.step and move it by ENGINE_ORIGIN); the clearance
    # boxes below are what the frame was checked against
    for bname, b in ENGINE_BOXES.items():
        assy.add(cq.Solid.makeBox(b["x"][1] - b["x"][0], b["y"][1] - b["y"][0], b["z"][1] - b["z"][0],
                                  cq.Vector(b["x"][0], b["y"][0], b["z"][0])),
                 name="ENGINE_BOX_%s" % bname, color=cq.Color(0.2, 0.5, 0.9, 0.35))
    assy.save(os.path.join(OUT, "frame.step"))

    # ---- DXF
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    for lay, col in (("SIDE", 7), ("TOP", 3), ("FRONT", 5), ("ENGINE", 4), ("PLATES", 1), ("TEXT", 8)):
        doc.layers.add(lay, color=col)
    msp = doc.modelspace()
    views = {"SIDE": (lambda p: (p[0], p[2]), (0, 0)),
             "TOP": (lambda p: (p[0], p[1]), (0, -1000)),
             "FRONT": (lambda p: (p[1], p[2]), (1700, 0))}
    for lay, (proj, off) in views.items():
        for r in rows:
            a = proj(pos[r["a"]])
            b = proj(pos[r["b"]])
            msp.add_line((a[0] + off[0], a[1] + off[1]), (b[0] + off[0], b[1] + off[1]), dxfattribs={"layer": lay})
        for n, p in pos.items():
            q = proj(p)
            msp.add_circle((q[0] + off[0], q[1] + off[1]), 6, dxfattribs={"layer": lay})
        # engine clearance boxes (outline of each box in this view)
        for b in ENGINE_BOXES.values():
            lo = proj((b["x"][0], b["y"][0], b["z"][0]))
            hi = proj((b["x"][1], b["y"][1], b["z"][1]))
            x0, x1 = sorted((lo[0], hi[0]))
            y0, y1 = sorted((lo[1], hi[1]))
            msp.add_lwpolyline([(x0 + off[0], y0 + off[1]), (x1 + off[0], y0 + off[1]),
                                (x1 + off[0], y1 + off[1]), (x0 + off[0], y1 + off[1])], close=True,
                               dxfattribs={"layer": "ENGINE"})
        msp.add_text("%s VIEW (engine = clearance boxes of the 349 cc design, crank axis at x%g y%g z%g)"
                     % (lay, ENGINE_ORIGIN[0], ENGINE_ORIGIN[1], ENGINE_ORIGIN[2]), height=25,
                     dxfattribs={"layer": "TEXT", "insert": (off[0], off[1] - 400 if lay == "SIDE" else off[1] + 320)})
    # wheels in side view for reference
    for ax in (FRONT_AXLE, REAR_AXLE):
        msp.add_circle((ax[0], ax[2]), WHEEL_R, dxfattribs={"layer": "TEXT"})
    # flat patterns
    ox = 0
    counts = {}
    for kind, n, s in plate_at:
        counts[kind] = counts.get(kind, 0) + 1
    for kind, (wd, ht, t, hole) in PL.items():
        msp.add_lwpolyline([(ox, -1800), (ox + wd, -1800), (ox + wd, -1800 + ht), (ox, -1800 + ht)], close=True,
                           dxfattribs={"layer": "PLATES"})
        msp.add_circle((ox + wd / 2, -1800 + ht / 2), hole / 2, dxfattribs={"layer": "PLATES"})
        msp.add_text("%s  %gx%gx%g mm, hole d%g, qty %d" % (kind, wd, ht, t, hole, counts[kind]), height=12,
                     dxfattribs={"layer": "TEXT", "insert": (ox, -1800 - 30)})
        ox += wd + 80
    doc.saveas(os.path.join(OUT, "frame.dxf"))

    # ---- preview data
    pdata = {
        "nodes": {n: [float(x) for x in p] for n, p in pos.items()},
        "members": [{"id": r["id"], "a": r["a"], "b": r["b"], "size": r["size"], "od": r["od"], "wall": r["wall"],
                     "len": round(r["length"], 1), "forces": {k: round(v, 1) for k, v in r["forces"].items()},
                     "sf_yield": None if math.isinf(r["sf_yield"]) else round(r["sf_yield"], 2),
                     "sf_buckle": None if math.isinf(r["sf_buckle"]) else round(r["sf_buckle"], 2)} for r in rows],
        "engine": {"origin": [float(x) for x in ENGINE_ORIGIN],
                   "envelope": {k: [float(v[0]), float(v[1])] for k, v in ENGINE.items()},
                   "boxes": {n: {k: [float(v[0]), float(v[1])] for k, v in b.items()} for n, b in ENGINE_BOXES.items()},
                   "mounts": {"E": [float(E_XZ[0]), float(E_XZ[1])], "F": [float(F_XZ[0]), float(F_XZ[1])],
                              "ear_outer_y": EAR_OUTER_Y, "mount_y": MOUNT_Y},
                   "airbox": {k: list(v) for k, v in KEEP_OUT["airbox"].items()}},
        "front_axle": FRONT_AXLE.tolist(), "rear_axle": REAR_AXLE.tolist(), "wheel_r": WHEEL_R,
        "hip": HIP, "peg": PEG, "grip": GRIP, "shock_lower": SHOCK_LOWER.tolist(),
        "ground_z": float(FRONT_CONTACT[2]),
        "summary": results["summary"],
    }
    with open(os.path.join(OUT, "preview_data.json"), "w") as fh:
        json.dump(pdata, fh)


def prune_central(names, pos, members, need):
    """Drop redundant central cross members (keep pivot tube DL-DR) -> isostatic, choose the stiffest set."""
    red = len(members) - need
    if red <= 0:
        return members, None
    central = [m for m in [("CL", "CR"), ("SL", "SR"), ("EL", "ER"), ("FL", "FR")] if m in members]
    if red > len(central):
        return members, None
    best = None
    for combo in itertools.combinations(central, red):
        rest = [m for m in members if m not in combo]
        if rigidity_rank(names, pos, rest) != need:
            continue
        sizes, loads, info, sol = size_members(names, pos, rest, lambda sz, rest=rest: masses(pos, rest, sz))
        score = sum(sol["cases"][c]["u_max"] for c in loads)
        n_m = sum(1 for v in sizes.values() if v == "M")
        score += 0.5 * n_m
        if best is None or score < best[0]:
            best = (score, rest, combo)
    if best is None:
        return members, None
    return best[1], best[2]


def main():
    pos = build_nodes()
    names = list(pos.keys())
    base = base_members()
    # base members that would cut through (or come within tube radius + CLEAR of) the real engine are dropped;
    # fix_topology then adds alternatives that keep clear of the engine
    r_clear = TUBES["M"][0] / 2 + CLEAR
    blocked = [(a, b, seg_engine_dist(pos[a], pos[b])) for a, b in base]
    blocked = [(a, b, d) for a, b, d in blocked if d < r_clear]
    gone = {(a, b) for a, b, _ in blocked}
    members = [m for m in base if m not in gone]
    print("base members removed (too close to the engine):", [(a, b, round(d, 1)) for a, b, d in blocked])
    added, rank, need = fix_topology(names, pos, members)
    members = members + added
    members, dropped = prune_central(names, pos, members, need)
    print("dropped redundant cross members:", dropped)
    print("nodes %d  members %d  rank %d  (isostatic needs 3j-6 = %d)  extra added: %s"
          % (len(names), len(members), rank, need, added))

    def mass_fn(sizes):
        return masses(pos, members, sizes)

    sizes, loads, info, sol = size_members(names, pos, members, mass_fn)
    rows = member_table(names, pos, members, sizes, sol, loads)
    cuts = cut_list(pos, rows)

    total_len = {k: sum(r["length"] for r in rows if r["size"] == k) for k in TUBES}
    mass_tube = sum(r["length"] * math.pi / 4 * (r["od"] ** 2 - (r["od"] - 2 * r["wall"]) ** 2) * RHO for r in rows)
    fails = [r for r in rows if r["sf_yield"] < SF_MIN or r["sf_buckle"] < SF_MIN]
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    zs = [p[2] for p in pos.values()]
    # clearance to engine for final members (tube surface to nearest clearance box)
    gaps = {r["id"]: seg_engine_dist(pos[r["a"]], pos[r["b"]]) - r["od"] / 2 for r in rows}
    clr = min(gaps.values())
    bad = [(k, round(v, 1)) for k, v in gaps.items() if v < CLEAR - 1e-6]
    if bad:
        print("ENGINE CLEARANCE VIOLATIONS (final members):", bad)
    # tube-to-tube clearance between members that do not share a node (a crossing would be a hidden joint)
    mgap = []
    for r1, r2 in itertools.combinations(rows, 2):
        if {r1["a"], r1["b"]} & {r2["a"], r2["b"]}:
            continue
        d = seg_seg_dist(pos[r1["a"]], pos[r1["b"]], pos[r2["a"]], pos[r2["b"]]) - (r1["od"] + r2["od"]) / 2
        mgap.append((round(d, 1), r1["id"], r2["id"]))
    mgap.sort()
    air_gap = min(seg_box_dist(pos[r["a"]], pos[r["b"]], KEEP_OUT["airbox"]) - r["od"] / 2 for r in rows)
    if mgap and mgap[0][0] < 3.0:
        bad.append(("tube-to-tube", mgap[0]))
        print("TUBES TOO CLOSE / CROSSING:", mgap[:3])
    if air_gap < 5.0:
        bad.append(("airbox", round(air_gap, 1)))
        print("TUBE INSIDE AIRBOX ZONE: gap %.1f" % air_gap)
    summary = {
        "nodes": len(names), "members": len(members), "rigidity_rank": rank, "isostatic_count": need,
        "redundant_members": len(members) - rank,
        "tube_length_mm": {k: round(v, 0) for k, v in total_len.items()},
        "tube_mass_kg": round(mass_tube, 2),
        "min_stiffness_eig": sol["min_eig"],
        "support_reaction_max_N": {c: round(sol["cases"][c]["react_max"], 4) for c in loads},
        "min_sf_yield": round(min(r["sf_yield"] for r in rows), 2),
        "min_sf_buckle": round(min(r["sf_buckle"] for r in rows), 2),
        "failing_members": [r["id"] for r in fails],
        "min_gap_to_engine_mm": round(clr, 1),
        "closest_to_engine": sorted([(k, round(v, 1)) for k, v in gaps.items()], key=lambda kv: kv[1])[:5],
        "min_tube_to_tube_gap_mm": mgap[0][0] if mgap else None,
        "closest_tube_pairs": [list(x) for x in mgap[:3]],
        "min_gap_to_airbox_zone_mm": round(air_gap, 1),
        "airbox_zone_mm": {k: list(v) for k, v in KEEP_OUT["airbox"].items()},
        "removed_base_members": [[a, b, round(d, 1)] for a, b, d in blocked],
        "added_members": [list(e) for e in added],
        "engine": {
            "origin_mm": [float(x) for x in ENGINE_ORIGIN],
            "envelope_mm": {k: [round(float(v[0]), 1), round(float(v[1]), 1)] for k, v in ENGINE.items()},
            "mount_y_mm": MOUNT_Y,
            "wet_kg": ENGINE_IF["mass_wet_kg"], "extras_kg": ENGINE_EXTRA_KG, "drivetrain_allowance_kg": DRIVETRAIN_KG,
            "kg_on_each_E": round(M_E, 2), "kg_on_each_F": round(M_F, 2),
            "cg_vehicle_mm": [round(float(x), 1) for x in ENGINE_CG],
            "front_share": round(float(_fE), 3),
        },
        "cases": info,
        "extent_mm": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
        "u_max_mm": {c: sol["cases"][c]["u_max"] for c in loads},
    }
    print(json.dumps(summary, indent=1, default=float))
    print("\n%-10s %-5s %8s  %9s %9s %9s  %7s %7s" % ("member", "size", "len", "static", "bump3g", "brake1g", "SFy", "SFb"))
    for r in rows:
        f = r["forces"]
        print("%-10s %-5s %8.0f  %9.0f %9.0f %9.0f  %7.2f %7.2f" % (
            r["id"], r["size"], r["length"], f["static"], f["bump_3g"], f["brake_1g"], r["sf_yield"],
            min(r["sf_buckle"], 999)))
    results = {"summary": summary}
    with open(os.path.join(OUT, "results.json"), "w") as fh:
        json.dump(results, fh, indent=1, default=float)
    if "--no-export" not in sys.argv:
        export_all(names, pos, rows, cuts, results)
        print("exported: frame.step frame.dxf cutlist.csv preview_data.json results.json")
    return 0 if not fails and not bad else 1


if __name__ == "__main__":
    sys.exit(main())
