"""Rotating and reciprocating parts, built at the assembled pose: firing TDC (crank pin up, rod vertical)."""
import math
import cadquery as cq
import params as P
from cadutil import *

D = P.derived()
RP = P.PISTON_D / 2.0
T14 = math.tan(math.radians(P.VALVE_TILT))
GROOVE_TOP_Z = P.Z_CROWN_TDC - P.RING_GROOVES[0][0]         # top face of the top ring groove


# ------------------------------------------------------------------ piston group
def _crown_z(x, g):
    return D["z_ridge"] - g - abs(x) * T14


def piston(g=4.0):
    zp = P.Z_PIN_TDC
    zsb = zp - P.SKIRT_BELOW_PIN
    ztop = D["z_ridge"] + 2.0
    body = cyl_z(RP, zsb, ztop)
    tent = prism_xz([(-50, zsb - 1), (-50, _crown_z(-50, g)), (0, _crown_z(0, g)), (50, _crown_z(50, g)), (50, zsb - 1)], -50, 50)
    body = common(body, tent)
    # top land relief and ring grooves
    body = cut(body, tube_z(RP + 1, 45.45, GROOVE_TOP_Z, ztop + 1))
    for depth, w in P.RING_GROOVES:
        z1 = P.Z_CROWN_TDC - depth
        body = cut(body, tube_z(RP + 1, RP - 3.8, z1 - w, z1))
    # underside shell: wall 5 mm under the crown, 8 mm behind the ring zone, 4.5 mm skirt
    tent_in = prism_xz([(-50, zsb - 1), (-50, _crown_z(-50, g) - 4.5), (0, _crown_z(0, g) - 4.5), (50, _crown_z(50, g) - 4.5), (50, zsb - 1)], -50, 50)
    z_belt = P.Z_CROWN_TDC - 14.0
    cav_low = cyl_z(RP - 4.5, zsb - 1, z_belt)
    cav_up = cyl_z(RP - 6.0, z_belt - 0.5, ztop)
    cavity = common(fuse(cav_low, cav_up), tent_in)
    bosses = []
    for s_ in (1, -1):
        y0, y1 = sorted((s_ * P.BOSS_Y_IN, s_ * (P.PIN_LEN / 2.0)))
        cylb = cyl_y(P.BOSS_R, y0, y1, z=zp)
        rib_y0, rib_y1 = sorted((s_ * (P.BOSS_Y_IN + 3.0), s_ * (P.BOSS_Y_IN + 9.0)))
        rib = box(-9.0, 9.0, rib_y0, rib_y1, zp, ztop)
        bosses.append(common(fuse(cylb, rib), common(cyl_z(RP - 1.0, zsb, ztop), tent_in.translate(V(0, 0, 3.0)))))
    body = fuse(cut(body, cavity), *bosses)
    body = cut(body, cyl_y(P.PIN_D / 2 + 0.01, -52, 52, z=zp))
    for s in (1, -1):
        y0, y1 = sorted((s * (P.PIN_LEN / 2.0), s * 47.0))
        body = cut(body, box(-50, 50, y0, y1, zsb - 1, zp + 3.0))
    return body


def crown_envelope(g):
    """Solid (not hollow) crown shape above the top ring: what the combustion space sees."""
    zlo = GROOVE_TOP_Z
    ztop = D["z_ridge"] + 2.0
    tent = prism_xz([(-50, zlo - 1), (-50, _crown_z(-50, g)), (0, _crown_z(0, g)), (50, _crown_z(50, g)), (50, zlo - 1)], -50, 50)
    return common(cyl_z(45.45, zlo, ztop), tent)


def piston_pin():
    return tube_y(P.PIN_D / 2, P.PIN_BORE / 2, -P.PIN_LEN / 2 + 0.2, P.PIN_LEN / 2 - 0.2, z=P.Z_PIN_TDC)


def piston_rings():
    out = []
    for depth, w in P.RING_GROOVES:
        z1 = P.Z_CROWN_TDC - depth
        axial = w - 0.1
        out.append(tube_z(P.BORE / 2, P.BORE / 2 - 3.6, z1 - w + 0.05, z1 - w + 0.05 + axial))
    return out


# ------------------------------------------------------------------ connecting rod
def _rod_parts():
    R, zp = P.R, P.Z_PIN_TDC
    hb = P.ROD_BIG_W / 2
    hs = P.ROD_SMALL_W / 2
    big = cyl_y(P.ROD_BIG_OR, -hb, hb, z=R)
    lugs = []
    for sx in (1, -1):
        x0, x1 = sorted((sx * (P.ROD_BOLT_X - P.ROD_LUG_HALF), sx * (P.ROD_BOLT_X + P.ROD_LUG_HALF)))
        lugs.append(box(x0, x1, -8.0, 8.0, R - 28.0, R + 20.0))
    small = cyl_y(P.ROD_SMALL_OR, -hs, hs, z=zp)
    bx, by, tf, tw = P.ROD_BEAM_X, P.ROD_BEAM_Y, P.ROD_FLANGE_T, P.ROD_WEB_T
    z0, z1 = R + P.ROD_BIG_OR - 6.0, zp - P.ROD_SMALL_OR + 6.0
    beam = box(-bx / 2, bx / 2, -by / 2, by / 2, z0, z1)
    for s in (1, -1):
        y0, y1 = sorted((s * tw / 2, s * by / 2))
        beam = cut(beam, box(-(bx / 2 - tf), bx / 2 - tf, y0, y1, z0 + 6.0, z1 - 6.0))
    solid = fuse(big, *lugs, small, beam)
    solid = cut(solid, cyl_y(P.ROD_BIG_BORE / 2, -30, 30, z=R), cyl_y(P.ROD_SMALL_BORE / 2, -30, 30, z=zp))
    for sx in (1, -1):
        solid = cut(solid, cyl_z(P.ROD_BOLT_D / 2 + 0.25, R - 40, R + 30, x=sx * P.ROD_BOLT_X))
    body = common(solid, box(-60, 60, -30, 30, R, zp + 30))
    cap = common(solid, box(-60, 60, -30, 30, R - 40, R))
    return body, cap


def conrod():
    return _rod_parts()[0]


def rod_cap():
    return _rod_parts()[1]


def rod_bolt():
    """7/16-20 premium rod bolt: head below the cap lug, shank up into the rod body."""
    R = P.R
    shank = cyl_z(P.ROD_BOLT_D / 2, R - 28.0, R + 22.0 - 2.0, x=P.ROD_BOLT_X)
    head = cyl_z(8.0, R - 34.0, R - 28.0, x=P.ROD_BOLT_X)
    return fuse(shank, head)


def small_end_bush():
    return tube_y(P.ROD_SMALL_BORE / 2, P.PIN_D / 2 + 0.01, -P.ROD_SMALL_W / 2, P.ROD_SMALL_W / 2, z=P.Z_PIN_TDC)


def rod_shells():
    R = P.R
    ro = P.ROD_BIG_BORE / 2
    ri = P.PIN_JOURNAL_D / 2
    w = P.PIN_W / 2
    ring = tube_y(ro, ri, -w, w, z=R)
    upper = common(ring, box(-50, 50, -30, 30, R, R + 50))
    lower = common(ring, box(-50, 50, -30, 30, R - 50, R))
    return upper, lower


def main_shells():
    ro = P.MAIN_D / 2 + P.MAIN_SHELL_T
    ri = P.MAIN_D / 2
    y0, y1 = P.MAIN_Y[0] + P.AXIAL_CLEAR, P.MAIN_Y[1]
    ring = tube_y(ro, ri, y0, y1)
    return common(ring, box(-50, 50, 0, 60, 0, 50)), common(ring, box(-50, 50, 0, 60, -50, 0))


# ------------------------------------------------------------------ crankshaft
def _cw_radius(a, r_flank):
    d = abs(((a - 180.0 + 180.0) % 360.0) - 180.0)
    if d <= 22.0:
        return P.CW_R_CENTRE
    if d >= 45.0:
        return r_flank
    s = (d - 22.0) / 23.0
    s = s * s * (3 - 2 * s)
    return P.CW_R_CENTRE + (r_flank - P.CW_R_CENTRE) * s


def crank(r_flank=56.0):
    R = P.R
    webs = []
    half = P.CW_HALF_ANGLE
    for s in (1, -1):
        y0, y1 = sorted((s * P.WEB_Y[0], s * P.WEB_Y[1]))
        hub = cyl_y(P.HUB_R, y0, y1)
        lobe = cyl_y(P.LOBE_R, y0, y1, z=R)
        arm = prism_xz([(-P.HUB_R, 0), (-P.LOBE_R, R), (P.LOBE_R, R), (P.HUB_R, 0)], y0, y1)
        cw = prism_xz(sector_pts(0, 0, lambda a: _cw_radius(a, r_flank), 180 - half, 180 + half, n=72), y0, y1)
        webs.append(fuse(hub, lobe, arm, cw))
    pin = cyl_y(P.PIN_JOURNAL_D / 2, -P.WEB_Y[0] - 0.5, P.WEB_Y[0] + 0.5, z=R)
    mains = [cyl_y(P.MAIN_D / 2, P.MAIN_Y[0] - 0.5, P.MAIN_Y[1] - P.AXIAL_CLEAR), cyl_y(P.MAIN_D / 2, -P.MAIN_Y[1] + P.AXIAL_CLEAR, -P.MAIN_Y[0] + 0.5)]
    gy0, gy1 = P.GEAR_Y
    sy0, sy1, sd = P.SEAL_JOURNAL
    rg = P.GEAR_M * P.GEAR_Z / 2
    gear = toothed_disc(0, 0, P.GEAR_Z, rg - 2.5, rg + 2.0, 0.34, 0.14, gy0, gy1, 0, 270.0)
    out_end = [cyl_y(P.OUT_NECK_D / 2, P.MAIN_Y[1] - P.AXIAL_CLEAR - 0.5, gy0 + 0.5), gear, cyl_y(sd / 2, sy0 - 0.5, sy1)]
    ly0, ly1, ld = P.SPROCKET_SEAT
    ty0, ty1, td = P.TRIGGER_SEAT
    ry0, ry1, rd = P.ROTOR_TAPER
    ey0, ey1, ed = P.ALT_END
    alt_end = [cyl_y(P.ALT_NECK_D / 2, -P.WALL_Y - 2.0, -P.MAIN_Y[1] + P.AXIAL_CLEAR + 0.5),
            cyl_y(ld / 2, ly1, ly0 + 0.5), cyl_y(td / 2, ty1, ty0 + 0.5), cyl_y(rd / 2, ry1, ry0 + 0.5), cyl_y(ed / 2, ey1, ey0 + 0.5)]
    shaft = fuse(*webs, pin, *mains, *out_end, *alt_end)
    for i in range(P.FLANGE_BOLT_N):
        a_ = 2 * math.pi * i / P.FLANGE_BOLT_N
        shaft = cut(shaft, cyl_y(P.FLANGE_BOLT_D / 2, sy1 - 14.0, sy1 + 1, x=P.FLANGE_MOUNT_PCD / 2 * math.cos(a_), z=P.FLANGE_MOUNT_PCD / 2 * math.sin(a_)))
    return shaft


def crank_moment_g_mm(shaft):
    """Net unbalance of the crank alone, g*mm; positive = heavy side opposite the pin (needed to balance)."""
    c = shaft.Center()
    return -P.RHO["steel"] * shaft.Volume() * c.z


# ------------------------------------------------------------------ toothed discs (gears, sprockets)
def toothed_disc(cx, cz, n, r_root, r_tip, half_root, half_tip, y0, y1, bore, phase_deg):
    pitch = 360.0 / n
    pts = []
    for i in range(n):
        a = phase_deg + i * pitch
        for da, r in ((-half_root * pitch, r_root), (-half_tip * pitch, r_tip), (half_tip * pitch, r_tip), (half_root * pitch, r_root)):
            aa = math.radians(a + da)
            pts.append((cx + r * math.sin(aa), cz + r * math.cos(aa)))
    s = prism_xz(pts, y0, y1)
    if not bore:
        return s
    return cut(s, cyl_y(bore / 2, y0 - 1, y1 + 1, x=cx, z=cz))


def output_flange():
    y0, y1, dia = P.FLANGE
    body = cyl_y(dia / 2, y0, y1)
    for i in range(P.FLANGE_BOLT_N):
        a = 2 * math.pi * i / P.FLANGE_BOLT_N
        body = cut(body, cyl_y(P.FLANGE_BOLT_D / 2 + 0.2, y0 - 1, y1 + 1, x=P.FLANGE_MOUNT_PCD / 2 * math.cos(a), z=P.FLANGE_MOUNT_PCD / 2 * math.sin(a)))
        b = a + math.pi / P.FLANGE_BOLT_N
        body = cut(body, cyl_y(P.FLANGE_BOLT_D / 2 + 0.2, y0 - 1, y1 + 1, x=P.FLANGE_BOLT_PCD / 2 * math.cos(b), z=P.FLANGE_BOLT_PCD / 2 * math.sin(b)))
    return body


def flange_bolt(i):
    a = 2 * math.pi * i / P.FLANGE_BOLT_N
    x, z = P.FLANGE_MOUNT_PCD / 2 * math.cos(a), P.FLANGE_MOUNT_PCD / 2 * math.sin(a)
    return fuse(cyl_y(P.FLANGE_BOLT_D / 2, P.FLANGE[1] - 24.0, P.FLANGE[1], x=x, z=z), cyl_y(6.5, P.FLANGE[1], P.FLANGE[1] + 5.5, x=x, z=z))


def balance_gear():
    r = P.GEAR_M * P.GEAR_Z / 2
    return toothed_disc(P.BAL_X, P.BAL_Z, P.GEAR_Z, r - 2.5, r + 2.0, 0.34, 0.14, P.GEAR_Y[0], P.GEAR_Y[1], P.BAL_SHAFT_D, 90.0 + 180.0 / P.GEAR_Z)


def _sprocket(n, bore, phase=0.0):
    p = P.CHAIN_PITCH
    pd = p / math.sin(math.pi / n)
    r_root = pd / 2 - 1.65
    r_tip = p * (0.6 + 1.0 / math.tan(math.pi / n)) / 2
    return pd, r_root, r_tip


def crank_sprocket():
    pd, rr, rt = _sprocket(P.SPROCKET_Z_CRANK, P.SPROCKET_SEAT[2])
    y0, y1 = P.SPROCKET_Y - 3.0, P.SPROCKET_Y + 3.0
    return toothed_disc(0, 0, P.SPROCKET_Z_CRANK, rr, rt, 0.30, 0.12, y0, y1, P.SPROCKET_SEAT[2], 0.0)


def cam_sprocket(side):
    pd, rr, rt = _sprocket(P.SPROCKET_Z_CAM, 22.0)
    y0, y1 = P.SPROCKET_Y - 3.0, P.SPROCKET_Y + 3.0
    cx = P.CAM_X * side
    return toothed_disc(cx, D["z_cam"], P.SPROCKET_Z_CAM, rr, rt, 0.30, 0.12, y0, y1, 22.0, 0.0)


def chain_hull(n_per_circle=90):
    import calc
    return calc.chain_hull(n_per_circle)


def chain():
    hull, per = chain_hull()
    y0, y1 = P.SPROCKET_Y - 3.5, P.SPROCKET_Y + 3.5
    w_out = cq.Wire.makePolygon([V(x, 0, z) for x, z in hull], close=True)
    outer = w_out.offset2D(4.8, "intersection")[0]
    inner = w_out.offset2D(1.9, "intersection")[0]
    fo = cq.Face.makeFromWires(outer)
    fi = cq.Face.makeFromWires(inner)
    so = cq.Solid.extrudeLinear(fo, V(0, y1 - y0, 0)).translate(V(0, y0, 0))
    si = cq.Solid.extrudeLinear(fi, V(0, y1 - y0 + 2, 0)).translate(V(0, y0 - 1, 0))
    return cut(so, si), per


# ------------------------------------------------------------------ balance shaft
def balance_shaft(t=14.6):
    shaft = cyl_y(P.BAL_SHAFT_D / 2, -72.0, 86.0, x=P.BAL_X, z=P.BAL_Z)
    parts = [shaft]
    for s in (1, -1):
        y0, y1 = sorted((s * P.BAL_WEIGHT_Y0, s * (P.BAL_WEIGHT_Y0 + t)))
        parts.append(prism_xz(sector_pts(P.BAL_X, P.BAL_Z, lambda a: P.BAL_WEIGHT_R, 90, 270, n=60), y0, y1))
    return fuse(*parts)


def balance_moment_g_mm(shaft):
    c = shaft.Center()
    return -P.RHO["steel"] * shaft.Volume() * (c.z - P.BAL_Z)


if __name__ == "__main__":
    import time
    for name, fn in (("piston", lambda: piston(4.0)), ("pin", piston_pin), ("rod", conrod), ("cap", rod_cap), ("bolt", rod_bolt),
                     ("crank", crank), ("bal", balance_shaft), ("bal_gear", balance_gear),
                     ("crank_sprocket", crank_sprocket)):
        t0 = time.time()
        s = fn()
        print("%-15s solids %d valid %s vol %.0f mm3  bbox %s  (%.1fs)" % (name, n_solids(s), s.isValid(), vol(s), bbox(s), time.time() - t0))
