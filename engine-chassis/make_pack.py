#!/usr/bin/env python3
"""
Make-the-chassis pack: cut-ready 3D model and everything a fabricator needs.

Run after frame.py:   python make_pack.py        (needs numpy, cadquery, ezdxf, matplotlib)
Writes make-pack/:
  chassis_cut_ready.step   every tube coped at both ends (separate named solids), plates with tube holes, spacers (frame only)
  tubes/<id>.step          one coped tube each, straight along Z in its own frame (for tube-laser shops)
  tubes/<id>.dxf           the unrolled (flat) tube with both coped ends
  plates.dxf               plate flat patterns with the tube holes
  notch_templates.pdf      1:1 wrap-around templates for hand coping
  drawings.pdf             A3 drawings, scale 1:4
  tube_table.csv, BOM.csv, jig_table.csv, jig_table.dxf, results_pack.json

All geometry comes from frame.py (same nodes, members, sizes), so it always matches the solver.
Coping rule: a tube is coped onto every tube at that node that has a larger diameter, or the same diameter and
a lower index (so exactly one of two equal tubes is cut).
"""
import csv
import itertools
import json
import math
import os

import numpy as np

import cadquery as cq
import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import frame as fr

OUT = os.path.join(fr.OUT, "make-pack")
os.makedirs(os.path.join(OUT, "tubes"), exist_ok=True)

# ------------------------------------------------------------------ the design (same pipeline as frame.main)
pos = fr.build_nodes()
names = list(pos)
members = fr.base_members()
sizes, loads, info, sol = fr.size_members(names, pos, members, lambda sz: fr.masses(pos, members, sz))
rows = fr.member_table(names, pos, members, sizes, sol, loads)
for i, r in enumerate(rows):
    r["idx"] = i
    r["key"] = (-r["od"], i)                       # priority: larger diameter first, then lower index
    r["safe"] = r["id"].replace("-", "_")
at_node = {}
for r in rows:
    at_node.setdefault(r["a"], []).append(r)
    at_node.setdefault(r["b"], []).append(r)

SHOW_ENGINE_REF = False        # the pack is the frame only; set True to add the engine clearance boxes to the STEP and the drawings
PLATE_KINDS = {"LUG": (70, 90, 6, 13), "PIVOT": (110, 150, 6, 0), "PEG": (50, 60, 6, 10), "SHOCK": (60, 80, 6, 12)}
T_PL = 6.0
R_OUT = fr.TUBES["M"][0] / 2 + T_PL / 2 + 1       # plate centre sits this far inboard of its node (as in frame.py)
V = lambda p: cq.Vector(float(p[0]), float(p[1]), float(p[2]))


def geom(r):
    pa, pb = pos[r["a"]], pos[r["b"]]
    L = float(np.linalg.norm(pb - pa))
    u = (pb - pa) / L
    ref = np.array([0.0, 0.0, 1.0]) if abs(u[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
    e1 = ref - (ref @ u) * u
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(u, e1)
    return pa, pb, L, u, e1, e2


def neighbours(r, node):
    """Higher-priority tubes at this node that r must be coped onto. A tube that leaves the node on the far side
    (obtuse angle, so it points away from r) does not touch r's end and is ignored."""
    other = r["b"] if r["a"] == node else r["a"]
    uu = pos[other] - pos[node]
    uu = uu / np.linalg.norm(uu)
    out = []
    for o in at_node[node]:
        if o is r or not o["key"] < r["key"]:
            continue
        on = o["b"] if o["a"] == node else o["a"]
        w = pos[on] - pos[node]
        w = w / np.linalg.norm(w)
        if float(uu @ w) >= 0.0:
            out.append(o)
    return out


def end_curve(r, end, n=181):
    """Distance s(phi) from the node plane to where the coped tube surface starts, for phi = 0..360 deg."""
    pa, pb, L, u, e1, e2 = geom(r)
    node, other = (r["a"], r["b"]) if end == "A" else (r["b"], r["a"])
    uu = u if end == "A" else -u                         # axis direction pointing from the node into the tube
    R = r["od"] / 2
    phis = np.linspace(0, 2 * math.pi, n)
    S = np.zeros(n)
    nbs = neighbours(r, node)
    for k, ph in enumerate(phis):
        c = math.cos(ph) * e1 + math.sin(ph) * e2
        ivs = []
        for o in nbs:
            on = o["b"] if o["a"] == node else o["a"]
            w = pos[on] - pos[node]
            w /= np.linalg.norm(w)
            Ro = o["od"] / 2
            al = float(uu @ w)
            be = R * float(c @ w)
            A = 1 - al * al
            if A < 1e-9:
                continue
            B = -2 * al * be
            C = R * R - be * be - Ro * Ro
            disc = B * B - 4 * A * C
            if disc <= 0:
                continue
            sq = math.sqrt(disc)
            ivs.append(((-B - sq) / (2 * A), (-B + sq) / (2 * A)))
        s = 0.0
        changed = True
        while changed:
            changed = False
            for lo, hi in ivs:
                if lo <= s + 1e-9 and hi > s + 1e-9:
                    s = hi
                    changed = True
        S[k] = s
    return phis, S


for r in rows:
    pa_, pb_, L_, u_, e1_, e2_ = geom(r)
    r["L"] = L_
    for end in "AB":
        ph, S = end_curve(r, end)
        r["curve" + end] = (ph, S)
    r["smin"] = [float(r["curveA"][1].min()), float(r["curveB"][1].min())]
    r["smax"] = [float(r["curveA"][1].max()), float(r["curveB"][1].max())]
    r["long"] = L_ - r["smin"][0] - r["smin"][1]            # tip of end A to tip of end B (they need not be on the same line)
    r["short"] = L_ - float((r["curveA"][1] + r["curveB"][1]).max())   # shortest line along the tube


# ------------------------------------------------------------------ cut-ready CAD
def cyl(p, d, length, radius):
    return cq.Solid.makeCylinder(radius, length, V(p), V(d))


def tube_solid(r, coped=True):
    pa, pb, L, u, e1, e2 = geom(r)
    R, w = r["od"] / 2, r["wall"]
    t = cyl(pa, u, L, R).cut(cyl(pa, u, L, R - w))
    if not coped:
        return t
    for node in (r["a"], r["b"]):
        cutters = []
        for o in neighbours(r, node):
            on = o["b"] if o["a"] == node else o["a"]
            w_ = pos[on] - pos[node]
            w_ /= np.linalg.norm(w_)
            back = 1.5 * (o["od"] / 2 + R)
            cutters.append(cyl(pos[node] - w_ * back, w_, back + 150.0, o["od"] / 2))
        for c in cutters:                                 # one tool at a time: multi-tool cuts failed silently on some nodes
            t2 = t.cut(c)
            if t2.isValid():
                t = t2
    return t


def plate_layout():
    """List of (kind, node, side, centre xyz). Plates sit 'inboard' of their node, like frame.py."""
    out = []
    for sfx in "LR":
        s = 1 if sfx == "L" else -1
        for n in ("E", "F"):
            out.append(("LUG", n + sfx, s))
        out.append(("PIVOT", "D" + sfx, s))
        out.append(("PEG", "P" + sfx, s))
    out.append(("SHOCK", "M", 0))
    return out


def plate_holes(node, yc):
    """Ellipses where tube axes pierce the plate plane y = yc (centre, semi-major, semi-minor, angle) in x,z."""
    holes = []
    for o in at_node[node]:
        other = o["b"] if o["a"] == node else o["a"]
        d = pos[other] - pos[node]
        L = np.linalg.norm(d)
        u = d / L
        if abs(u[1]) < 1e-6:
            continue
        t = (yc - pos[node][1]) / u[1]
        if not (0 < t < min(L, 90.0)):                   # tubes crossing the plate plane farther out run alongside it, clear of the plate
            continue
        c = pos[node] + u * t
        R = o["od"] / 2
        cos_t = abs(u[1])
        a = R / cos_t
        ang = math.atan2(u[2], u[0])
        holes.append(dict(cx=float(c[0]), cz=float(c[2]), a=a, b=R, ang=ang, tube=o["id"]))
    return holes


def ellipse_pts(h, n=48):
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = h["a"] * np.cos(th)
    z = h["b"] * np.sin(th)
    ca, sa = math.cos(h["ang"]), math.sin(h["ang"])
    return np.c_[h["cx"] + x * ca - z * sa, h["cz"] + x * sa + z * ca]


plates = []
for kind, node, s in plate_layout():
    p = pos[node]
    wd, ht, t, hole = PLATE_KINDS[kind]
    yc = p[1] - s * R_OUT if s else p[1]
    if kind == "PEG":                                   # peg plate goes on the outboard side of its node: no tube pierces it
        yc = p[1] + s * (8.0 + T_PL / 2)
    holes = plate_holes(node, yc) if kind not in ("SHOCK", "PEG") else []
    if holes:
        pts = np.vstack([ellipse_pts(h) for h in holes])
        ext_x = max(abs(pts[:, 0] - p[0]).max(), wd / 2 - 10)
        ext_z = max(abs(pts[:, 1] - p[2]).max(), ht / 2 - 10)
        wd = math.ceil((2 * ext_x + 20) / 5) * 5
        ht = math.ceil((2 * ext_z + 20) / 5) * 5
    plates.append(dict(kind=kind, node=node, s=s, yc=float(yc), w=wd, h=ht, t=t, hole=hole, holes=holes, c=p))


def plate_solid(pl, with_tubes=True):
    p = pl["c"]
    box = cq.Solid.makeBox(pl["w"], pl["t"], pl["h"], cq.Vector(p[0] - pl["w"] / 2, pl["yc"] - pl["t"] / 2, p[2] - pl["h"] / 2))
    if pl["hole"]:
        box = box.cut(cq.Solid.makeCylinder(pl["hole"] / 2, pl["t"] + 2, cq.Vector(p[0], pl["yc"] - pl["t"] / 2 - 1, p[2]), cq.Vector(0, 1, 0)))
    if with_tubes:
        for o in at_node.get(pl["node"], []):
            if o["id"] in [h["tube"] for h in pl["holes"]]:
                box = box.cut(tube_solid(o, coped=False).fuse(cyl(pos[o["a"]], geom(o)[3], geom(o)[2], o["od"] / 2 - o["wall"])))
    return box


def spacer_solid(node, s):
    p = pos[node]
    y_in = abs(p[1]) - R_OUT - T_PL / 2
    L = y_in - fr.EAR_OUTER_Y
    sp = cq.Solid.makeCylinder(fr.SPACER_OD / 2, L, cq.Vector(p[0], s * fr.EAR_OUTER_Y, p[2]), cq.Vector(0, s, 0))
    return sp.cut(cq.Solid.makeCylinder(fr.SPACER_ID / 2, L + 2, cq.Vector(p[0], s * (fr.EAR_OUTER_Y - 1), p[2]), cq.Vector(0, s, 0))), L


def build_cad():
    assy = cq.Assembly(name="chassis_cut_ready")
    solids = {}
    for r in rows:
        t = tube_solid(r)
        solids[r["id"]] = t
        col = cq.Color(0.3, 0.3, 0.35, 1) if r["size"] == "H" else cq.Color(0.55, 0.57, 0.62, 1)
        assy.add(t, name="TUBE_" + r["id"], color=col)
    for pl in plates:
        assy.add(plate_solid(pl), name="PLATE_%s_%s" % (pl["kind"], pl["node"]), color=cq.Color(0.9, 0.55, 0.1, 1))
    spacer_len = None
    for sfx in "LR":
        s = 1 if sfx == "L" else -1
        for n in ("E", "F"):
            sp, spacer_len = spacer_solid(n + sfx, s)
            assy.add(sp, name="SPACER_%s%s" % (n, sfx), color=cq.Color(0.9, 0.55, 0.1, 1))
    for bname, b in (fr.ENGINE_BOXES.items() if SHOW_ENGINE_REF else []):
        assy.add(cq.Solid.makeBox(b["x"][1] - b["x"][0], b["y"][1] - b["y"][0], b["z"][1] - b["z"][0], cq.Vector(b["x"][0], b["y"][0], b["z"][0])),
                 name="REFERENCE_ENGINE_BOX_%s" % bname, color=cq.Color(0.2, 0.5, 0.9, 0.3))
    assy.save(os.path.join(OUT, "chassis_cut_ready.step"))
    return solids, spacer_len


solids, SPACER_LEN = build_cad()
print("cut-ready STEP written")

# ------------------------------------------------------------------ per-tube files (straight along Z, own frame)
check_rows = []
for r in rows:
    pa, pb, L, u, e1, e2 = geom(r)
    loc = cq.Location(cq.Plane(origin=V(pa), xDir=V(e1), normal=V(u)))
    local = solids[r["id"]].moved(loc.inverse)
    cq.exporters.export(cq.Workplane("XY").newObject([local]), os.path.join(OUT, "tubes", r["safe"] + ".step"))
    verts, _ = local.tessellate(0.05, 0.05)           # outer-surface points only (the inside edge of a coped wall is longer)
    P = np.array([[v.x, v.y, v.z] for v in verts])
    outer = P[np.hypot(P[:, 0], P[:, 1]) > r["od"] / 2 - 0.05]
    long_cad = float(outer[:, 2].max() - outer[:, 2].min())
    check_rows.append((r["id"], r["long"], long_cad))
    # flat pattern: x = R*phi, y along the tube (end A at the bottom)
    R = r["od"] / 2
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    phA, SA = r["curveA"]
    phB, SB = r["curveB"]
    lo = [(R * float(p_), float(s_)) for p_, s_ in zip(phA, SA)]
    hi = [(R * float(p_), float(r["L"] - s_)) for p_, s_ in zip(phB, SB)]
    msp.add_lwpolyline(lo)
    msp.add_lwpolyline(hi)
    msp.add_line(lo[0], hi[0])
    msp.add_line(lo[-1], hi[-1])
    msp.add_text("%s  %gx%g  long side %.1f  short side %.1f  (flat pattern, width = %.1f = pi x OD; edge x=0 is the reference line)" % (
        r["id"], r["od"], r["wall"], r["long"], r["short"], math.pi * r["od"]), height=4, dxfattribs={"insert": (0, -10)})
    doc.saveas(os.path.join(OUT, "tubes", r["safe"] + ".dxf"))
worst = max(abs(a - b) for _, a, b in check_rows)
print("tube long-side length (outer surface), analytic vs CAD: worst difference %.3f mm" % worst)

# ------------------------------------------------------------------ plates.dxf (one pattern per distinct plate, viewed from outside +y)
doc = ezdxf.new("R2010")
doc.units = ezdxf.units.MM
msp = doc.modelspace()
ox = 0.0
seen = {}
for pl in plates:
    key = (pl["kind"], pl["node"].rstrip("LR"))
    seen.setdefault(key, []).append(pl["node"])
done = set()
for pl in plates:
    key = (pl["kind"], pl["node"].rstrip("LR"))
    if key in done:
        continue
    done.add(key)
    p = pl["c"]
    x0, z0 = p[0] - pl["w"] / 2, p[2] - pl["h"] / 2
    msp.add_lwpolyline([(ox, 0), (ox + pl["w"], 0), (ox + pl["w"], pl["h"]), (ox, pl["h"])], close=True)
    if pl["hole"]:
        msp.add_circle((ox + pl["w"] / 2, pl["h"] / 2), pl["hole"] / 2)
    for h in pl["holes"]:
        pts = ellipse_pts(h, 90)
        msp.add_lwpolyline([(ox + (x - x0), (z - z0)) for x, z in pts], close=True)
    msp.add_text("%s at %s: %.0f x %.0f x %.0f mm, bolt hole %s, %d tube holes (qty %d)" % (
        pl["kind"], "/".join(seen[key]), pl["w"], pl["h"], pl["t"], ("d%g" % pl["hole"]) if pl["hole"] else "none",
        len(pl["holes"]), len(seen[key])), height=5, dxfattribs={"insert": (ox, -14)})
    ox += pl["w"] + 60
doc.saveas(os.path.join(OUT, "plates.dxf"))
print("plates.dxf written")

# ------------------------------------------------------------------ tube table, BOM
with open(os.path.join(OUT, "tube_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "tube_mm", "centreline_mm", "long_side_mm (cut to this, square)", "short_side_mm", "end_A_node", "end_A_depth_mm", "end_B_node", "end_B_depth_mm",
                "end_A_coped_onto", "end_B_coped_onto"])
    for r in rows:
        w.writerow([r["id"], "%gx%g" % (r["od"], r["wall"]), "%.1f" % r["L"], "%.1f" % r["long"], "%.1f" % r["short"],
                    r["a"], "%.1f" % (r["smax"][0] - r["smin"][0]), r["b"], "%.1f" % (r["smax"][1] - r["smin"][1]),
                    "+".join(o["id"] for o in neighbours(r, r["a"])) or "(flat end)", "+".join(o["id"] for o in neighbours(r, r["b"])) or "(flat end)"])


def nest(lengths, stock=6000.0, kerf=3.0):
    bins = []
    for L in sorted(lengths, reverse=True):
        for b in bins:
            if b["left"] >= L + kerf:
                b["left"] -= L + kerf
                b["cuts"].append(L)
                break
        else:
            bins.append(dict(left=stock - L - kerf, cuts=[L]))
    return bins


bom = []
tot_mass = 0.0
for key, (od, wall) in fr.TUBES.items():
    sel = [r for r in rows if r["size"] == key]
    if not sel:
        continue
    bins = nest([r["long"] for r in sel])
    area = math.pi / 4 * (od ** 2 - (od - 2 * wall) ** 2)
    m = sum(r["long"] for r in sel) * area * fr.RHO
    tot_mass += m
    bom.append(["Tube ERW mild steel %gx%g mm" % (od, wall), len(sel), "%.0f mm cut lengths in total" % sum(r["long"] for r in sel),
                "%d x 6 m stock length(s) (first-fit nesting, 3 mm kerf)" % len(bins), "%.2f kg" % m])
pl_counts = {}
pl_mass = 0.0
for pl in plates:
    k = (pl["kind"], pl["node"].rstrip("LR"), pl["w"], pl["h"], pl["t"])
    pl_counts[k] = pl_counts.get(k, 0) + 1
    pl_mass += pl["w"] * pl["h"] * pl["t"] * fr.RHO
for (kind, node, wd, ht, t), q in pl_counts.items():
    bom.append(["Plate %s (%s) mild steel, laser cut from plates.dxf" % (kind, node), q, "%.0f x %.0f x %.0f mm" % (wd, ht, t), "", "%.2f kg each (before holes)" % (wd * ht * t * fr.RHO)])
sp_area = math.pi / 4 * (fr.SPACER_OD ** 2 - fr.SPACER_ID ** 2)
bom.append(["Spacer tube %g/%g mm" % (fr.SPACER_OD, fr.SPACER_ID), 4, "%.1f mm long (cut square)" % SPACER_LEN, "", "%.2f kg each" % (sp_area * SPACER_LEN * fr.RHO)])
bom.append(["Bolt M12 x 90 (grade 8.8) with lock nut and 2 washers", 4, "engine mounts E and F, both sides", "", ""])
bom.append(["Filler wire / rod for mild steel (ER70S-6 or equivalent)", 1, "about 0.5 kg", "", ""])
bom.append(["Powder coat or paint", 1, "after weld inspection", "", ""])
with open(os.path.join(OUT, "BOM.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["item", "qty", "size / note", "stock", "mass"])
    w.writerows(bom)

# ------------------------------------------------------------------ jig table (node posts on a flat table)
zmin = min(p[2] for p in pos.values())
xmin = min(p[0] for p in pos.values())
ymid = 0.0
with open(os.path.join(OUT, "jig_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["node", "table_x_mm", "table_y_mm", "height_above_table_mm (node centre)", "frame x", "frame y", "frame z"])
    for n, p in pos.items():
        w.writerow([n, "%.1f" % (p[0] - xmin), "%.1f" % (p[1]), "%.1f" % (p[2] - zmin + 50), "%.1f" % p[0], "%.1f" % p[1], "%.1f" % p[2]])
doc = ezdxf.new("R2010")
doc.units = ezdxf.units.MM
msp = doc.modelspace()
for n, p in pos.items():
    x, y = p[0] - xmin, p[1]
    msp.add_circle((x, y), 6)
    msp.add_line((x - 12, y), (x + 12, y))
    msp.add_line((x, y - 12), (x, y + 12))
    msp.add_text("%s  h=%.0f" % (n, p[2] - zmin + 50), height=7, dxfattribs={"insert": (x + 9, y + 9)})
for r in rows:
    a, b = pos[r["a"]], pos[r["b"]]
    msp.add_line((a[0] - xmin, a[1]), (b[0] - xmin, b[1]))
doc.saveas(os.path.join(OUT, "jig_table.dxf"))

# inspection diagonals: straight-line distances between node pairs that are not members
diag = []
for a, b in [("HT", "DL"), ("HT", "DR"), ("HB", "DL"), ("HB", "DR"), ("EL", "ER"), ("FL", "FR"), ("CL", "CR"), ("SL", "SR"), ("SL", "DR"), ("SR", "DL"),
             ("EL", "FR"), ("ER", "FL"), ("PL", "PR"), ("CL", "SR"), ("CR", "SL"), ("EL", "DL"), ("ER", "DR"), ("HT", "CL"), ("HT", "CR")]:
    diag.append((a, b, float(np.linalg.norm(pos[a] - pos[b]))))

# ------------------------------------------------------------------ notch templates (1:1)
A4 = (210.0, 297.0)
pdf = PdfPages(os.path.join(OUT, "notch_templates.pdf"))


def new_page():
    fig = plt.figure(figsize=(A4[0] / 25.4, A4[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, A4[0])
    ax.set_ylim(0, A4[1])
    ax.axis("off")
    return fig, ax


def finish(fig, ax, pageno):
    ax.plot([10, 60], [8, 8], "k-", lw=1)
    ax.plot([10, 10], [6, 10], "k-", lw=1)
    ax.plot([60, 60], [6, 10], "k-", lw=1)
    ax.text(62, 7, "<- this bar must measure 50 mm when printed. Print at 100% / actual size (no 'fit to page').", fontsize=6, va="center")
    ax.text(200, 7, "p%d" % pageno, fontsize=6, ha="right")
    pdf.savefig(fig)
    plt.close(fig)


page = 1
fig, ax = new_page()
ytop = 285.0
ax.text(10, ytop, "Tube notch (fishmouth) templates, 1:1", fontsize=11, weight="bold")
for i, line in enumerate([
        "How to use: 1) cut the tube square to the LONG SIDE length. 2) Draw a straight line along the tube; this is the reference line (0 deg).",
        "3) Cut out the template, put its straight bottom edge flush with the tube end, its left edge on the reference line, and wrap it round the tube",
        "clockwise as seen looking at that end, printed side out (end B templates are already mirrored). 4) Trace the curve, cut away the shaded part.",
        "Ends marked FLAT are cut square: other tubes are coped onto them. Notch depth is measured from the long point of the end."]):
    ax.text(10, ytop - 8 - 5 * i, line, fontsize=6.5)
y = ytop - 36
for r in rows:
    R = r["od"] / 2
    circ = 2 * math.pi * R
    blocks = []
    for end in "AB":
        ph, S = r["curve" + end]
        d = S - S.min()
        if d.max() < 0.3:
            continue
        blocks.append((end, ph, d))
    if not blocks:
        continue
    hmax = max(b[2].max() for b in blocks) + 18
    if y - hmax < 18:
        finish(fig, ax, page)
        page += 1
        fig, ax = new_page()
        y = ytop
    x0 = 12.0
    ax.text(x0, y, "%s  %gx%g mm   long side %.1f mm   short side %.1f mm   %s" % (r["id"], r["od"], r["wall"], r["long"], r["short"],
            "ends: " + ", ".join("%s=%s" % (e, r["a"] if e == "A" else r["b"]) for e, _, _ in blocks)), fontsize=7, weight="bold")
    for end, ph, d in blocks:
        xs = R * ph if end == "A" else R * (2 * math.pi - ph)
        order = np.argsort(xs)
        xs, dd = xs[order], d[order]
        yb = y - 6 - d.max() - 3
        ax.plot([x0, x0 + circ, x0 + circ, x0, x0], [yb, yb, yb + d.max() + 3, yb + d.max() + 3, yb], "k-", lw=0.6)
        ax.fill_between(x0 + xs, yb, yb + dd, color="0.8")
        ax.plot(x0 + xs, yb + dd, "k-", lw=0.9)
        for q, lab in ((0, "0"), (0.25, "90"), (0.5, "180"), (0.75, "270"), (1.0, "360")):
            ax.plot([x0 + q * circ] * 2, [yb, yb + 2], "k-", lw=0.5)
            ax.text(x0 + q * circ, yb - 3, lab, fontsize=5, ha="center")
        ax.text(x0, yb + d.max() + 4.5, "end %s (node %s), depth %.1f mm" % (end, r["a"] if end == "A" else r["b"], d.max()), fontsize=6)
        x0 += circ + 14
    y -= hmax + 14
finish(fig, ax, page)
pdf.close()
print("notch_templates.pdf written (%d pages)" % page)


# ------------------------------------------------------------------ drawings.pdf (A3, scale 1:4 for the views)
PW, PH = 420.0, 297.0
SC = 4.0


def dpage(title, sheet):
    fig = plt.figure(figsize=(PW / 25.4, PH / 25.4))
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_xlim(0, PW)
    bg.set_ylim(0, PH)
    bg.axis("off")
    bg.plot([8, PW - 8, PW - 8, 8, 8], [8, 8, PH - 8, PH - 8, 8], "k-", lw=0.8)
    bg.plot([8, PW - 8], [34, 34], "k-", lw=0.6)
    for xx in (150, 230, 290, 340):
        bg.plot([xx, xx], [8, 34], "k-", lw=0.4)
    bg.plot([8, PW - 8], [21, 21], "k-", lw=0.4)
    bg.text(11, 28, "TITLE", fontsize=4.5, color="0.4")
    bg.text(11, 23.5, "Truss chassis, 349cc single, prototype", fontsize=8, weight="bold")
    bg.text(11, 17.5, "Mild steel ERW tube 19x1.6 / 28x2 / 50x3, plate 6 mm. TIG or MIG welded.", fontsize=5.5)
    bg.text(11, 12.5, "Not a certified motorcycle frame: weld inspection and a load test are required before riding.", fontsize=5.5)
    bg.text(153, 28, "DRAWING NO.", fontsize=4.5, color="0.4")
    bg.text(153, 23.5, "CH-001", fontsize=9, weight="bold")
    bg.text(153, 12.5, "Units: mm   Axes: x forward, y left, z up", fontsize=5.5)
    bg.text(153, 17.5, "Origin: swingarm pivot centre", fontsize=5.5)
    bg.text(233, 28, "SCALE", fontsize=4.5, color="0.4")
    bg.text(233, 23.5, "1:4 (views)", fontsize=7.5)
    bg.text(233, 12.5, "Projection: third angle", fontsize=5.5)
    bg.text(293, 28, "TOLERANCE", fontsize=4.5, color="0.4")
    bg.text(293, 23.5, "ISO 2768-m; nodes +-1", fontsize=6.5)
    bg.text(293, 12.5, "Weld: ISO 5817 level C", fontsize=5.5)
    bg.text(343, 28, "REV / DATE", fontsize=4.5, color="0.4")
    bg.text(343, 23.5, "A  2026-11-18", fontsize=7.5)
    bg.text(343, 17.5, "Sheet %s" % sheet, fontsize=8, weight="bold")
    bg.text(343, 12.5, "Designed by Claude (AI), unchecked", fontsize=5)
    bg.text(12, PH - 16, title, fontsize=11, weight="bold")
    return fig, bg


def vaxes(fig, left, bottom, xr, yr):
    w, h = (xr[1] - xr[0]) / SC, (yr[1] - yr[0]) / SC
    ax = fig.add_axes([left / PW, bottom / PH, w / PW, h / PH])
    ax.set_xlim(*xr)
    ax.set_ylim(*yr)
    ax.axis("off")
    return ax


def proj_fn(view):
    return {"side": lambda p: (p[0], p[2]), "top": lambda p: (p[0], p[1]), "front": lambda p: (p[1], p[2])}[view]


def draw_view(ax, view, label_all=False):
    pr = proj_fn(view)
    for r in rows:
        a, b = pr(pos[r["a"]]), pr(pos[r["b"]])
        ax.plot([a[0], b[0]], [a[1], b[1]], "-", color="0.15" if r["size"] != "S" else "0.35", lw={"S": 1.1, "M": 2.2, "H": 3.0}[r["size"]], solid_capstyle="round")
    for bname, bx in (fr.ENGINE_BOXES.items() if SHOW_ENGINE_REF else []):
        lo, hi = pr((bx["x"][0], bx["y"][0], bx["z"][0])), pr((bx["x"][1], bx["y"][1], bx["z"][1]))
        ax.plot([lo[0], hi[0], hi[0], lo[0], lo[0]], [lo[1], lo[1], hi[1], hi[1], lo[1]], "--", color="tab:blue", lw=0.4)
    for n, p in pos.items():
        q = pr(p)
        ax.plot(q[0], q[1], "o", ms=2.2, color="k")
        if label_all or not n.endswith("R"):
            ax.annotate("%s (%.0f, %.0f)" % (n, q[0], q[1]), q, xytext=(3, 3), textcoords="offset points", fontsize=5.2)


def dim(ax, p, q, text, off=(0, 0)):
    p2, q2 = (p[0] + off[0], p[1] + off[1]), (q[0] + off[0], q[1] + off[1])
    ax.annotate("", xy=q2, xytext=p2, arrowprops=dict(arrowstyle="<->", lw=0.5, color="tab:red"))
    for a_, b_ in ((p, p2), (q, q2)):
        ax.plot([a_[0], b_[0]], [a_[1], b_[1]], "-", color="tab:red", lw=0.3)
    ax.text((p2[0] + q2[0]) / 2, (p2[1] + q2[1]) / 2, text, fontsize=5.5, color="tab:red", ha="center", va="bottom")


xs = [p[0] for p in pos.values()]
ys = [p[1] for p in pos.values()]
zs = [p[2] for p in pos.values()]
dpdf = PdfPages(os.path.join(OUT, "drawings.pdf"))

# sheet 1: summary
fig, bg = dpage("Chassis summary and notes", "1 of 6")
lines = [
    "ASSEMBLY: 39 straight tubes + 9 plates + 4 spacer tubes. Isostatic truss (rank 39 = 3j-6 for 15 joints). Engine hangs from nodes E and F.",
    "MATERIAL: ERW mild steel tube, yield taken as 250 MPa: 37 x 19x1.6 mm, 1 x 28x2 mm (pivot tube DL-DR), 1 x 50x3 mm (head tube HT-HB). Plates 6 mm mild steel.",
    "CUTTING: cut each tube square to the LONG SIDE length in tube_table.csv, then cope the ends with the 1:1 templates (notch_templates.pdf) or from tubes/*.step on a tube laser.",
    "COPING RULE: a tube is coped onto the larger tube at the node, or onto the lower-numbered tube of equal size (see 'coped onto' in tube_table.csv). Tubes that leave a node on the far side are not coped to each other.",
    "WELDING: full-perimeter welds, no gaps over 1 mm at fit-up. Jig: build on a flat table with node posts (jig_table.csv); check the diagonals on sheet 5 before final welding.",
    "ENGINE MOUNTS (the engine itself is not part of this pack): engine ears (14 mm holes, ear faces at |y| = 82) bolt with M12 x 90 through a 24/13 mm spacer (about 49 mm) and a 6 mm frame plate at E and F. Hang an engine template before welding the plates.",
    "OPEN DETAILS (not designed): shock mount at M is a placeholder plate (a real shock needs a clevis of two plates); swingarm pivot bearings and bolt length; footpeg and brake pedal brackets; seat, tank and bodywork mounts.",
    "ENGINE SHAKE (about 1.1 tonnes-force at 15,000 rpm, mostly at twice engine speed) is not in the analysis: use rubber-bushed mounts or test at low rpm first.",
    "ANALYSIS: pin-jointed static truss (static 1 g, bump 3 g, braking 1 g), minimum safety factor 3.16 (yield) and 6.01 (buckling). No weld, fatigue, lateral or crash analysis.",
]
for i, t in enumerate(lines):
    bg.text(14, PH - 34 - 8.5 * i, t, fontsize=6.6)
bg.text(14, PH - 34 - 8.5 * len(lines) - 8, "Overall: length %.0f x width %.0f x height %.0f mm (nodes), wheelbase 1400 mm, rake 25 deg, tube mass %.1f kg (+ plates %.1f kg)." % (
    max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), tot_mass, pl_mass), fontsize=7, weight="bold")
dpdf.savefig(fig)
plt.close(fig)

# sheet 2: side view + node table
fig, bg = dpage("Side view (x, z), scale 1:4, and node coordinates", "2 of 6")
xr = (min(xs) - 40, max(xs) + 60)
ax = vaxes(fig, 14, 60, xr, (min(zs) - 140, max(zs) + 40))
draw_view(ax, "side")
dim(ax, (min(xs), max(zs) + 20), (max(xs), max(zs) + 20), "%.0f (node to node)" % (max(xs) - min(xs)))
dim(ax, (max(xs) + 35, min(zs)), (max(xs) + 35, max(zs)), "%.0f" % (max(zs) - min(zs)))
role = {"HT": "head tube top", "HB": "head tube bottom", "M": "shock top", "C": "seat rear", "S": "seat front / tank", "D": "swingarm pivot",
        "E": "engine front mount", "F": "engine rear mount", "P": "footpeg"}
bg.text(262, PH - 36, "Node coordinates (mm)", fontsize=8, weight="bold")
bg.text(262, PH - 42, "node      x        y        z   role", fontsize=6.5, family="monospace")
for i, (n, p) in enumerate(pos.items()):
    bg.text(262, PH - 48 - 5.2 * i, "%-5s %7.1f %8.1f %8.1f   %s" % (n, p[0], p[1], p[2], role.get(n if n in ("HT", "HB", "M") else n[0], "")), fontsize=6.5, family="monospace")
dpdf.savefig(fig)
plt.close(fig)

# sheet 3: top view + front view
fig, bg = dpage("Top view (x, y) and front view (y, z), scale 1:4", "3 of 6")
ax = vaxes(fig, 14, 90, (min(xs) - 40, max(xs) + 60), (min(ys) - 30, max(ys) + 30))
draw_view(ax, "top", label_all=True)
dim(ax, (max(xs) + 35, min(ys)), (max(xs) + 35, max(ys)), "%.0f" % (max(ys) - min(ys)))
ax = vaxes(fig, 250, 90, (min(ys) - 40, max(ys) + 40), (min(zs) - 140, max(zs) + 40))
draw_view(ax, "front", label_all=True)
dpdf.savefig(fig)
plt.close(fig)

# sheet 4: tube table
fig, bg = dpage("Tube table (full table with coped-onto lists: tube_table.csv)", "4 of 6")
hdr = "%-8s %-7s %9s %9s %9s  %-4s %6s  %-4s %6s" % ("tube", "size", "centre", "long side", "short", "endA", "depth", "endB", "depth")
for col, rr in enumerate((rows[:20], rows[20:])):
    x0 = 14 + 205 * col
    bg.text(x0, PH - 36, hdr, fontsize=6, family="monospace", weight="bold")
    for i, r in enumerate(rr):
        bg.text(x0, PH - 42 - 5.6 * i, "%-8s %-7s %9.1f %9.1f %9.1f  %-4s %6.1f  %-4s %6.1f" % (
            r["id"], "%gx%g" % (r["od"], r["wall"]), r["L"], r["long"], r["short"], r["a"], r["smax"][0] - r["smin"][0], r["b"], r["smax"][1] - r["smin"][1]), fontsize=6, family="monospace")
bg.text(14, 36, "centre = node to node along the axis; long side = tip to tip, cut the tube square to this; depth = notch depth of that end (0 = cut square, other tubes cope onto it). All in mm.", fontsize=6)
dpdf.savefig(fig)
plt.close(fig)

# sheet 5: inspection diagonals + jig
fig, bg = dpage("Inspection distances and jig post table", "5 of 6")
bg.text(14, PH - 36, "Straight-line distances between nodes (check with a tape or laser measure before final welding, +-1.5 mm):", fontsize=7.5, weight="bold")
for i, (a, b, d_) in enumerate(diag):
    bg.text(14, PH - 44 - 5.6 * i, "%-3s - %-3s   %8.1f" % (a, b, d_), fontsize=6.5, family="monospace")
for r_i, r in enumerate(rows[:6]):
    pass
bg.text(150, PH - 36, "Member centreline lengths: see sheet 4. Jig posts on a flat table (jig_table.csv / jig_table.dxf):", fontsize=7.5, weight="bold")
bg.text(150, PH - 44, "node     table x    table y   post height (to node centre)", fontsize=6.5, family="monospace")
for i, (n, p) in enumerate(pos.items()):
    bg.text(150, PH - 50 - 5.2 * i, "%-6s %8.1f %9.1f %10.1f" % (n, p[0] - xmin, p[1], p[2] - zmin + 50), fontsize=6.5, family="monospace")
bg.text(150, 40, "Table x = frame x minus %.0f; table y = frame y; post height = frame z minus %.0f plus 50 mm clearance. Clamp each node point, tack tubes, then weld in a balanced order." % (xmin, zmin), fontsize=6)
dpdf.savefig(fig)
plt.close(fig)

# sheet 6: plates (1:2) and engine mount detail (1:1)
fig, bg = dpage("Plates (scale 1:2, flat patterns 1:1 in plates.dxf) and engine mount detail (scale 1:1)", "6 of 6")
K = 0.5
x_cur, y_row, row_h = 18.0, PH - 48, 0.0
done_k = set()
for pl in plates:
    key = (pl["kind"], pl["node"].rstrip("LR"))
    if key in done_k:
        continue
    done_k.add(key)
    if x_cur + pl["w"] * K > 235:
        x_cur, y_row, row_h = 18.0, y_row - row_h - 38, 0.0
    p = pl["c"]
    x0, z0 = p[0] - pl["w"] / 2, p[2] - pl["h"] / 2
    w_, h_ = pl["w"] * K, pl["h"] * K
    yb = y_row - h_
    bg.plot([x_cur, x_cur + w_, x_cur + w_, x_cur, x_cur], [yb, yb, yb + h_, yb + h_, yb], "k-", lw=0.8)
    if pl["hole"]:
        th = np.linspace(0, 2 * math.pi, 60)
        bg.plot(x_cur + w_ / 2 + K * pl["hole"] / 2 * np.cos(th), yb + h_ / 2 + K * pl["hole"] / 2 * np.sin(th), "k-", lw=0.8)
    for h in pl["holes"]:
        pts = ellipse_pts(h, 90)
        xx = list(x_cur + K * (pts[:, 0] - x0)) + [x_cur + K * (pts[0, 0] - x0)]
        zz = list(yb + K * (pts[:, 1] - z0)) + [yb + K * (pts[0, 1] - z0)]
        bg.plot(xx, zz, "k-", lw=0.8)
    names_ = [q["node"] for q in plates if (q["kind"], q["node"].rstrip("LR")) == key]
    bg.text(x_cur, y_row + 3, "%s at %s (qty %d)" % (pl["kind"], "/".join(names_), len(names_)), fontsize=6, weight="bold")
    bg.text(x_cur, yb - 4, "%.0f x %.0f x %.0f, bolt hole %s" % (pl["w"], pl["h"], pl["t"], ("d%g" % pl["hole"]) if pl["hole"] else "none"), fontsize=5.5)
    bg.text(x_cur, yb - 8, ("tube holes: " + ", ".join(h["tube"] for h in pl["holes"])) if pl["holes"] else "no tube holes", fontsize=5.2)
    x_cur += w_ + 18
    row_h = max(row_h, h_)
bg.text(18, 52, "Plates are shown from outside (+y); right-hand plates are the same parts turned over. Tube holes are the ellipses where tube axes pierce the", fontsize=6)
bg.text(18, 47, "plate: cut the plate as drawn, slide it over the tubes, weld all round. Peg plates sit on the outboard side of node P. The shock plate is a placeholder for a clevis.", fontsize=6)
x0m, zc = 262.0, 150.0
sp_len = SPACER_LEN
ear_w, ear_h = 20.0, 28.0
bg.add_patch(plt.Rectangle((x0m, zc - ear_h / 2), ear_w, ear_h, fc="0.85", ec="k", lw=0.8))
bg.add_patch(plt.Rectangle((x0m + ear_w, zc - fr.SPACER_OD / 2), sp_len, fr.SPACER_OD, fc="0.95", ec="k", lw=0.8))
bg.add_patch(plt.Rectangle((x0m + ear_w + sp_len, zc - 65), T_PL, 130, fc="orange", ec="k", lw=0.8))
bg.plot([x0m - 8, x0m + ear_w + sp_len + T_PL + 22], [zc, zc], "k-.", lw=0.5)
bg.add_patch(plt.Rectangle((x0m - 6, zc - 11), 6, 22, fc="0.6", ec="k", lw=0.6))
bg.add_patch(plt.Rectangle((x0m + ear_w + sp_len + T_PL, zc - 9), 12, 18, fc="0.6", ec="k", lw=0.6))
bg.text(x0m - 6, zc + 76, "Engine mount at E and F: section along the bolt (1:1)", fontsize=7, weight="bold")
bg.text(x0m - 6, zc - 22, "engine ear 20 (hole 14)", fontsize=5.5)
bg.text(x0m + ear_w, zc + 16, "spacer 24/13 x %.0f" % sp_len, fontsize=5.5)
bg.text(x0m + ear_w + sp_len - 8, zc - 72, "6 mm frame plate (hole 13)", fontsize=5.5)
bg.text(x0m - 6, zc - 86, "M12 x 90 bolt, 8.8, head on the engine side, lock nut and washers on the outside.", fontsize=5.5)
bg.text(x0m - 6, zc - 92, "The tube axes meet %.0f mm outboard of the plate's outer face." % (R_OUT - T_PL / 2), fontsize=5.5)
dpdf.savefig(fig)
plt.close(fig)
dpdf.close()
print("drawings.pdf written")


# ------------------------------------------------------------------ welded single-body STEP (for SolidWorks: one part, tubes + plates fused)
try:
    parts_ = [solids[r["id"]] for r in rows] + [plate_solid(pl) for pl in plates] + [spacer_solid(n + sfx, 1 if sfx == "L" else -1)[0] for sfx in "LR" for n in ("E", "F")]
    body = parts_[0].fuse(*parts_[1:]).clean()
    vol_sum = sum(p.Volume() for p in parts_)
    print("welded body: valid=%s solids=%d volume %.0f mm3 (sum of parts %.0f)" % (body.isValid(), len(body.Solids()), body.Volume(), vol_sum))
    cq.exporters.export(cq.Workplane("XY").newObject([body]), os.path.join(OUT, "chassis_welded_single_body.step"))
except Exception as ex:
    print("welded body failed:", ex)

# ------------------------------------------------------------------ drawing_views.dxf: 2D views at 1:1 with dimensions (opens in SolidWorks drawings / any CAD)
doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
for lay, col in (("TUBE_19", 7), ("TUBE_28", 2), ("TUBE_50", 6), ("NODES", 1), ("TEXT", 8), ("DIM", 3)):
    doc.layers.add(lay, color=col)
msp = doc.modelspace()
GAP = 150.0
views = {"SIDE (x,z)": (lambda p: (p[0], p[2]), (0.0, 0.0)),
         "TOP (x,y)": (lambda p: (p[0], p[1]), (0.0, -(max(zs) - min(zs)) - (max(ys) - min(ys)) - 2 * GAP)),
         "FRONT (y,z)": (lambda p: (p[1], p[2]), (max(xs) - min(xs) + 2 * GAP + (max(ys) - min(ys)), 0.0))}
for vname, (pr, off) in views.items():
    for r in rows:
        a, b = pr(pos[r["a"]]), pr(pos[r["b"]])
        msp.add_line((a[0] + off[0], a[1] + off[1]), (b[0] + off[0], b[1] + off[1]), dxfattribs={"layer": "TUBE_%d" % int(r["od"])})
    for n, p in pos.items():
        q = pr(p)
        msp.add_circle((q[0] + off[0], q[1] + off[1]), 5, dxfattribs={"layer": "NODES"})
        msp.add_text("%s (%.0f, %.0f)" % (n, q[0], q[1]), height=8, dxfattribs={"layer": "TEXT", "insert": (q[0] + off[0] + 8, q[1] + off[1] + 8)})
    allq = [pr(p) for p in pos.values()]
    lo_x, hi_x = min(q[0] for q in allq), max(q[0] for q in allq)
    lo_y, hi_y = min(q[1] for q in allq), max(q[1] for q in allq)
    msp.add_text(vname + "  scale 1:1, tubes centreline", height=14, dxfattribs={"layer": "TEXT", "insert": (lo_x + off[0], hi_y + off[1] + 60)})
    d1 = msp.add_linear_dim(base=(lo_x + off[0], hi_y + off[1] + 40), p1=(lo_x + off[0], hi_y + off[1]), p2=(hi_x + off[0], hi_y + off[1]), dimstyle="EZDXF", override={"dimtxt": 8, "dimasz": 6}, dxfattribs={"layer": "DIM"})
    d1.render()
    d2 = msp.add_linear_dim(base=(hi_x + off[0] + 50, lo_y + off[1]), p1=(hi_x + off[0], lo_y + off[1]), p2=(hi_x + off[0], hi_y + off[1]), angle=90, dimstyle="EZDXF", override={"dimtxt": 8, "dimasz": 6}, dxfattribs={"layer": "DIM"})
    d2.render()
doc.saveas(os.path.join(OUT, "drawing_views.dxf"))
print("drawing_views.dxf written")

json.dump(dict(tube_long_check_worst_mm=worst, tube_mass_kg=tot_mass, plate_mass_kg=pl_mass, spacer_len_mm=SPACER_LEN,
               plates=[dict(kind=p["kind"], node=p["node"], w=p["w"], h=p["h"], t=p["t"], holes=len(p["holes"])) for p in plates],
               diagonals=[[a, b, round(d, 1)] for a, b, d in diag]),
          open(os.path.join(OUT, "results_pack.json"), "w"), indent=1)
