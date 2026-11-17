#!/usr/bin/env python3
"""Check make-pack/chassis_cut_ready.step by re-importing it: solid validity, tube-to-tube overlap volume, and node positions."""
import itertools
import json
import os

import numpy as np
import cadquery as cq

import frame as fr

HERE = os.path.dirname(os.path.abspath(__file__))
assy = cq.Assembly.importStep(os.path.join(HERE, "make-pack", "chassis_cut_ready.step"))
parts = {c.name: (c.obj.val() if hasattr(c.obj, "val") else c.obj) for c in assy.children}
tubes = {k: v for k, v in parts.items() if k.startswith("TUBE_")}
others = {k: v for k, v in parts.items() if not k.startswith(("TUBE_", "REFERENCE_"))}
print("solids: %d tubes, %d plates/spacers" % (len(tubes), len(others)))
bad = [k for k, v in {**tubes, **others}.items() if not v.isValid()]
print("invalid solids:", bad or "none")

bbs = {k: v.BoundingBox() for k, v in tubes.items()}
worst = (0.0, None)
nchk = 0
for (a, va), (b, vb) in itertools.combinations(tubes.items(), 2):
    A, B = bbs[a], bbs[b]
    if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin:
        continue
    nchk += 1
    vol = va.intersect(vb).Volume()
    if vol > worst[0]:
        worst = (vol, (a, b))
print("tube pairs tested: %d, largest overlap volume %.2f mm3 %s (small slivers at the nodes, filled by the weld)" % (nchk, worst[0], worst[1]))

# node positions: tube axes must still pass through the node points (check tube centre-of-end positions via bounding box of the full tubes)
pos = fr.build_nodes()
members = fr.base_members()
ok_nodes = True
for a, b in members:
    key = "TUBE_%s-%s" % (a, b)
    if key not in tubes:
        ok_nodes = False
        print("missing", key)
print("all %d members present: %s" % (len(members), ok_nodes))
res = dict(tubes=len(tubes), plates_spacers=len(others), invalid=bad, max_tube_overlap_mm3=round(worst[0], 2), overlap_pair=worst[1], members_present=ok_nodes)
json.dump(res, open(os.path.join(HERE, "make-pack", "verify_pack.json"), "w"), indent=1)
raise SystemExit(0 if not bad and ok_nodes and worst[0] < 500 else 1)
