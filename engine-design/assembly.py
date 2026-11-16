"""
Builds every part at the assembled pose, solves the dependent dimensions (piston dome for the compression ratio,
crank counterweights and balance weights for balance), and returns the part list with metadata.
"""
import math
import numpy as np
import cadquery as cq
import params as P
import calc
import p_rotating as R
import p_static as S
import p_valve as VT
import p_misc as M
from cadutil import *

D = P.derived()
RHO = dict(al7075=2.81e-3, al6061=2.70e-3, al2618=2.76e-3, steel=7.85e-3, ti=4.43e-3, bronze=8.8e-3, trimetal=7.4e-3,
           elec=5.5e-3, rubber=1.2e-3, mlsteel=7.85e-3)

# part id -> name, group, material, rho, process, source, step, explode (mm at full explode)
META = {
    "upper_case": ("Upper crankcase", "structure", "Al 7075-T6", "al7075", "CNC 5-axis + line bore", "make", 1, (0, 0, 0)),
    "bedplate": ("Bedplate (main caps)", "structure", "Al 7075-T6", "al7075", "CNC + line bore with upper case", "make", 4, (0, 0, -90)),
    "oil_pan": ("Oil pan", "structure", "Al 6061-T6", "al6061", "CNC 3-axis", "make", 12, (0, 0, -150)),
    "liner": ("Cylinder liner (wet)", "structure", "42CrMo4, nitrided", "steel", "CNC turning, nitride, hone", "make", 6, (0, 0, 150)),
    "barrel": ("Cylinder barrel", "structure", "Al 7075-T6", "al7075", "CNC turn-mill", "make", 6, (0, 0, 100)),
    "head_gasket": ("Head gasket (MLS)", "structure", "Stainless MLS, 3 layers", "mlsteel", "Laser cut, buy", "buy", 6, (0, 0, 130)),
    "head": ("Cylinder head", "structure", "Al 7075-T6", "al7075", "CNC 5-axis", "make", 7, (0, 0, 170)),
    "cam_ladder": ("Cam ladder (bearing caps)", "structure", "Al 7075-T6", "al7075", "CNC 3-axis", "make", 8, (0, 0, 330)),
    "cam_cover": ("Cam cover", "structure", "Al 6061-T6", "al6061", "CNC 3-axis", "make", 9, (0, 0, 400)),
    "cover_chain": ("Chain and alternator cover (bike's right side)", "structure", "Al 6061-T6", "al6061", "CNC 3-axis", "make", 11, (0, -230, 0)),
    "cover_gear": ("Gear and pump cover (bike's left side)", "structure", "Al 6061-T6", "al6061", "CNC 3-axis", "make", 10, (0, 110, 0)),
    "pump_cover": ("Water pump cover", "structure", "Al 6061-T6", "al6061", "CNC 3-axis", "make", 10, (0, 190, 0)),
    "crankshaft": ("Crankshaft (one piece)", "rotating", "42CrMo4, nitrided", "steel", "CNC 5-axis, heat treat, grind", "make", 3, (0, 0, -55)),
    "conrod": ("Connecting rod", "rotating", "42CrMo4, shot-peened", "steel", "CNC 5-axis, hone", "make", 2, (0, 0, -55)),
    "rod_cap": ("Rod cap", "rotating", "42CrMo4, shot-peened", "steel", "CNC 5-axis, hone", "make", 2, (0, 0, -70)),
    "rod_bolt": ("Rod bolt 7/16-20", "rotating", "Premium alloy steel", "steel", "Buy (ARP-type)", "buy", 2, (0, 0, -90)),
    "rod_shell_upper": ("Rod shell, upper", "rotating", "Tri-metal", "trimetal", "Buy", "buy", 2, (0, 0, -55)),
    "rod_shell_lower": ("Rod shell, lower", "rotating", "Tri-metal", "trimetal", "Buy", "buy", 2, (0, 0, -70)),
    "small_end_bush": ("Small-end bush", "rotating", "Bronze", "bronze", "Buy", "buy", 2, (0, 0, -55)),
    "main_shell_upper": ("Main shell, upper", "rotating", "Tri-metal", "trimetal", "Buy", "buy", 1, (0, 0, -10)),
    "main_shell_lower": ("Main shell, lower", "rotating", "Tri-metal", "trimetal", "Buy", "buy", 4, (0, 0, -75)),
    "bal_shell_upper": ("Balance shaft shell, upper", "rotating", "Tri-metal", "trimetal", "Buy", "buy", 1, (0, 0, -10)),
    "bal_shell_lower": ("Balance shaft shell, lower", "rotating", "Tri-metal", "trimetal", "Buy", "buy", 4, (0, 0, -75)),
    "piston": ("Piston (forged)", "rotating", "Al 2618 forged", "al2618", "Buy (custom forging)", "buy", 5, (0, 0, 60)),
    "piston_pin": ("Piston pin", "rotating", "Case-hardened steel, DLC", "steel", "Buy", "buy", 5, (0, 90, 60)),
    "ring_top": ("Top ring", "rotating", "Steel, nitrided", "steel", "Buy", "buy", 5, (0, 0, 75)),
    "ring_second": ("Second ring", "rotating", "Cast iron", "steel", "Buy", "buy", 5, (0, 0, 85)),
    "ring_oil": ("Oil ring", "rotating", "Steel rails + expander", "steel", "Buy", "buy", 5, (0, 0, 95)),
    "balance_shaft": ("Balance shaft", "rotating", "42CrMo4, nitrided", "steel", "CNC turn-mill, grind", "make", 3, (0, 0, -55)),
    "output_flange": ("Output flange (bolt-on)", "rotating", "42CrMo4", "steel", "CNC turn-mill", "make", 10, (0, 150, 0)),
    "flange_bolt": ("Output flange bolt M8", "hardware", "12.9 steel", "steel", "Buy", "buy", 10, (0, 190, 0)),
    "balance_gear": ("Balance gear (46T, m2)", "drive", "Case-hardened steel", "steel", "CNC + grind", "make", 10, (0, 60, -20)),
    "crank_sprocket": ("Crank sprocket (14T)", "drive", "Steel, hardened", "steel", "CNC", "make", 11, (0, -60, 0)),
    "cam_sprocket": ("Cam sprocket (28T)", "drive", "Steel, hardened", "steel", "CNC", "make", 11, (0, -60, 330)),
    "chain": ("Cam roller chain 04C", "drive", "Roller chain", "steel", "Buy", "buy", 11, (0, -95, 0)),
    "chain_guide": ("Chain guide", "drive", "Steel + polymer pad", "steel", "CNC", "make", 11, (0, -95, 0)),
    "chain_tensioner": ("Chain tensioner", "drive", "Steel + spring", "steel", "Buy / CNC", "buy", 11, (0, -95, 0)),
    "intake_cam": ("Intake camshaft", "valvetrain", "Steel, DLC", "steel", "CNC, harden, grind", "make", 8, (0, 0, 290)),
    "exhaust_cam": ("Exhaust camshaft", "valvetrain", "Steel, DLC", "steel", "CNC, harden, grind", "make", 8, (0, 0, 290)),
    "valve_intake": ("Intake valve", "valvetrain", "Ti-6Al-4V", "ti", "Buy (custom)", "buy", 7, (0, 0, 130)),
    "valve_exhaust": ("Exhaust valve", "valvetrain", "Ti-6Al-4V, coated", "ti", "Buy (custom)", "buy", 7, (0, 0, 130)),
    "spring_outer": ("Valve spring, outer", "valvetrain", "Cr-Si wire, peened", "steel", "Buy (custom)", "buy", 7, (0, 0, 215)),
    "spring_inner": ("Valve spring, inner", "valvetrain", "Cr-Si wire, peened", "steel", "Buy (custom)", "buy", 7, (0, 0, 225)),
    "retainer": ("Spring retainer", "valvetrain", "Ti-6Al-4V", "ti", "Buy", "buy", 7, (0, 0, 245)),
    "keepers": ("Keepers", "valvetrain", "Steel", "steel", "Buy", "buy", 7, (0, 0, 255)),
    "lash_cap": ("Lash cap (shim)", "valvetrain", "Steel, hardened", "steel", "Buy", "buy", 8, (0, 0, 270)),
    "follower": ("Finger follower", "valvetrain", "Steel, DLC", "steel", "CNC, grind", "make", 8, (0, 0, 280)),
    "follower_shaft": ("Follower pivot shaft", "valvetrain", "Steel, ground", "steel", "Buy / CNC", "buy", 8, (0, 0, 275)),
    "spark_plug": ("Spark plug M10", "ignition", "Iridium", "steel", "Buy", "buy", 9, (0, 0, 460)),
    "spark_coil": ("Coil-on-plug", "ignition", "-", "elec", "Buy", "buy", 9, (0, 0, 520)),
    "trigger_wheel": ("Trigger wheel (36-2)", "ignition", "Steel", "steel", "CNC", "make", 11, (0, -110, 0)),
    "alt_rotor": ("Alternator rotor", "ignition", "Steel + magnets", "elec", "Buy", "buy", 11, (0, -160, 0)),
    "alt_stator": ("Alternator stator", "ignition", "Laminations + copper", "elec", "Buy", "buy", 11, (0, -125, 0)),
    "water_impeller": ("Water pump impeller", "fluids", "Al 6061", "al6061", "CNC", "make", 10, (0, 140, 0)),
    "oil_rotor_inner": ("Oil pump inner rotor", "fluids", "Sintered steel", "steel", "Buy", "buy", 11, (0, -75, 0)),
    "oil_rotor_outer": ("Oil pump outer rotor", "fluids", "Sintered steel", "steel", "Buy", "buy", 11, (0, -75, 0)),
    "oil_filter": ("Oil filter (spin-on)", "fluids", "-", "steel", "Buy", "buy", 12, (70, 0, 0)),
    "throttle_body": ("Throttle body 44 mm", "intake", "Al", "al6061", "Buy", "buy", 12, (-80, 0, 0)),
    "stud": ("Head stud M10 x 228", "hardware", "12.9 steel", "steel", "Buy", "buy", 7, (0, 0, 300)),
    "nut_m10": ("Nut M10", "hardware", "12.9 steel", "steel", "Buy", "buy", 7, (0, 0, 330)),
    "washer_m10": ("Washer M10", "hardware", "Hardened steel", "steel", "Buy", "buy", 7, (0, 0, 315)),
    "bolt_m10_main": ("Main cap bolt M10", "hardware", "12.9 steel", "steel", "Buy", "buy", 4, (0, 0, -100)),
    "bolt_m8_case": ("Case bolt M8", "hardware", "12.9 steel", "steel", "Buy", "buy", 4, (0, 0, -100)),
    "bolt_m6_pan": ("Oil pan bolt M6", "hardware", "10.9 steel", "steel", "Buy", "buy", 12, (0, 0, -170)),
    "bolt_m6_ladder": ("Ladder bolt M6", "hardware", "10.9 steel", "steel", "Buy", "buy", 8, (0, 0, 360)),
}
MASS_OVERRIDE_G = {}     # part id -> mass per piece in g, when the solid is a simplified stand-in


def _split_rod_masses(rod, cap, bolts, bush):
    """Two-mass model of the connecting rod about its centre of gravity (kg)."""
    items = [(rod, RHO["steel"]), (cap, RHO["steel"])] + [(b, RHO["steel"]) for b in bolts]
    m = 0.0
    mz = 0.0
    for s, rho in items:
        mi = s.Volume() * rho * 1e-3
        m += mi
        mz += mi * s.Center().z
    zcg = mz / m
    m_small = m * (zcg - P.R) / P.ROD
    return dict(total=m, m_small=m_small, m_big=m - m_small, zcg=zcg)


def solve_piston(log):
    lo, hi = 1.8, 5.2
    best = None
    for _ in range(14):
        g = 0.5 * (lo + hi)
        pis = R.piston(g)
        vc = chamber_volume(g) + 600.0             # +0.6 cc seat recesses, plug thread, gasket gap
        cr = (P.VD_CC * 1000.0 + vc) / vc
        best = (g, cr, vc, pis)
        if cr > P.CR_TARGET:
            lo = g
        else:
            hi = g
    log("piston crown gap %.2f mm -> chamber %.2f cc, CR %.2f" % (best[0], best[2] / 1000, best[1]))
    return best


def chamber_volume(g):
    zlo = R.GROOVE_TOP_Z
    zhi = D["z_ridge"] + 1.0
    tent = prism_xz([(-48, zlo), (-48, S._roof_z(-48)), (0, D["z_ridge"]), (48, S._roof_z(48)), (48, zlo)], -50, 50)
    region = common(tent, cyl_z(P.BORE / 2, zlo, zhi))
    return region.Volume() - common(region, R.crown_envelope(g)).Volume()


def solve_crank(target_g_mm, log):
    lo, hi = 48.0, P.CW_R_FLANK_MAX
    c_hi = R.crank(hi)
    if R.crank_moment_g_mm(c_hi) < target_g_mm:
        log("WARNING: counterweights at max radius give %.0f g*mm, target %.0f" % (R.crank_moment_g_mm(c_hi), target_g_mm))
        return hi, c_hi
    best = (hi, c_hi)
    for _ in range(10):
        mid = 0.5 * (lo + hi)
        c = R.crank(mid)
        if R.crank_moment_g_mm(c) >= target_g_mm:
            hi, best = mid, (mid, c)
        else:
            lo = mid
    log("crank counterweight flank radius %.1f mm (moment %.0f g*mm, target %.0f)" % (best[0], R.crank_moment_g_mm(best[1]), target_g_mm))
    return best


def solve_balance(target_g_mm, log):
    lo, hi = 8.0, 24.0
    for _ in range(12):
        mid = 0.5 * (lo + hi)
        if R.balance_moment_g_mm(R.balance_shaft(mid)) >= target_g_mm:
            hi = mid
        else:
            lo = mid
    t = round(hi + 0.05, 2)
    log("balance weight thickness %.2f mm (each), moment %.0f g*mm, target %.0f" % (t, R.balance_moment_g_mm(R.balance_shaft(t)), target_g_mm))
    return t


def build(log=print):
    ctx = {}
    # ---- piston group and rod
    g, cr, vc, pis = solve_piston(log)
    pin = R.piston_pin()
    rings = R.piston_rings()
    rod, cap = R.conrod(), R.rod_cap()
    bolts = [R.rod_bolt(), R.rod_bolt().mirror("YZ")]
    bush = R.small_end_bush()
    sh_u, sh_l = R.rod_shells()
    m_pis = pis.Volume() * RHO["al2618"] * 1e-3
    m_pin = pin.Volume() * RHO["steel"] * 1e-3
    m_rings = sum(r.Volume() for r in rings) * RHO["steel"] * 1e-3
    m_clips = 0.004
    m_bush = bush.Volume() * RHO["bronze"] * 1e-3
    sp = _split_rod_masses(rod, cap, bolts, bush)
    m_shells = (sh_u.Volume() + sh_l.Volume()) * RHO["trimetal"] * 1e-3
    piston_group = m_pis + m_pin + m_rings + m_clips + m_bush
    m_rec = piston_group + sp["m_small"]
    m_rot = sp["m_big"] + m_shells
    log("masses: piston %.0f g, pin %.0f g, rings %.0f g, rod total %.0f g (small-end share %.0f g), bush %.0f g" %
        (m_pis * 1000, m_pin * 1000, m_rings * 1000, sp["total"] * 1000, sp["m_small"] * 1000, m_bush * 1000))
    log("reciprocating %.0f g, rotating (big end + shells) %.0f g" % (m_rec * 1000, m_rot * 1000))
    ctx.update(g=g, cr=cr, vc=vc, m_rec=m_rec, m_rot=m_rot, piston_group=piston_group, rod_split=sp, m_pis=m_pis, m_pin=m_pin)
    # ---- crank and balance shaft
    cw_t, bal_t = calc.balance_targets(m_rec, m_rot)
    flank, crank = solve_crank(cw_t * 1000.0, log)
    P.BAL_T = solve_balance(bal_t * 1000.0, log)
    bal = R.balance_shaft(P.BAL_T)
    ctx.update(flank=flank, bal_t=P.BAL_T, crank_moment=R.crank_moment_g_mm(crank), bal_moment=R.balance_moment_g_mm(bal), cw_target=cw_t * 1000, bal_target=bal_t * 1000)
    # ---- valvetrain design from CAD masses
    vcad = {}
    for kind, name in (("in", "valve_in"), ("ex", "valve_ex")):
        vv = [v for v in D["valves"] if v["kind"] == kind][0]
        vcad[name] = VT.valve(kind, vv["side"]).Volume() * RHO["ti"]
    vv0 = D["valves"][0]
    ret = VT.retainer(vv0).Volume() * RHO["ti"]
    fol = VT.follower("in", 1)
    pivot = np.array([-P.PIVOT_X, fol.Center().y, VT.Z_P])
    cg = np.array([fol.Center().x, fol.Center().y, fol.Center().z])
    lever = D["tip_x"] - P.PIVOT_X
    fol_g = fol.Volume() * RHO["steel"]
    r_cg = abs(cg[0] - pivot[0])
    vcad.update(retainer=ret, keepers=VT.keepers(vv0).Volume() * RHO["steel"], lash_cap=VT.lash_cap(vv0).Volume() * RHO["steel"],
                follower_eff=fol_g * (r_cg / lever) ** 2 * 1.25)
    ctx["valve_masses"] = vcad
    designs = {k: VT.spring_design(k, vcad) for k in ("in", "ex")}
    ctx["designs"] = designs
    ctx["cad_for_calc"] = dict(vc_mm3=vc, piston_group_kg=piston_group, rod_kg=sp["total"], rod_small_frac=sp["m_small"] / sp["total"],
                               rod_shells_kg=m_shells, cap_kg=(cap.Volume() + sum(b.Volume() for b in bolts)) * RHO["steel"] * 1e-3, crank_moment_kgmm=ctx["crank_moment"] / 1000,
                               bal_moment_kgmm=ctx["bal_moment"] / 1000, valve_masses=vcad)
    return ctx, dict(pis=pis, pin=pin, rings=rings, rod=rod, cap=cap, bolts=bolts, bush=bush, sh_u=sh_u, sh_l=sh_l, crank=crank, bal=bal)


def mirror_y(shape):
    return shape.mirror("XZ")


def instances(ctx, rot):
    """List of dicts: part id, instance label, shape."""
    out = []

    def add(pid, shape, label=None):
        out.append(dict(part=pid, label=label or pid, shape=shape))
    sh_u, sh_l = rot["sh_u"], rot["sh_l"]
    ms_u, ms_l = R.main_shells()
    # structure
    add("upper_case", S.upper_case())
    add("bedplate", S.bedplate())
    add("oil_pan", S.oil_pan())
    add("liner", S.liner())
    add("barrel", S.barrel())
    add("head_gasket", S.head_gasket())
    add("head", S.head())
    add("cam_ladder", S.cam_ladder())
    add("cam_cover", S.cam_cover())
    add("cover_chain", S.cover_chain())
    add("cover_gear", S.cover_gear())
    add("pump_cover", S.pump_cover())
    # rotating
    add("crankshaft", rot["crank"])
    add("conrod", rot["rod"])
    add("rod_cap", rot["cap"])
    add("rod_bolt", rot["bolts"][0], "rod_bolt#1")
    add("rod_bolt", rot["bolts"][1], "rod_bolt#2")
    add("rod_shell_upper", sh_u)
    add("rod_shell_lower", sh_l)
    add("small_end_bush", rot["bush"])
    for k, s in enumerate((ms_u, mirror_y(ms_u))):
        add("main_shell_upper", s, "main_shell_upper#%d" % (k + 1))
    for k, s in enumerate((ms_l, mirror_y(ms_l))):
        add("main_shell_lower", s, "main_shell_lower#%d" % (k + 1))
    bu, bl = M.bal_shells()
    for k, s in enumerate((bu, mirror_y(bu))):
        add("bal_shell_upper", s, "bal_shell_upper#%d" % (k + 1))
    for k, s in enumerate((bl, mirror_y(bl))):
        add("bal_shell_lower", s, "bal_shell_lower#%d" % (k + 1))
    add("piston", rot["pis"])
    add("piston_pin", rot["pin"])
    for pid, s in zip(("ring_top", "ring_second", "ring_oil"), rot["rings"]):
        add(pid, s)
    add("balance_shaft", rot["bal"])
    add("output_flange", R.output_flange())
    for k in range(P.FLANGE_BOLT_N):
        add("flange_bolt", R.flange_bolt(k), "flange_bolt#%d" % (k + 1))
    add("balance_gear", R.balance_gear())
    add("crank_sprocket", R.crank_sprocket())
    for k, side in enumerate((1, -1)):
        add("cam_sprocket", R.cam_sprocket(side), "cam_sprocket#%d" % (k + 1))
    ch, per = R.chain()
    add("chain", ch)
    g, t = M.chain_guide_tensioner()
    add("chain_guide", g)
    add("chain_tensioner", t)
    # valvetrain
    add("intake_cam", VT.cam("in"))
    add("exhaust_cam", VT.cam("ex"))
    for kind, vpid in (("in", "valve_intake"), ("ex", "valve_exhaust")):
        dsg = ctx["designs"][kind]
        for vv in [v for v in D["valves"] if v["kind"] == kind]:
            tag = "%s#%s" % (kind, "L" if vv["side"] > 0 else "R")
            add(vpid, VT.valve(kind, vv["side"]), "%s_%s" % (vpid, tag))
            o, i = VT.spring_pair(dsg, vv)
            add("spring_outer", o, "spring_outer_%s" % tag)
            add("spring_inner", i, "spring_inner_%s" % tag)
            add("retainer", VT.retainer(vv), "retainer_%s" % tag)
            add("keepers", VT.keepers(vv), "keepers_%s" % tag)
            add("lash_cap", VT.lash_cap(vv), "lash_cap_%s" % tag)
            add("follower", VT.follower(kind, vv["side"]), "follower_%s" % tag)
    add("follower_shaft", VT.follower_shaft(-1), "follower_shaft#1")
    add("follower_shaft", VT.follower_shaft(1), "follower_shaft#2")
    # fluids, ignition, intake
    add("water_impeller", M.water_impeller())
    gi, go = M.gerotor_pair()
    add("oil_rotor_inner", gi)
    add("oil_rotor_outer", go)
    add("oil_filter", M.oil_filter())
    add("throttle_body", M.throttle_body())
    add("spark_plug", M.spark_plug())
    add("spark_coil", M.spark_coil())
    add("trigger_wheel", M.trigger_wheel())
    add("alt_rotor", M.alt_rotor())
    add("alt_stator", M.alt_stator())
    # hardware
    for k, (x, y) in enumerate(S.STUDS):
        add("stud", M.stud().translate(V(x, y, 0)), "stud#%d" % (k + 1))
        add("nut_m10", M.nut_m10().translate(V(x, y, 0)), "nut_m10#%d" % (k + 1))
        add("washer_m10", M.washer_m10().translate(V(x, y, 0)), "washer_m10#%d" % (k + 1))
    for k, pos in enumerate(S.BOLTS_M10):
        add("bolt_m10_main", M.bolt_m10_main(pos), "bolt_m10_main#%d" % (k + 1))
    for k, pos in enumerate(S.BOLTS_M8):
        add("bolt_m8_case", M.bolt_m8_case(pos), "bolt_m8_case#%d" % (k + 1))
    for k, pos in enumerate(S.BOLTS_PAN):
        add("bolt_m6_pan", M.bolt_m6_pan(pos), "bolt_m6_pan#%d" % (k + 1))
    for k, pos in enumerate(S.LADDER_BOLTS):
        add("bolt_m6_ladder", M.bolt_m6_ladder(pos), "bolt_m6_ladder#%d" % (k + 1))
    return out, per


if __name__ == "__main__":
    import time
    t0 = time.time()
    ctx, rot = build()
    print("solve time %.1fs" % (time.time() - t0))
    t0 = time.time()
    inst, per = instances(ctx, rot)
    print("%d instances built in %.1fs; chain path %.0f mm" % (len(inst), time.time() - t0, per))
    bad = [i["label"] for i in inst if not i["shape"].isValid()]
    print("invalid:", bad)
