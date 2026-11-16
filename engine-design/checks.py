"""CAD checks: overlaps in the assembled pose, motion sweeps, piston-valve clearance, assembly insertion sweeps."""
import math
import time
import numpy as np
import cadquery as cq
import params as P
import calc
import p_rotating as R
import p_valve as VT
from cadutil import *

D = P.derived()


def _bb(s):
    b = s.BoundingBox()
    return (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)


def _bb_overlap(a, b, tol=0.0):
    return not (a[1] < b[0] - tol or b[1] < a[0] - tol or a[3] < b[2] - tol or b[3] < a[2] - tol or a[5] < b[4] - tol or b[5] < a[4] - tol)


def overlap_report(inst, tol_mm3=1.0, skip=None, log=print):
    """Pairwise intersection volumes in the assembled pose. Returns list of (label_a, label_b, volume)."""
    skip = skip or set()
    boxes = [_bb(i["shape"]) for i in inst]
    hits = []
    n = 0
    t0 = time.time()
    for a in range(len(inst)):
        for b in range(a + 1, len(inst)):
            la, lb = inst[a]["label"], inst[b]["label"]
            pa, pb = inst[a]["part"], inst[b]["part"]
            if (pa, pb) in skip or (pb, pa) in skip:
                continue
            if not _bb_overlap(boxes[a], boxes[b]):
                continue
            n += 1
            try:
                v = inst[a]["shape"].intersect(inst[b]["shape"]).Volume()
            except Exception as e:
                v = -1.0
            if v > tol_mm3 or v < 0:
                hits.append((la, lb, v))
    log("overlap check: %d bbox-overlapping pairs tested in %.0fs, %d with intersection > %.1f mm3" % (n, time.time() - t0, len(hits), tol_mm3))
    return hits


# ------------------------------------------------------------------ crank-train motion
def pose_moving(rot, theta_deg, inst_by_label):
    """Moving parts at crank angle theta (deg from gas-exchange TDC; the build pose is firing TDC = 360)."""
    d = theta_deg - 360.0                  # rotate by d from the build pose
    z_pin = P.R * math.cos(math.radians(theta_deg)) + math.sqrt(P.ROD ** 2 - (P.R * math.sin(math.radians(theta_deg))) ** 2)
    ang = math.degrees(math.asin(P.R * math.sin(math.radians(theta_deg)) / P.ROD))
    x_pin = P.R * math.sin(math.radians(theta_deg))
    out = {}
    out["crank"] = rot(rot_shape(inst_by_label["crankshaft"], d))
    return out


def rot_shape(shape, deg):
    return shape.rotate(V(0, 0, 0), V(0, 1, 0), deg)


def rod_pose(shape, theta_deg):
    """Rod-side parts: build pose has the big end at (0, R) and the small end at (0, R+L). Move to angle theta."""
    t = math.radians(theta_deg)
    xb, zb = P.R * math.sin(t), P.R * math.cos(t)           # big end centre
    phi = math.asin(P.R * math.sin(t) / P.ROD)              # rod tilt (positive: small end toward -x)
    s = shape.translate(V(0, 0, -P.R))                      # big end centre to the origin
    s = s.rotate(V(0, 0, 0), V(0, 1, 0), math.degrees(-phi))   # rotate about y: positive rotation takes +z toward +x
    return s.translate(V(xb, 0, zb))


def piston_pose(shape, theta_deg):
    t = math.radians(theta_deg)
    z_pin = P.R * math.cos(t) + math.sqrt(P.ROD ** 2 - (P.R * math.sin(t)) ** 2)
    return shape.translate(V(0, 0, z_pin - P.Z_PIN_TDC))


def sweep_motion(by, steps=range(0, 360, 20), log=print):
    """Crank, rod, piston and balance parts against the case, liner and barrel at several crank angles.
    by: dict label/part id -> shape (build pose). Returns worst-case numbers."""
    statics = {k: by[k] for k in ("upper_case", "bedplate", "oil_pan", "liner")}
    worst = {}
    t0 = time.time()
    for th in steps:
        d = th - 360.0
        crank = rot_shape(by["crankshaft"], d)
        rodset = [rod_pose(by[k], th) for k in ("conrod", "rod_cap", "rod_bolt#1", "rod_bolt#2")]
        pist = [piston_pose(by[k], th) for k in ("piston", "piston_pin")]
        bal = rot_shape(by["balance_shaft"], 0).rotate(V(P.BAL_X, 0, 0), V(P.BAL_X, 1, 0), -d)
        moving = {"crank": crank, "rod": rodset, "piston": pist, "bal": bal}
        for mname, mv in moving.items():
            mvs = mv if isinstance(mv, list) else [mv]
            for sname, st in statics.items():
                for k, sh in enumerate(mvs):
                    if not _bb_overlap(_bb(sh), _bb(st)):
                        continue
                    v = sh.intersect(st).Volume()
                    key = (mname, sname)
                    if v > worst.get(key, (0, 0))[0]:
                        worst[key] = (v, th)
    log("motion sweep (%d crank angles) took %.0fs" % (len(list(steps)), time.time() - t0))
    return worst


# ------------------------------------------------------------------ piston to valve
def piston_valve_clearance(by, d_range=range(-70, 71, 10), log=print):
    """Minimum distance piston to each valve around gas-exchange TDC (theta = 0), with the valves at their lifts."""
    res = []
    for th in d_range:
        pis = piston_pose(by["piston"], th % 720)
        for kind, pid in (("in", "valve_intake"), ("ex", "valve_exhaust")):
            lift = float(calc.valve_lift(th % 720, kind))
            for side in (1, -1):
                label = "%s_%s#%s" % (pid, kind, "L" if side > 0 else "R")
                v = VT.valve_at(kind, side, lift)
                dmin = pis.distance(v) if lift > 0 or True else 99.0
                res.append((th, kind, side, lift, dmin))
    worst = min(res, key=lambda r: r[4])
    log("piston-valve: worst clearance %.2f mm at theta %d deg (%s valve, lift %.2f mm)" % (worst[4], worst[0], worst[1], worst[3]))
    return res, worst


# ------------------------------------------------------------------ assembly insertion sweeps
def insertion_sweep(moving, fixed_list, direction, start, step=10.0, tail=8.0):
    """Move the group along 'direction' (unit) from 'start' mm away to the assembled pose; return max overlap volume.
    A finer step is used for the last 'tail' mm."""
    d = V(*direction)
    offsets = list(np.arange(start, tail, -step)) + list(np.arange(tail, -0.01, -2.0))
    worst = (0.0, None)
    fixed_bb = [(_bb(f), f) for f in fixed_list]
    for off in offsets:
        mv = [m.translate(d * off) for m in moving]
        for m in mv:
            bm = _bb(m)
            for bf, f in fixed_bb:
                if not _bb_overlap(bm, bf):
                    continue
                v = m.intersect(f).Volume()
                if v > worst[0]:
                    worst = (v, off)
    return worst


if __name__ == "__main__":
    import assembly
    ctx, rot = assembly.build()
    inst, per = assembly.instances(ctx, rot)
    hits = overlap_report(inst)
    for h in sorted(hits, key=lambda x: -x[2])[:60]:
        print("%-32s %-32s %10.1f" % h)
