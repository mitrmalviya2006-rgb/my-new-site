#!/usr/bin/env python3
"""
Solid-to-solid fit check between the chassis (frame.step) and the real engine (../engine-design/engine.step).

1. Do the engine clearance boxes used by frame.py really enclose every part of the engine?
   (tessellate all engine solids, report the largest distance any vertex sticks out of the union of boxes)
2. Smallest gap between every frame solid (tube, lug plate, spacer, ...) and every engine solid
   (exact B-rep distance, BRepExtrema), after moving the engine to ENGINE_ORIGIN.

Writes fit_check.json. Needs cadquery; the full run takes about 5 minutes (exact distances to 139 engine solids).
`python check_fit.py --boxes-only` redoes only step 1 (about 10 s) after the engine's boxes change.
"""
import json
import os
import sys
import time

import numpy as np

import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

import frame as fr

HERE = os.path.dirname(os.path.abspath(__file__))
t0 = time.time()

# ---- engine solids, moved into the vehicle frame
eng = cq.importers.importStep(os.path.join(fr.ENGINE_DIR, "engine.step"))
move = cq.Vector(*[float(x) for x in fr.ENGINE_ORIGIN])
eng_solids = [s.translate(move) for s in eng.val().Solids()]
print("engine solids: %d  (%.0f s)" % (len(eng_solids), time.time() - t0), flush=True)

# ---- 1. boxes enclose the engine?
lo = np.array([[b["x"][0], b["y"][0], b["z"][0]] for b in fr.ENGINE_BOXES.values()])
hi = np.array([[b["x"][1], b["y"][1], b["z"][1]] for b in fr.ENGINE_BOXES.values()])
worst = 0.0
worst_at = None
worst_part = None
for i, s in enumerate(eng_solids):
    verts, _ = s.tessellate(0.5, 0.5)
    if not verts:
        continue
    P = np.array([[v.x, v.y, v.z] for v in verts])
    d = np.maximum(np.maximum(lo[None, :, :] - P[:, None, :], P[:, None, :] - hi[None, :, :]), 0.0)
    out = np.linalg.norm(d, axis=2).min(axis=1)       # distance of each vertex to the nearest box
    k = int(out.argmax())
    if out[k] > worst:
        worst, worst_at, worst_part = float(out[k]), [round(float(c), 1) for c in P[k]], i
print("largest protrusion of any engine vertex outside the clearance boxes: %.2f mm at %s (engine solid #%s, %.0f s)"
      % (worst, worst_at, worst_part, time.time() - t0), flush=True)

if "--boxes-only" in sys.argv:          # quick rerun (about 10 s) after the engine's clearance boxes change; keeps the slow part-2 results
    path = os.path.join(HERE, "fit_check.json")
    prev = json.load(open(path)) if os.path.exists(path) else {}
    prev.update({"engine_solids": len(eng_solids), "boxes_enclose_engine": worst < 0.6,
                 "max_protrusion_outside_boxes_mm": round(worst, 2), "max_protrusion_at_mm": worst_at})
    with open(path, "w") as fh:
        json.dump(prev, fh, indent=1)
    print(json.dumps(prev, indent=1))
    sys.exit(0 if worst < 0.6 else 1)

# ---- 2. frame solids vs engine solids
assy = cq.Assembly.importStep(os.path.join(HERE, "frame.step"))
frame_parts = []
for name, child in [(c.name, c) for c in assy.children]:
    if name.startswith("ENGINE_BOX_"):
        continue
    frame_parts.append((name, child.obj if not hasattr(child.obj, "val") else child.obj.val()))
print("frame solids: %d" % len(frame_parts))

ebb = [s.BoundingBox() for s in eng_solids]


def bb_gap(a, b):
    dx = max(a.xmin - b.xmax, b.xmin - a.xmax, 0.0)
    dy = max(a.ymin - b.ymax, b.ymin - a.ymax, 0.0)
    dz = max(a.zmin - b.zmax, b.zmin - a.zmax, 0.0)
    return (dx * dx + dy * dy + dz * dz) ** 0.5


rows = []
overlap = []
for name, shp in frame_parts:
    fb = shp.BoundingBox()
    best = (1e9, None)
    for j, s in enumerate(eng_solids):
        if bb_gap(fb, ebb[j]) > 60.0:      # cannot be the closest one if the boxes are more than 60 mm apart
            continue
        d = BRepExtrema_DistShapeShape(shp.wrapped, s.wrapped)
        d.Perform()
        if d.IsDone() and d.Value() < best[0]:
            best = (d.Value(), j)
        if d.IsDone() and d.Value() < 0.05:        # touching: is it contact or does it overlap?
            vol = shp.intersect(s).Volume()
            if vol > 0.5:
                overlap.append((name, j, round(float(vol), 1)))
    rows.append((name, best[0], best[1]))
rows.sort(key=lambda r: r[1])
print("closest frame solids to a real engine part (mm):")
for name, d, j in rows[:8]:
    print("  %-14s %7.1f" % (name, d if d < 1e8 else float("nan")))
closest = rows[0][1]
out = {
    "engine_solids": len(eng_solids),
    "boxes_enclose_engine": worst < 0.6,
    "max_protrusion_outside_boxes_mm": round(worst, 2),
    "frame_solids": len(frame_parts),
    "closest_frame_part": rows[0][0],
    "min_gap_frame_to_engine_mm": round(closest, 1) if closest < 1e8 else None,
    "closest_list": [[n, round(d, 1)] for n, d, _ in rows[:8] if d < 1e8],
    "overlaps_mm3": overlap,
    "max_protrusion_at_mm": worst_at,
    "seconds": round(time.time() - t0),
}
with open(os.path.join(HERE, "fit_check.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps(out, indent=1))
ok_gap = all(d >= fr.CLEAR for n, d, _ in rows if not n.startswith("SPACER_"))    # spacers bolt to the ears: contact is intended
sys.exit(0 if out["boxes_enclose_engine"] and ok_gap and not overlap else 1)
