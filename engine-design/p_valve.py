"""Valvetrain parts at the assembled pose (firing TDC, all valves closed)."""
import math
import numpy as np
import cadquery as cq
import params as P
import calc
from cadutil import *

D = P.derived()
Z_P = D["z_tip"] + P.LASH_CAP_T + 1.1 + P.FOLLOWER_T / 2        # follower and pivot centre height
RET_S = lambda L: L - 9.0                                       # axial position of the retainer underside
SPRING_L_INST = 32.5                                            # installed length of both springs (mm)
SPRING_S0 = lambda L: RET_S(L) - SPRING_L_INST


def _vcfg(kind):
    return P.VALVE_IN if kind == "in" else P.VALVE_EX


def valve_local(kind):
    v = _vcfg(kind)
    d, st, L = v["d"], v["stem"], v["length"]
    rim = 1.6
    neck = 0.30 * d
    pts = [(0, 0), (d / 2, 0), (d / 2, rim), (st / 2 + 2.2, neck), (st / 2, neck + 3.5), (st / 2, L - 7.5), (st / 2 - 0.5, L - 7.0),
           (st / 2 - 0.5, L - 3.5), (st / 2, L - 3.0), (st / 2, L), (0, L)]
    return revolve_z(pts)


def valve(kind, side=1):
    for vv in D["valves"]:
        if vv["kind"] == kind and vv["side"] == side:
            return place_z_to(valve_local(kind), vv["seat"], vv["axis"])
    raise KeyError((kind, side))


def valve_at(kind, side, lift):
    for vv in D["valves"]:
        if vv["kind"] == kind and vv["side"] == side:
            return valve(kind, side).translate(V(*[vv["axis"][i] * lift for i in range(3)]))


def _place_on_valve(solid_local, vv, s=0.0):
    org = tuple(vv["seat"][i] + vv["axis"][i] * s for i in range(3))
    return place_z_to(solid_local, org, vv["axis"])


def spring_pair(design, vv):
    o, i = design["spring"]["outer"], design["spring"]["inner"]
    L = vv["length"]
    s0 = SPRING_S0(L)
    so = tube_z((o["D"] + o["d"]) / 2, (o["D"] - o["d"]) / 2, 0.0, SPRING_L_INST)
    si = tube_z((i["D"] + i["d"]) / 2, (i["D"] - i["d"]) / 2, 0.0, SPRING_L_INST)
    return _place_on_valve(so, vv, s0), _place_on_valve(si, vv, s0)


def retainer(vv):
    pts = [(2.9, 0.0), (9.5, 0.0), (9.5, 1.0), (6.0, 2.5), (4.3, 2.5), (2.9, 1.3)]
    return _place_on_valve(revolve_z(pts), vv, RET_S(vv["length"]))


def keepers(vv):
    L = vv["length"]
    ring = tube_z(3.1, 1.5, 0.0, 3.4)
    return _place_on_valve(ring, vv, L - 6.9)


def lash_cap(vv):
    return _place_on_valve(cyl_z(4.5, 0.0, P.LASH_CAP_T), vv, vv["length"] + 0.05)


def follower_local():
    """Follower for the intake side (x < 0) built with its pivot at the origin; lever extends toward -x."""
    tip = D["tip_x"] - P.PIVOT_X
    w = P.FOLLOWER_W
    t = P.FOLLOWER_T
    body = box(-tip - 5.5, 0.0, -w / 2, w / 2, -t / 2, t / 2)
    boss = cyl_y(6.5, -w / 2, w / 2)
    body = fuse(body, boss)
    # lightening pockets in the sides, a thin web left in the middle
    for s in (1, -1):
        y0, y1 = yr(s * 1.8, s * (w / 2 + 0.01))
        body = cut(body, box(-tip + 2.0, -9.0, y0, y1, -t / 2 + 1.5, t / 2 - 1.5))
    body = cut(body, cyl_y(P.SHAFT_D / 2 + 0.1, -w, w))
    return body


def yr(a, b):
    return (min(a, b), max(a, b))


def follower(kind, side):
    """Placed follower for valve (kind, side)."""
    vv = [v for v in D["valves"] if v["kind"] == kind and v["side"] == side][0]
    f = follower_local()
    sx = -1.0 if vv["seat"][0] < 0 else 1.0
    if sx > 0:
        f = f.rotate(V(0, 0, 0), V(0, 0, 1), 180)
    return f.translate(V(sx * P.PIVOT_X, vv["seat"][1], Z_P))


def follower_shaft(sx):
    return cyl_y(P.SHAFT_D / 2, -40.0, 40.0, x=sx * P.PIVOT_X, z=Z_P)


# ------------------------------------------------------------------ cams
def cam(kind):
    v = _vcfg(kind)
    sx = -1 if kind == "in" else 1
    cx = P.CAM_X * sx
    ang, r = calc.cam_lobe_radius(kind, n=720)
    # radius vs angle from the nose over the full circle
    pts = []
    for a in np.arange(-180.0, 180.0, 2.0):
        rad = P.CAM_BASE_R
        if abs(math.radians(a)) <= ang[-1]:
            rad = float(np.interp(math.radians(a), ang, r))
        aa = math.radians(a)
        pts.append((cx + rad * math.sin(aa), ZC_ + rad * math.cos(aa)))
    ys = (18.0, -18.0) if kind == "in" else (16.5, -16.5)
    shaft = cyl_y(P.CAM_JOURNAL_D / 2, -P.WALL_Y - 10.0, P.WALL_Y - 9.0, x=cx, z=ZC_)
    lobes = []
    for yl in ys:
        lobes.append(prism_xz(pts, yl - 5.5, yl + 5.5))
    solid = fuse(shaft, *lobes)
    phi = 180.0 + (360.0 - (P.LCA_IN if kind == "in" else P.LCA_EX)) / 2.0
    return solid.rotate(V(cx, 0, ZC_), V(cx, 1, ZC_), phi)


ZC_ = D["z_cam"]


def spring_design(kind, masses=None):
    return calc.design_valvetrain(kind, masses)


if __name__ == "__main__":
    for kind in ("in", "ex"):
        dsg = spring_design(kind)
        vv = [v for v in D["valves"] if v["kind"] == kind][0]
        parts = dict(valve=valve(kind), outer=spring_pair(dsg, vv)[0], inner=spring_pair(dsg, vv)[1], retainer=retainer(vv), keepers=keepers(vv),
                     cap=lash_cap(vv), follower=follower(kind, 1), cam=cam(kind))
        for n, s in parts.items():
            print("%s %-9s solids %d valid %s vol %.0f mm3 (%.1f g steel) %s" % (kind, n, n_solids(s), s.isValid(), vol(s), vol(s) * 7.85e-3, bbox(s)))
    print("follower shaft", bbox(follower_shaft(-1)))
