"""Static structure at the assembled pose: upper case, bedplate, oil pan, liner, barrel, gasket, head, cam ladder, cam cover, side covers."""
import math
import cadquery as cq
import params as P
import calc
from cadutil import *

D = P.derived()
X0, X1 = P.CASE_X
YW = P.CASE_Y
T14 = math.tan(math.radians(P.VALVE_TILT))
ZH = P.Z_HEAD_DECK
ZC = D["z_cam"]
STUDS = [(sx * P.STUD_XY[0], sy * P.STUD_XY[1]) for sx in (1, -1) for sy in (1, -1)]
BOLTS_M8 = [(x, s * 55.5) for x in (-128.0, -68.0, -34.0, 34.0, 50.0, 78.0) for s in (1, -1)]
BOLTS_M10 = [(sx * 34.0, sy * 41.0) for sx in (1, -1) for sy in (1, -1)]
BOLTS_PAN = [(x, s * 57.5) for x in (-112.0, -85.0, -50.0, 0.0, 66.0) for s in (1, -1)] + [(-134.0, 0.0), (80.0, 0.0)]
LUG_UPPER = (83.0, 163.0)       # engine mount on the head front (x, z), hole along y
LUG_LOWER = (-125.0, 78.0)      # engine mount at the rear boss of the upper case
LUG_Y = (YW, YW + 20.0)         # |y| range of the mount ears
R_MAIN_SHELL = P.MAIN_D / 2 + P.MAIN_SHELL_T


def yr(a, b):
    return (min(a, b), max(a, b))


def _bal_t():
    return P.BAL_T


def _common_case_cuts(body, upper):
    """Features that appear in both halves: saddles, neck notches, balance pockets, shaft bore, bearing shells."""
    sel = (lambda z0, z1: (0.0, z1)) if upper else (lambda z0, z1: (z0, 0.0))
    y_m = P.MAIN_Y[0]
    for s in (1, -1):
        body = cut(body, cyl_y(R_MAIN_SHELL, *yr(s * (P.MAIN_Y[0] + P.AXIAL_CLEAR - 0.01), s * P.MAIN_Y[1])))
        r_neck = (P.OUT_NECK_D if s > 0 else P.ALT_NECK_D) / 2 + 0.6
        body = cut(body, cyl_y(r_neck, *yr(s * (P.MAIN_Y[1] - 0.01), s * (YW + 1.0))))
        # balance weight pocket
        body = cut(body, cyl_y(34.0, *yr(s * (P.BAL_WEIGHT_Y0 - 1.0), s * (P.BAL_WEIGHT_Y0 + _bal_t() + 1.0)), x=P.BAL_X, z=0.0))
        # balance shaft shell seat (Ø 26) at the end walls
        body = cut(body, cyl_y(13.0, *yr(s * P.BAL_BEARING_Y[0], s * (YW + 1.0)), x=P.BAL_X, z=0.0))
    body = cut(body, cyl_y(11.8, -YW - 1.0, YW + 1.0, x=P.BAL_X, z=0.0))
    return body


def upper_case():
    z_top = P.CASE_TOP_Z
    body = box(X0, X1, -YW, YW, 0.0, z_top)
    y_m = P.MAIN_Y[0] + P.AXIAL_CLEAR
    body = cut(body, cyl_y(P.CAVITY_UP, -y_m, y_m))
    body = cut(body, cyl_z(49.0, 30.0, z_top + 1.0))
    body = _common_case_cuts(body, True)
    for (x, y) in STUDS:
        body = cut(body, cyl_z(5.1, P.STUD_Z0, z_top + 1.0, x=x, y=y))
    for (x, y) in BOLTS_M10:
        body = cut(body, cyl_z(5.0, -1.0, 24.0, x=x, y=y))
    for (x, y) in BOLTS_M8:
        body = cut(body, cyl_z(4.0, -1.0, 22.0, x=x, y=y))
    # rear engine mount boss and ears (above the side covers)
    boss = box(X0, X0 + 26.0, -YW, YW, z_top, LUG_LOWER[1] + 14.0)
    body = fuse(body, boss)
    for s_ in (1, -1):
        y0, y1 = yr(s_ * LUG_Y[0], s_ * LUG_Y[1])
        ear = box(X0, X0 + 26.0, y0, y1, LUG_LOWER[1] - 14.0, LUG_LOWER[1] + 14.0)
        ear = cut(ear, cyl_y(7.0, y0 - 1, y1 + 1, x=LUG_LOWER[0], z=LUG_LOWER[1]))
        body = fuse(body, ear)
    return body


def bedplate():
    body = box(X0, X1, -YW, YW, -45.0, 0.0)
    y_m = P.MAIN_Y[0] + P.AXIAL_CLEAR
    body = cut(body, cyl_y(P.CAVITY_LOW, -y_m, y_m))
    body = _common_case_cuts(body, False)
    for (x, y) in BOLTS_M10:
        body = cut(body, cyl_z(5.3, -46.0, 1.0, x=x, y=y))
    for (x, y) in BOLTS_M8:
        body = cut(body, cyl_z(4.3, -46.0, 1.0, x=x, y=y))
    for (x, y) in BOLTS_PAN:
        body = cut(body, cyl_z(3.0, -46.0, -33.0, x=x, y=y))
    return body


def oil_pan():
    body = box(X0, X1, -YW, YW, -100.0, -45.0)
    body = cut(body, box(X0 + 12.0, X1 - 10.0, -52.0, 52.0, -93.0, -44.0))
    for (x, y) in BOLTS_PAN:
        body = cut(body, cyl_z(3.3, -101.0, -44.0, x=x, y=y))
    for (x, y) in BOLTS_M8:
        body = cut(body, cyl_z(8.5, -52.5, -44.0, x=x, y=y))
    # drain boss and oil filter boss on the front face
    body = fuse(body, cyl_x(18.0, X1, X1 + 14.0, y=0.0, z=-75.0))
    body = cut(body, cyl_x(10.0, X1 - 1.0, X1 + 15.0, y=0.0, z=-75.0))
    return body


# ------------------------------------------------------------------ cylinder stack
def liner():
    ro = P.LINER_OD / 2
    rf = P.LINER_FLANGE[0] / 2
    tf = P.LINER_FLANGE[1]
    body = fuse(tube_z(ro, P.LINER_ID / 2, P.LINER_Z0, P.Z_DECK - tf), tube_z(rf, P.LINER_ID / 2, P.Z_DECK - tf, P.Z_DECK))
    for z0 in (P.LINER_Z0 + 3.0, P.LINER_Z0 + 8.0):
        body = cut(body, tube_z(ro + 1, ro - 2.0, z0, z0 + 2.0))
    return body


def _barrel_outline(z0, z1):
    parts = [cyl_z(P.BARREL_R, z0, z1)]
    for (x, y) in STUDS:
        parts.append(cyl_z(9.0, z0, z1, x=x, y=y))
        ang = math.degrees(math.atan2(y, x))
        dist = math.hypot(x, y)
        web = box(0.0, dist, -9.0, 9.0, z0, z1).rotate(V(0, 0, 0), V(0, 0, 1), ang)
        parts.append(web)
    return fuse(*parts)


TRANSFER = [(54.2 * math.cos(math.radians(a)), 54.2 * math.sin(math.radians(a))) for a in (45.0, 135.0, 225.0, 315.0)]


def barrel():
    body = _barrel_outline(P.LINER_Z0, P.Z_DECK)
    body = cut(body, cyl_z(P.LINER_OD / 2, P.LINER_Z0 - 1, P.Z_DECK + 1))
    body = cut(body, cyl_z(P.LINER_FLANGE[0] / 2 + 0.3, P.Z_DECK - P.LINER_FLANGE[1], P.Z_DECK + 1))
    body = cut(body, tube_z(P.JACKET_R, P.LINER_OD / 2, P.LINER_Z0 + 14.0, 145.5))
    for (x, y) in STUDS:
        body = cut(body, cyl_z(5.3, P.LINER_Z0 - 1, P.Z_DECK + 1, x=x, y=y))
    for (x, y) in TRANSFER:
        body = cut(body, cyl_z(3.0, 145.0, P.Z_DECK + 1, x=x, y=y))
    # coolant inlet boss at the rear, low
    body = fuse(body, cyl_x(13.0, -78.0, -50.0, y=0.0, z=88.0))
    body = cut(body, cyl_x(8.0, -79.0, -50.0, y=0.0, z=88.0))
    return body


def head_gasket():
    body = _barrel_outline(P.Z_DECK, ZH)
    body = cut(body, cyl_z(47.0, P.Z_DECK - 1, ZH + 1))
    for (x, y) in STUDS:
        body = cut(body, cyl_z(5.3, P.Z_DECK - 1, ZH + 1, x=x, y=y))
    for (x, y) in TRANSFER:
        body = cut(body, cyl_z(3.2, P.Z_DECK - 1, ZH + 1, x=x, y=y))
    return body


# ------------------------------------------------------------------ cylinder head
def _roof_z(x):
    return D["z_ridge"] - abs(x) * T14


def chamber_cavity():
    """Pent-roof combustion space above the head deck, inside the bore."""
    tent = prism_xz([(-48, ZH - 1), (-48, _roof_z(-48)), (0, D["z_ridge"]), (48, _roof_z(48)), (48, ZH - 1)], -50, 50)
    return common(tent, cyl_z(47.0, ZH - 1, D["z_ridge"] + 1))


def head():
    body = box(-P.HEAD_X, P.HEAD_X, -YW, YW, ZH, ZC)
    body = cut(body, chamber_cavity())
    cuts = []
    for v in D["valves"]:
        s = v["seat"]
        a = v["axis"]
        d = v["d"]
        # seat recess for the valve head and neck
        cuts.append(cyl_dir(d / 2 + 0.8, (s[0] - a[0] * 0.5, s[1], s[2] - a[2] * 0.5), a, 5.0))
        # stem guide hole (guide pressed in is not modelled), then spring pocket
        cuts.append(cyl_dir(2.6, (s[0], s[1], s[2]), a, v["length"] - 24.0))
        cuts.append(cyl_dir(12.5, (s[0] + a[0] * P.SPRING_POCKET_S0, s[1], s[2] + a[2] * P.SPRING_POCKET_S0), a, 70.0))
    # ports
    for v in D["valves"]:
        s, a = v["seat"], v["axis"]
        if v["kind"] == "in":
            A = tuple(s[i] + a[i] * 18.0 for i in range(3))
            F = (-P.HEAD_X - 1.0, math.copysign(14.0, s[1]), 200.0)
            dvec = tuple(F[i] - A[i] for i in range(3))
            L = math.sqrt(sum(c * c for c in dvec))
            dvec = tuple(c / L for c in dvec)
            cuts.append(cyl_dir(12.0, (s[0] - a[0] * 0.5, s[1], s[2] - a[2] * 0.5), a, 19.0))
            cuts.append(cyl_dir(12.0, A, dvec, L))
        else:
            A = tuple(s[i] + a[i] * 16.0 for i in range(3))
            B = (40.0, 0.0, 180.0)
            dvec = tuple(B[i] - A[i] for i in range(3))
            L = math.sqrt(sum(c * c for c in dvec))
            dvec = tuple(c / L for c in dvec)
            cuts.append(cyl_dir(10.0, (s[0] - a[0] * 0.5, s[1], s[2] - a[2] * 0.5), a, 17.0))
            cuts.append(cyl_dir(10.0, A, dvec, L))
    dx, dz = 30.0, 5.0
    ln = math.hypot(dx, dz)
    cuts.append(cyl_dir(16.0, (40.0, 0.0, 180.0), (dx / ln, 0.0, dz / ln), ln + 2.0))
    cuts.append(cyl_x(19.0, P.HEAD_X - 4.0, P.HEAD_X + 1.0, y=0.0, z=185.0))     # exhaust flange recess
    cuts.append(cyl_x(26.0, -P.HEAD_X - 1.0, -P.HEAD_X + 8.0, y=0.0, z=200.0))   # intake flange recess
    # plug well and thread hole
    cuts.append(cyl_z(P.PLUG_WELL_D / 2, 185.0, ZC + 1.0))
    cuts.append(cyl_z(P.PLUG_THREAD_D / 2, D["z_ridge"] - 1.0, 186.0))
    # follower and cam windows, two per side
    for sx in (-1, 1):
        x0, x1 = yr(sx * (P.PIVOT_X - 7.5), sx * (P.CAM_X + 18.0))
        for sy in (-1, 1):
            y0, y1 = yr(sy * 8.5, sy * 29.5)
            cuts.append(box(x0, x1, y0, y1, D["z_tip"] - 4.0, ZC + 1.0))
    # stud holes with nut recesses
    for (x, y) in STUDS:
        cuts.append(cyl_z(5.6, ZH - 1.0, ZC + 1.0, x=x, y=y))
        cuts.append(cyl_z(10.5, ZC - 18.0, ZC + 1.0, x=x, y=y))
    # cam saddles (lower halves) and the cam stub hole through the alternator-side (-y) wall
    for sx in (-1, 1):
        cuts.append(cyl_y(P.CAM_JOURNAL_D / 2 + 0.05, -YW + 9.0, 54.0, x=sx * P.CAM_X, z=ZC))
        cuts.append(cyl_y(P.CAM_JOURNAL_D / 2 + 0.05, -YW - 1.0, -YW + 10.0, x=sx * P.CAM_X, z=ZC))
        # follower shaft bore through the towers
        cuts.append(cyl_y(P.SHAFT_D / 2 + 0.05, -42.0, YW + 1.0, x=sx * P.PIVOT_X, z=D["z_tip"] + P.LASH_CAP_T + 1.1 + P.FOLLOWER_T / 2))
    # ladder bolt holes
    for (x, y) in LADDER_BOLTS:
        cuts.append(cyl_z(3.0, ZC - 16.0, ZC + 1.0, x=x, y=y))
    out = cut(body, *cuts)
    # engine mount blocks and ears on the front of the head (beside the exhaust port)
    for s_ in (1, -1):
        y0, y1 = yr(s_ * 40.0, s_ * YW)
        blk = box(P.HEAD_X - 1.0, LUG_UPPER[0] + 11.0, y0, y1, LUG_UPPER[1] - 14.0, LUG_UPPER[1] + 14.0)
        y2, y3 = yr(s_ * LUG_Y[0], s_ * LUG_Y[1])
        ear = box(P.HEAD_X + 1.0, LUG_UPPER[0] + 11.0, y2, y3, LUG_UPPER[1] - 14.0, LUG_UPPER[1] + 14.0)
        blk = cut(fuse(blk, ear), cyl_y(7.0, -YW - 30.0, YW + 30.0, x=LUG_UPPER[0], z=LUG_UPPER[1]))
        out = fuse(out, blk)
    return out


LADDER_BOLTS = [(sx * 50.0, sy * 34.0) for sx in (1, -1) for sy in (1, -1)] + [(0.0, 47.0), (0.0, -47.0), (58.0, 0.0), (-58.0, 0.0)]
COVER_BOLTS = [(sx * 64.0, sy * 55.0) for sx in (1, -1) for sy in (1, -1)] + [(0.0, 57.0), (0.0, -57.0), (64.0, 0.0), (-64.0, 0.0)]


def cam_ladder():
    z0, z1 = ZC, ZC + 14.0
    body = box(-64.0, 64.0, -56.0, 56.0, z0, z1)
    cuts = []
    for sx in (-1, 1):
        x0, x1 = yr(sx * (P.CAM_X - 17.5), sx * (P.CAM_X + 17.5))
        for sy in (-1, 1):
            y0, y1 = yr(sy * 8.5, sy * 29.5)
            cuts.append(box(x0, x1, y0, y1, z0 - 1.0, z1 + 1.0))
        cuts.append(cyl_y(P.CAM_JOURNAL_D / 2 + 0.05, -YW - 1.0, YW + 1.0, x=sx * P.CAM_X, z=ZC))
    cuts.append(cyl_z(P.PLUG_WELL_D / 2 + 1.0, z0 - 1.0, z1 + 1.0))
    for (x, y) in LADDER_BOLTS:
        cuts.append(cyl_z(3.3, z0 - 1.0, z1 + 1.0, x=x, y=y))
    for (x, y) in COVER_BOLTS:
        cuts.append(cyl_z(2.5, z1 - 10.0, z1 + 1.0, x=x * 0.0 + x, y=y)) if False else None
    return cut(body, *[c for c in cuts if c is not None])


def cam_cover():
    z1 = ZC + 14.0 + 22.0
    body = box(-P.HEAD_X, P.HEAD_X, -YW, YW, ZC, z1)
    body = cut(body, box(-65.0, 65.0, -57.0, 57.0, ZC - 1.0, z1 - 6.0))
    body = cut(body, cyl_z(12.5, z1 - 8.0, z1 + 1.0))
    for sx in (-1, 1):
        body = cut(body, cyl_y(13.0, -YW - 1.0, -56.0, x=sx * P.CAM_X, z=ZC))
    return body


# ------------------------------------------------------------------ side covers and pump cover
def cover_chain():
    y_in = -YW
    y_out = y_in - 18.0
    plate = fuse(box(X0, X1, y_out, y_in, -100.0, 63.0),
                 box(-48.0, 48.0, y_out, y_in, 63.0, 150.0),
                 box(-P.HEAD_X, P.HEAD_X, y_out, y_in, 150.0, ZC + 36.0),
                 cyl_y(78.0, y_out - 40.0, y_in, x=0.0, z=0.0))
    pocket = chain_pocket_solid(y_in - 14.0, y_in + 1.0)
    alt = cyl_y(72.0, y_in - 64.0, y_in + 1.0, x=0.0, z=0.0)
    pump = cyl_y(28.0, y_in - 14.0, y_in + 1.0, x=P.BAL_X, z=0.0)
    plate = cut(plate, pocket, alt, pump)
    boss = tube_y(45.0, 26.0, y_in - 64.0, y_in - 46.0, x=0.0, z=0.0)       # stator mounting boss in the pocket bottom
    plate = fuse(plate, boss)
    plate = cut(plate, cyl_y(10.0, y_in - 66.0, y_in - 52.0, x=0.0, z=0.0)) if False else plate
    return plate


def chain_pocket_solid(y0, y1):
    import p_rotating as R
    hull, _ = R.chain_hull()
    w = cq.Wire.makePolygon([V(x, 0, z) for x, z in hull], close=True)
    off = w.offset2D(14.0, "intersection")[0]
    f = cq.Face.makeFromWires(off)
    return cq.Solid.extrudeLinear(f, V(0, y1 - y0, 0)).translate(V(0, y0, 0))


def cover_gear():
    y_in = YW
    y_out = y_in + 26.0
    body = fuse(cyl_y(58.0, y_in, y_out, x=0.0, z=0.0), cyl_y(58.0, y_in, y_out, x=P.BAL_X, z=0.0),
                box(P.BAL_X, 0.0, y_in, y_out, -58.0, 58.0))
    gear_chamber = fuse(cyl_y(51.0, y_in - 1.0, y_in + 18.0, x=0.0, z=0.0), cyl_y(51.0, y_in - 1.0, y_in + 18.0, x=P.BAL_X, z=0.0),
                        box(P.BAL_X, 0.0, y_in - 1.0, y_in + 18.0, -51.0, 51.0))
    pump_pocket = cyl_y(22.0, y_in + 17.0, y_in + 27.0, x=P.BAL_X, z=0.0)
    seal = cyl_y(21.0, y_in - 1.0, y_out + 1.0, x=0.0, z=0.0)
    return cut(body, gear_chamber, pump_pocket, seal)


def pump_cover():
    y0 = YW + 26.0
    body = cyl_y(34.0, y0, y0 + 8.0, x=P.BAL_X, z=0.0)
    body = fuse(body, cyl_y(14.0, y0 + 8.0, y0 + 26.0, x=P.BAL_X, z=0.0))
    return cut(body, cyl_y(10.0, y0 - 1.0, y0 + 27.0, x=P.BAL_X, z=0.0))


if __name__ == "__main__":
    import time
    P.BAL_T = 23.7
    for name in ("upper_case", "bedplate", "oil_pan", "liner", "barrel", "head_gasket", "head", "cam_ladder", "cam_cover", "cover_chain", "cover_gear", "pump_cover"):
        t0 = time.time()
        try:
            s = globals()[name]()
            print("%-12s solids %d valid %s vol %.0f mm3 bbox %s (%.1fs)" % (name, n_solids(s), s.isValid(), vol(s), bbox(s), time.time() - t0))
        except Exception as e:
            print(name, "ERROR", repr(e))
