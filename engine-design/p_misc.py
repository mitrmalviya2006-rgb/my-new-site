"""Pumps, ignition, intake, filter, hardware and small parts at the assembled pose."""
import math
import cadquery as cq
import params as P
import p_rotating as R
import p_static as S
from cadutil import *

D = P.derived()
ZC = D["z_cam"]
YW = P.CASE_Y


def yr(a, b):
    return (min(a, b), max(a, b))


# ------------------------------------------------------------------ bearing shells for the balance shaft
def bal_shells():
    y0, y1 = P.BAL_BEARING_Y
    ring = tube_y(13.0, 11.0, y0, y1, x=P.BAL_X, z=0.0)
    up = common(ring, box(P.BAL_X - 20, P.BAL_X + 20, 0, 80, 0, 20))
    lo = common(ring, box(P.BAL_X - 20, P.BAL_X + 20, 0, 80, -20, 0))
    return up, lo


# ------------------------------------------------------------------ pumps
def water_impeller():
    y0 = YW + 18.0
    hub = tube_y(13.0, 11.0, y0, y0 + 8.0, x=P.BAL_X, z=0.0)
    back = tube_y(18.0, 11.0, y0 + 2.0, y0 + 3.5, x=P.BAL_X, z=0.0)
    vanes = []
    for k in range(6):
        v = box(P.BAL_X - 0.9, P.BAL_X + 0.9, y0 + 3.5, y0 + 8.0, 12.5, 17.8)
        vanes.append(v.rotate(V(P.BAL_X, 0, 0), V(P.BAL_X, 1, 0), 60.0 * k))
    return fuse(hub, back, *vanes)


def gerotor_pair():
    y1 = -YW - 2.0
    y0 = y1 - 10.0
    inner = tube_y(15.5, 11.0, y0, y1, x=P.BAL_X, z=0.0)
    outer = tube_y(24.0, 17.0, y0, y1, x=P.BAL_X + 1.0, z=0.0)
    return inner, outer


# ------------------------------------------------------------------ electrics
def trigger_wheel():
    y0, y1 = P.TRIGGER_SEAT[1], P.TRIGGER_SEAT[0]
    disc = R.toothed_disc(0, 0, 36, 30.0, 33.5, 0.32, 0.22, y0, y1, P.TRIGGER_SEAT[2], 0.0)
    # remove two teeth (36-2) at the reference position
    gap = prism_xz(sector_pts(0, 0, lambda a: 40.0, -10.5, 10.5, n=6), y0 - 1, y1 + 1)
    return cut(disc, gap)


def alt_rotor():
    """Cup rotor: back plate on the engine side, rim opening outward so the stator (on the cover) enters from outside."""
    y_back0, y_back1 = -82.5, -78.5
    plate = cyl_y(66.0, y_back0, y_back1)
    rim = tube_y(66.0, 60.0, -112.0, y_back1)
    hub = tube_y(24.0, 10.0, -100.0, y_back1)
    return cut(fuse(plate, rim, hub), cyl_y(10.0, -101.0, y_back1 + 1))


def alt_stator():
    return tube_y(58.0, 29.0, -108.0, -88.0)


def spark_plug():
    body = cyl_z(8.0, 185.2, 205.0)
    thread = cyl_z(4.95, D["z_ridge"] - 0.5, 185.2)
    return fuse(body, thread)


def spark_coil():
    return cyl_z(10.0, 205.0, ZC + 40.0)


# ------------------------------------------------------------------ intake and filter
def throttle_body():
    outer = cyl_x(28.0, -135.0, -P.HEAD_X, y=0.0, z=200.0)
    spigot = cyl_x(25.5, -P.HEAD_X, -P.HEAD_X + 8.0, y=0.0, z=200.0)
    body = fuse(outer, spigot)
    return cut(body, cyl_x(22.0, -136.0, -P.HEAD_X + 9.0, y=0.0, z=200.0))


def oil_filter():
    x0 = P.CASE_X[1] + 14.0
    return cyl_x(31.0, x0, x0 + 55.0, y=0.0, z=-75.0)


# ------------------------------------------------------------------ chain guide and tensioner
def chain_guide_tensioner():
    hull, _ = R.chain_hull()
    cx = sum(p[0] for p in hull) / len(hull)
    cz = sum(p[1] for p in hull) / len(hull)
    edges = []
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        edges.append((math.dist(a, b), a, b))
    edges.sort(reverse=True)
    out = []
    for ln, a, b in edges[:2]:
        t0, t1 = 0.22, 0.80
        pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        dx, dz = b[0] - a[0], b[1] - a[1]
        n = (dz, -dx)
        nl = math.hypot(*n)
        n = (n[0] / nl, n[1] / nl)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if (mid[0] - cx) * n[0] + (mid[1] - cz) * n[1] < 0:
            n = (-n[0], -n[1])
        o1, o2 = 5.4, 11.4
        pts = [(pa[0] + n[0] * o1, pa[1] + n[1] * o1), (pb[0] + n[0] * o1, pb[1] + n[1] * o1),
               (pb[0] + n[0] * o2, pb[1] + n[1] * o2), (pa[0] + n[0] * o2, pa[1] + n[1] * o2)]
        out.append(prism_xz(pts, P.SPROCKET_Y - 4.0, P.SPROCKET_Y + 4.0))
    return out[0], out[1]


# ------------------------------------------------------------------ hardware
def stud():
    return cyl_z(P.STUD_D / 2, P.STUD_Z0, ZC - 8.0)


def nut_m10():
    pts = [(9.8 * math.cos(math.radians(60 * i)), 9.8 * math.sin(math.radians(60 * i))) for i in range(6)]
    n = prism_xy(pts, ZC - 16.0, ZC - 8.0)
    return cut(n, cyl_z(5.0, ZC - 17.0, ZC - 7.0))


def washer_m10():
    return tube_z(10.0, 5.2, ZC - 18.0, ZC - 16.0)


def bolt_m10_main(pos):
    x, y = pos
    return fuse(cyl_z(5.0, -45.0, 22.0, x=x, y=y), cyl_z(8.0, -51.0, -45.0, x=x, y=y))


def bolt_m8_case(pos):
    x, y = pos
    return fuse(cyl_z(4.0, -45.0, 20.0, x=x, y=y), cyl_z(5.5, -51.0, -45.0, x=x, y=y))


def bolt_m6_pan(pos):
    x, y = pos
    return fuse(cyl_z(3.0, -100.0, -35.0, x=x, y=y), cyl_z(5.0, -106.0, -100.0, x=x, y=y))


def bolt_m6_ladder(pos):
    x, y = pos
    return fuse(cyl_z(3.0, ZC - 13.0, ZC + 14.0, x=x, y=y), cyl_z(5.0, ZC + 14.0, ZC + 19.0, x=x, y=y))


if __name__ == "__main__":
    for name, fn in (("shell", lambda: bal_shells()[0]), ("impeller", water_impeller), ("gerotor_in", lambda: gerotor_pair()[0]),
                     ("gerotor_out", lambda: gerotor_pair()[1]), ("trigger", trigger_wheel), ("rotor", alt_rotor), ("stator", alt_stator),
                     ("plug", spark_plug), ("coil", spark_coil), ("tb", throttle_body), ("filter", oil_filter),
                     ("guide", lambda: chain_guide_tensioner()[0]), ("tens", lambda: chain_guide_tensioner()[1]),
                     ("stud", stud), ("nut", nut_m10), ("washer", washer_m10)):
        s = fn()
        print("%-12s solids %d valid %s vol %.0f %s" % (name, n_solids(s), s.isValid(), vol(s), bbox(s)))
