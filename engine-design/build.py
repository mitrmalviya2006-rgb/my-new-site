#!/usr/bin/env python3
"""
Builds the whole engine, runs every check, and writes: engine.step, parts/*.step, bom.csv, interface.json,
results.json, mesh.json.  Run:  python build.py   (needs numpy, cadquery)
"""
import base64
import csv
import json
import math
import os
import sys
import time

import numpy as np
import cadquery as cq

import assembly
import calc
import checks
import p_misc as M
import p_rotating as R
import p_static as S
import params as P
from cadutil import *

OUT = os.path.dirname(os.path.abspath(__file__))
D = P.derived()
T0 = time.time()
LOG = []


def log(*a):
    msg = " ".join(str(x) for x in a)
    LOG.append(msg)
    print("[%5.0fs] %s" % (time.time() - T0, msg), flush=True)


ZC_TOP = D["z_cam"] + 36.0
GROUP_COLOR = {"structure": (0.62, 0.64, 0.68), "rotating": (0.85, 0.55, 0.25), "drive": (0.35, 0.55, 0.85), "valvetrain": (0.30, 0.70, 0.50),
               "ignition": (0.75, 0.35, 0.65), "fluids": (0.30, 0.65, 0.85), "intake": (0.55, 0.55, 0.60), "hardware": (0.45, 0.45, 0.48)}


def piece_mass_g(inst, ctx, links):
    pid, label, shape = inst["part"], inst["label"], inst["shape"]
    rho = assembly.RHO[assembly.META[pid][3]]
    vol = shape.Volume()
    if pid in ("spring_outer", "spring_inner"):
        kind = "in" if "_in#" in label else "ex"
        key = "outer" if pid == "spring_outer" else "inner"
        return ctx["designs"][kind]["spring"][key]["mass"]
    if pid == "chain":
        return 0.37 * links * P.CHAIN_PITCH
    if pid == "alt_rotor":
        return vol * rho * 0.9
    if pid == "alt_stator":
        return vol * rho * 0.7
    if pid == "oil_filter":
        return 300.0
    if pid == "head_gasket":
        return vol * rho * 0.6
    return vol * rho


def main():
    log("building parts and solving piston, crank and balance weights")
    ctx, rot = assembly.build(log=log)
    inst, per = assembly.instances(ctx, rot)
    links = int(round(per / P.CHAIN_PITCH / 2.0)) * 2
    log("%d solids built; chain path %.0f mm = %d links" % (len(inst), per, links))
    by = {}
    for i in inst:
        by[i["label"]] = i["shape"]
        by.setdefault(i["part"], i["shape"])

    # ------------------------------------------------------------ physics with CAD masses
    res = calc.run(cad=ctx["cad_for_calc"])
    chk = res["checks"]

    def add(name, value, limit, ok, unit="", note=""):
        chk.append(dict(name=name, value=value, limit=limit, ok=bool(ok), unit=unit, note=note))

    # ------------------------------------------------------------ CAD checks
    # swept volume from CAD geometry: bore from a slice of the liner, stroke from the crank pin position
    slab = common(by["liner"], box(-60, 60, -60, 60, 100.0, 101.0))
    area = slab.Volume()
    r_out = P.LINER_OD / 2
    r_in = math.sqrt(r_out ** 2 - area / math.pi)
    pin_slice = common(by["crankshaft"], box(-60, 60, -1, 1, -60, 60))
    r_pin = pin_slice.Center().z
    vsw = math.pi * r_in ** 2 * 2 * r_pin / 1000.0
    add("Swept volume from CAD (bore %.2f mm x stroke %.2f mm)" % (2 * r_in, 2 * r_pin), vsw, 349.0, abs(vsw - 349.0) <= 0.5, "cc", "liner slice and crank pin offset")
    add("Compression ratio from CAD volumes", ctx["cr"], P.CR_TARGET, abs(ctx["cr"] - P.CR_TARGET) <= 0.2, "", "chamber %.2f cc, crown gap %.2f mm" % (ctx["vc"] / 1000, ctx["g"]))
    cw_ok = ctx["crank_moment"] >= 0.97 * ctx["cw_target"]
    add("Crank counterweight moment vs target", ctx["crank_moment"], ctx["cw_target"], cw_ok, "g*mm", "flank radius %.1f mm" % ctx["flank"])
    add("Balance weight moment vs target", ctx["bal_moment"], ctx["bal_target"], ctx["bal_moment"] >= 0.97 * ctx["bal_target"], "g*mm", "%.1f mm thick each" % ctx["bal_t"])

    log("overlap check of the assembled engine")
    hits = checks.overlap_report(inst, log=log)
    add("Overlaps between parts (assembled pose)", len(hits), 0, len(hits) == 0, "pairs", "intersection volume > 1 mm3")

    log("motion sweep every 10 degrees")
    worst = checks.sweep_motion(by, steps=range(0, 360, 10), log=log)
    nmot = sum(1 for v in worst.values() if v[0] > 1.0)
    add("Moving parts vs case and liner, 36 crank angles", nmot, 0, nmot == 0, "interferences", "crank, rod, bolts, piston, balance shaft")

    log("minimum clearances")
    statics = ["upper_case", "bedplate", "oil_pan", "liner"]
    mind = {}
    for th in range(0, 360, 30):
        d = th - 360.0
        moving = {"crank": [checks.rot_shape(by["crankshaft"], d)],
                  "rod": [checks.rod_pose(by[k], th) for k in ("conrod", "rod_cap", "rod_bolt#1", "rod_bolt#2")]}
        for mn, mv in moving.items():
            for sn in statics:
                for sh in mv:
                    dd = sh.distance(by[sn])
                    if (mn, sn) not in mind or dd < mind[(mn, sn)]:
                        mind[(mn, sn)] = dd
    crank_gap = min(v for k, v in mind.items() if k[0] == "crank")
    rod_gap = min(v for k, v in mind.items() if k[0] == "rod")
    res["clearances"] = {"%s vs %s" % k: round(v, 2) for k, v in mind.items()}
    add("Minimum gap, crank to case", crank_gap, 0.3, crank_gap >= 0.3, "mm", "axial gap to bulkheads is the smallest")
    add("Minimum gap, rod and bolts to case", rod_gap, 1.0, rod_gap >= 1.0, "mm", "sweep at 30 degree steps")

    log("piston to valve clearance")
    pv, worst_pv = checks.piston_valve_clearance(by, d_range=range(-80, 81, 10), log=log)
    add("Piston to valve clearance through overlap", worst_pv[4], 1.5, worst_pv[4] >= 1.5, "mm", "worst at crank angle %d deg" % worst_pv[0])
    res["piston_valve"] = [dict(theta=r[0], kind=r[1], side=r[2], lift=r[3], clearance=r[4]) for r in pv]

    log("assembly insertion sweeps")
    ins_rows = run_insertion(inst, log)
    nblocked = sum(1 for r in ins_rows if not r["ok"])
    add("Assembly moves without interference", len(ins_rows) - nblocked, len(ins_rows), nblocked == 0, "of %d" % len(ins_rows), "each part or sub-assembly slid in along one straight line")
    res["insertion"] = ins_rows

    # ------------------------------------------------------------ masses, centre of gravity, BOM
    rows = {}
    mtot, mx, my, mz = 0.0, 0.0, 0.0, 0.0
    for i in inst:
        g = piece_mass_g(i, ctx, links)
        c = i["shape"].Center()
        mtot += g
        mx += g * c.x
        my += g * c.y
        mz += g * c.z
        i["mass_g"] = g
        r = rows.setdefault(i["part"], dict(qty=0, mass_each=g, total=0.0))
        r["qty"] += 1
        r["total"] += g
    mass_dry = mtot / 1000.0
    fluids = (P.OIL_L * 0.87 + P.COOLANT_L * 1.05)
    cg = (mx / mtot, my / mtot, mz / mtot)
    res["mass"] = dict(dry_kg=mass_dry, oil_l=P.OIL_L, coolant_l=P.COOLANT_L, wet_kg=mass_dry + fluids, cg=cg)
    log("engine dry mass %.1f kg, wet %.1f kg, CG %s" % (mass_dry, mass_dry + fluids, tuple(round(c, 1) for c in cg)))
    add("Engine mass (dry, no radiator, exhaust, ECU)", mass_dry, 40.0, mass_dry <= 40.0, "kg", "target from the chassis: 60 kg including ancillaries")

    bom = []
    for pid, r in rows.items():
        name, group, mat, rk, proc, src, step, ex = assembly.META[pid]
        if pid == "chain":
            name = "Cam roller chain 04C, %d links" % links
        bom.append(dict(id=pid, name=name, group=group, material=mat, process=proc, source=src, step=step, qty=r["qty"],
                        mass_each_g=round(r["mass_each"], 1), mass_total_g=round(r["total"], 1)))
    bom.sort(key=lambda b: (b["group"], b["step"], b["id"]))
    with open(os.path.join(OUT, "bom.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["part_id", "name", "group", "material", "process", "make_or_buy", "assembly_step", "qty", "mass_each_g", "mass_total_g"])
        for b in bom:
            w.writerow([b["id"], b["name"], b["group"], b["material"], b["process"], b["source"], b["step"], b["qty"], b["mass_each_g"], b["mass_total_g"]])
    n_make = sum(1 for b in bom if b["source"] == "make")
    log("BOM: %d unique parts (%d to machine, %d to buy), %d pieces modelled" % (len(bom), n_make, len(bom) - n_make, len(inst)))
    res["bom"] = bom
    res["counts"] = dict(unique=len(bom), make=n_make, buy=len(bom) - n_make, pieces=len(inst))

    # ------------------------------------------------------------ exports
    log("exporting STEP")
    os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)
    assy = cq.Assembly(name="engine_349cc")
    for i in inst:
        col = GROUP_COLOR[assembly.META[i["part"]][1]]
        assy.add(i["shape"], name=i["label"], color=cq.Color(col[0], col[1], col[2], 1.0))
    assy.save(os.path.join(OUT, "engine.step"))
    for pid, shape in ((i["part"], i["shape"]) for i in inst):
        if assembly.META[pid][5] == "make" and not os.path.exists(os.path.join(OUT, "parts", pid + ".step")) or False:
            pass
    done = set()
    for i in inst:
        pid = i["part"]
        if assembly.META[pid][5] == "make" and pid not in done:
            done.add(pid)
            cq.exporters.export(cq.Workplane("XY").newObject([i["shape"]]), os.path.join(OUT, "parts", pid + ".step"))
    log("%d part STEP files written" % len(done))

    # interface for the chassis
    def merged(pids):
        bbs = [i["shape"].BoundingBox() for i in inst if i["part"] in pids]
        return dict(x=[min(b.xmin for b in bbs), max(b.xmax for b in bbs)], y=[min(b.ymin for b in bbs), max(b.ymax for b in bbs)],
                    z=[min(b.zmin for b in bbs), max(b.zmax for b in bbs)])
    X0, X1 = P.CASE_X
    def bx(x0, x1, y0, y1, z0, z1):
        return dict(x=[x0, x1], y=[y0, y1], z=[z0, z1])
    boxes = {
        "case": bx(X0, X1 + 14.0, -62.0, 62.0, -106.0, 62.0),
        "filter": bx(X1 + 14.0, X1 + 69.0, -31.0, 31.0, -106.0, -44.0),
        "rear_boss": bx(X0, X0 + 26.0, -82.0, 82.0, 62.0, 92.0),
        "cover_chain_plate": bx(X0, X1, -80.0, -62.0, -106.0, 63.0),
        "cover_chain_strip": bx(-48.0, 48.0, -80.0, -62.0, 63.0, 150.0),
        "cover_chain_head": bx(-70.0, 70.0, -80.0, -62.0, 150.0, ZC_TOP),
        "alt_bulge": bx(-78.0, 78.0, -126.0, -80.0, -78.0, 78.0),
        "cover_gear": bx(-150.0, 58.0, 62.0, 88.0, -58.0, 58.0),
        "pump_cover": bx(-126.0, -58.0, 88.0, 118.0, -34.0, 34.0),
        "flange": bx(-36.0, 36.0, 88.0, 106.0, -36.0, 36.0),
        "head_block": bx(-78.0, 94.0, -62.0, 62.0, 62.0, ZC_TOP),
        "front_ears": bx(70.0, 94.0, -82.0, 82.0, S.LUG_UPPER[1] - 14.0, S.LUG_UPPER[1] + 14.0),
        "intake": bx(-135.0, -62.0, -28.0, 28.0, 172.0, 228.0),
        "exhaust_stub": bx(70.0, 100.0, -20.0, 20.0, 165.0, 205.0),
        "coil": bx(-10.0, 10.0, -10.0, 10.0, 205.0, ZC_TOP + 4.0),
    }
    allb = merged(tuple(assembly.META.keys()))
    iface = dict(boxes=boxes, envelope=allb, mounts=dict(
        upper=dict(x=S.LUG_UPPER[0], z=S.LUG_UPPER[1], y_inner=S.LUG_Y[0], y_outer=S.LUG_Y[1], hole_d=14.0),
        rear=dict(x=S.LUG_LOWER[0], z=S.LUG_LOWER[1], y_inner=S.LUG_Y[0], y_outer=S.LUG_Y[1], hole_d=14.0)),
        mass_dry_kg=mass_dry, mass_wet_kg=mass_dry + fluids, cg=cg, crank_axis=(0, 0, 0), output_flange_y=[P.FLANGE[0], P.FLANGE[1]],
        exhaust_flange=dict(x=P.HEAD_X, z=185.0), intake_flange=dict(x=-P.HEAD_X, z=200.0), note="engine frame: x forward, y left, z up, origin = crank axis; +y = output side (bike's left), -y = alternator side (bike's right)")

    log("tessellating for the viewer")
    mesh = tessellate_all(inst)
    iface["boxes"], grown = grow_boxes(iface["boxes"], mesh["meshes"])
    log("interface boxes enclose every mesh vertex; boxes that had to grow (mm): %s" % (grown or "none"))
    json.dump(iface, open(os.path.join(OUT, "interface.json"), "w"), indent=1)
    json.dump(mesh, open(os.path.join(OUT, "mesh.json"), "w"), separators=(",", ":"))
    log("mesh.json %.1f MB, %d triangles" % (os.path.getsize(os.path.join(OUT, "mesh.json")) / 1e6, sum(m["tris"] for m in mesh["meshes"])))

    # ------------------------------------------------------------ results
    res["ctx"] = dict(piston_gap=ctx["g"], chamber_cc=ctx["vc"] / 1000, cr=ctx["cr"], flank=ctx["flank"], bal_t=ctx["bal_t"], m_rec=ctx["m_rec"],
                      m_rot=ctx["m_rot"], crank_moment=ctx["crank_moment"], bal_moment=ctx["bal_moment"], cw_target=ctx["cw_target"],
                      bal_target=ctx["bal_target"], piston_group=ctx["piston_group"], rod=ctx["rod_split"],
                      swept_cc=vsw, bore_cad=2 * r_in, stroke_cad=2 * r_pin, chain_links=links, chain_path=per)
    res["interface"] = iface
    res["envelope"] = allb
    res["steps"] = STEP_TEXT
    res["checks"] = chk
    res["log"] = LOG
    json.dump(res, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
    nfail = [c for c in chk if not c["ok"]]
    log("checks: %d total, %d failing" % (len(chk), len(nfail)))
    for c in nfail:
        log("  FAIL: %s = %s (limit %s) %s" % (c["name"], c["value"], c["limit"], c["note"]))
    return 0


STEP_TEXT = {
    1: "Upper case on a stand. Press the upper main shells and balance-shaft shells into their saddles.",
    2: "On the bench: fit the rod shells and bush, bolt the rod cap onto the crank pin with the two 7/16 rod bolts.",
    3: "Lower the crank and rod from below into the upper case, then the balance shaft (weights down).",
    4: "Fit the lower shells, set the bedplate on the upper case (add two dowel pins here in the real build, not modelled yet), fit and torque the M10 main-cap bolts and M8 case bolts.",
    5: "Set the piston on the rod small end from above, push the pin in from the side, fit the rings.",
    6: "Press the liner into the barrel, lower the barrel over the piston (ring compressor), then the head gasket.",
    7: "Head with valves, springs, retainers and keepers built on the bench; lower it onto the four studs, washers and nuts.",
    8: "Set the four followers on the valve tips, slide in the pivot shafts, lower the cams, fit the ladder and its bolts.",
    9: "Cam cover, spark plug and coil.",
    10: "Output side (+y, the bike's left): balance gear onto the shaft, water impeller, gear cover and pump cover, then the output flange.",
    11: "Alternator side (-y, the bike's right): oil pump rotors, crank sprocket, cam sprockets, chain with master link, guide, tensioner, trigger wheel, rotor, chain and alternator cover with stator.",
    12: "Oil pan, oil filter and throttle body.",
}


def run_insertion(inst, log):
    def sh(*pids):
        return [i["shape"] for i in inst if i["part"] in pids]
    ROD = ("conrod", "rod_cap", "rod_bolt", "rod_shell_upper", "rod_shell_lower", "small_end_bush")
    CRANKSET = ("crankshaft",) + ROD
    HEAD_ASM = ("head_gasket", "head", "valve_intake", "valve_exhaust", "spring_outer", "spring_inner", "retainer", "keepers", "lash_cap")
    steps = [
        ("Crank and rod up into the upper case", sh(*CRANKSET), sh("upper_case", "main_shell_upper", "bal_shell_upper", "balance_shaft"), (0, 0, -1), 150),
        ("Balance shaft up into the upper case", sh("balance_shaft"), sh("upper_case", "main_shell_upper", "bal_shell_upper", *CRANKSET), (0, 0, -1), 120),
        ("Bedplate with lower shells up", sh("bedplate", "main_shell_lower", "bal_shell_lower"), sh("upper_case", "main_shell_upper", "bal_shell_upper", "balance_shaft", *CRANKSET), (0, 0, -1), 100),
        ("Piston and rings down onto the rod", sh("piston", "ring_top", "ring_second", "ring_oil"), sh("upper_case", "bedplate", *CRANKSET, "balance_shaft"), (0, 0, 1), 120),
        ("Piston pin in from the side", sh("piston_pin"), sh("piston", "conrod", "small_end_bush", "ring_top", "ring_second", "ring_oil"), (0, 1, 0), 90),
        ("Barrel and liner down over the piston", sh("barrel", "liner"), sh("upper_case", "piston", "piston_pin", "ring_top", "ring_second", "ring_oil", *CRANKSET, "stud"), (0, 0, 1), 170),
        ("Gasket and built-up head down onto the studs", sh(*HEAD_ASM), sh("barrel", "liner", "upper_case", "piston", "ring_top", "stud"), (0, 0, 1), 150),
        ("Followers down onto the valve tips", sh("follower"), sh("head", "valve_intake", "valve_exhaust", "lash_cap", "retainer", "keepers", "stud", "nut_m10", "washer_m10"), (0, 0, 1), 60),
        ("Follower shafts in from the side", sh("follower_shaft"), sh("follower", "head"), (0, 1, 0), 70),
        ("Cams down into the saddles", sh("intake_cam", "exhaust_cam"), sh("head", "follower", "follower_shaft", "nut_m10", "stud", "valve_intake", "valve_exhaust"), (0, 0, 1), 70),
        ("Cam ladder down", sh("cam_ladder"), sh("head", "intake_cam", "exhaust_cam", "follower", "follower_shaft", "nut_m10", "stud"), (0, 0, 1), 60),
        ("Cam cover down", sh("cam_cover"), sh("cam_ladder", "intake_cam", "exhaust_cam", "head", "bolt_m6_ladder"), (0, 0, 1), 70),
        ("Spark plug and coil down the well", sh("spark_plug", "spark_coil"), sh("head", "cam_ladder", "cam_cover"), (0, 0, 1), 130),
        ("Balance gear onto the shaft from the output side", sh("balance_gear"), sh("upper_case", "bedplate", "balance_shaft", "crankshaft", "bal_shell_upper", "bal_shell_lower"), (0, 1, 0), 60),
        ("Water impeller onto the shaft from the output side", sh("water_impeller"), sh("upper_case", "balance_shaft", "balance_gear", "crankshaft"), (0, 1, 0), 50),
        ("Gear cover over the crank end", sh("cover_gear"), sh("upper_case", "bedplate", "crankshaft", "balance_shaft", "balance_gear", "water_impeller"), (0, 1, 0), 150),
        ("Pump cover", sh("pump_cover"), sh("cover_gear", "balance_shaft", "water_impeller"), (0, 1, 0), 80),
        ("Output flange from the output side", sh("output_flange"), sh("crankshaft", "cover_gear"), (0, 1, 0), 70),
        ("Crank sprocket onto the alternator end", sh("crank_sprocket"), sh("crankshaft", "upper_case"), (0, -1, 0), 60),
        ("Cam sprockets onto the cam ends", sh("cam_sprocket"), sh("intake_cam", "exhaust_cam", "head", "cam_cover"), (0, -1, 0), 60),
        ("Trigger wheel and rotor", sh("trigger_wheel", "alt_rotor"), sh("crankshaft", "crank_sprocket", "upper_case"), (0, -1, 0), 80),
        ("Chain and alternator cover with stator", sh("cover_chain", "alt_stator"), sh("upper_case", "bedplate", "head", "cam_cover", "crankshaft", "crank_sprocket", "cam_sprocket", "trigger_wheel", "alt_rotor", "chain", "chain_guide", "chain_tensioner", "barrel", "oil_rotor_inner", "oil_rotor_outer", "balance_shaft"), (0, -1, 0), 220),
        ("Oil pan up", sh("oil_pan"), sh("bedplate", "crankshaft", "conrod", "rod_cap", "rod_bolt", "bolt_m10_main", "bolt_m8_case", "upper_case"), (0, 0, -1), 100),
    ]
    rows = []
    for name, mv, st, d, start in steps:
        v, off = checks.insertion_sweep(mv, st, d, start)
        rows.append(dict(step=name, worst_mm3=round(v, 1), ok=v <= 1.0, direction=list(d), start_mm=start))
    log("insertion sweeps: %d moves, %d blocked" % (len(rows), sum(1 for r in rows if not r["ok"])))
    return rows


def decode_mesh(m):
    """positions of one quantised mesh entry, in the engine frame (mm)"""
    q = np.frombuffer(base64.b64decode(m["v"]), dtype=np.uint16).reshape(-1, 3).astype(np.float64)
    return np.array(m["lo"]) + q / 65535.0 * np.array(m["span"])


def grow_boxes(boxes, meshes, pad=0.5):
    """Make the chassis clearance boxes self-verifying: any mesh vertex outside every box pulls the nearest box out to it
    (plus pad mm). Returns the new boxes and how far each one had to grow."""
    keys = list(boxes)
    lo = np.array([[boxes[k]["x"][0], boxes[k]["y"][0], boxes[k]["z"][0]] for k in keys], dtype=np.float64)
    hi = np.array([[boxes[k]["x"][1], boxes[k]["y"][1], boxes[k]["z"][1]] for k in keys], dtype=np.float64)
    lo0, hi0 = lo.copy(), hi.copy()
    for m in meshes:
        Pt = decode_mesh(m)
        for _ in range(3):       # a grown box can swallow more vertices; a few passes settle it
            d = np.maximum(np.maximum(lo[None, :, :] - Pt[:, None, :], Pt[:, None, :] - hi[None, :, :]), 0.0)
            dist = np.linalg.norm(d, axis=2)
            dmin, near = dist.min(axis=1), dist.argmin(axis=1)
            out = np.where(dmin > 1e-6)[0]
            if len(out) == 0:
                break
            for ix in out:
                k = near[ix]
                lo[k] = np.minimum(lo[k], Pt[ix] - pad)
                hi[k] = np.maximum(hi[k], Pt[ix] + pad)
    grown = {}
    new = {}
    for n, k in enumerate(keys):
        new[k] = dict(x=[round(float(lo[n, 0]), 2), round(float(hi[n, 0]), 2)], y=[round(float(lo[n, 1]), 2), round(float(hi[n, 1]), 2)],
                      z=[round(float(lo[n, 2]), 2), round(float(hi[n, 2]), 2)])
        g = float(max((lo0[n] - lo[n]).max(), (hi[n] - hi0[n]).max()))
        if g > 1e-6:
            grown[k] = round(g, 2)
    return new, grown


def tessellate_all(inst, tol=0.35, ang=0.25):
    meshes = []
    for i in inst:
        pid = i["part"]
        verts, tris = i["shape"].tessellate(tol, ang)
        v = np.array([(p.x, p.y, p.z) for p in verts], dtype=np.float64)
        t = np.array(tris, dtype=np.int64)
        if len(v) == 0:
            continue
        lo, hi = v.min(axis=0), v.max(axis=0)
        span = np.where(hi - lo > 1e-9, hi - lo, 1.0)
        q = np.round((v - lo) / span * 65535).astype(np.uint16)
        idx = t.astype(np.uint16) if len(v) < 65536 else t.astype(np.uint32)
        name, group, mat, rk, proc, src, step, ex = assembly.META[pid]
        meshes.append(dict(label=i["label"], part=pid, name=name, group=group, material=mat, process=proc, source=src, step=step,
                           explode=list(ex), mass_g=round(i.get("mass_g", 0.0), 1), lo=[round(float(x), 3) for x in lo],
                           span=[round(float(x), 3) for x in span], v=base64.b64encode(q.tobytes()).decode(),
                           i=base64.b64encode(idx.tobytes()).decode(), it="u2" if idx.dtype == np.uint16 else "u4",
                           tris=int(len(t)), nv=int(len(v))))
    return dict(meshes=meshes)


if __name__ == "__main__":
    sys.exit(main())
