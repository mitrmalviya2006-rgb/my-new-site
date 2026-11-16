#!/usr/bin/env python3
"""
Search for the 39-bar set (isostatic, mirror-symmetric) that suits the node positions and engine in frame.py.

Why: with the real engine hung from nodes E and F, many obvious bars are not allowed (they cut through the engine, pass
within 25 mm of another node, cross another bar, or run through the airbox zone above the engine). The bars that are
allowed are few enough to search. Cost = tube mass after S/M sizing + 40 per failing member + 30 per tube crossing
+ largest node movement (mm) - 0.1 per bar that was in the original hand layout.

Run:  python topology_search.py [seed] [seconds]     (several seeds converge to the same answer)
Then paste the printed list into base_members() in frame.py (or keep it as is if it already matches).
"""
import itertools
import math
import random
import sys
import time

import numpy as np

import frame as fr

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
budget = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
LMIN, LMAX = 150.0, 700.0           # bar length limits, mm
NODE_CLEAR = 25.0                   # no bar may pass closer than this to a node it does not end at
CROSS_CLEAR = 20.0                  # centreline distance below which two bars count as crossing

pos = fr.build_nodes()
names = list(pos)
need = 3 * len(names) - 6
r_clear = fr.TUBES["M"][0] / 2 + fr.CLEAR + 0.5


def mirror(n):
    return n[:-1] + ("R" if n.endswith("L") else "L") if n.endswith(("L", "R")) else n


def pt_seg(p, a, b):
    dvec = b - a
    t = max(0.0, min(1.0, float((p - a) @ dvec) / float(dvec @ dvec)))
    return float(np.linalg.norm(p - (a + dvec * t)))


allowed = {}
for a, b in itertools.combinations(names, 2):
    L = float(np.linalg.norm(pos[a] - pos[b]))
    if not (LMIN <= L <= LMAX):
        continue
    if fr.seg_engine_dist(pos[a], pos[b]) < r_clear:
        continue
    if fr.seg_box_dist(pos[a], pos[b], fr.KEEP_OUT["airbox"]) < 20.0:
        continue
    if any(pt_seg(pos[c], pos[a], pos[b]) < NODE_CLEAR for c in names if c not in (a, b)):
        continue
    allowed[frozenset((a, b))] = (a, b)


def orbit_of(e):
    a, b = e
    return frozenset({frozenset((a, b)), frozenset((mirror(a), mirror(b)))})


orbits = {}
for k, e in allowed.items():
    o = orbit_of(e)
    if all(x in allowed for x in o):
        orbits[o] = [tuple(sorted(x)) for x in o]


def crossing_count(mem):
    n = 0
    for (a, b), (c, d) in itertools.combinations(mem, 2):
        if len({a, b, c, d}) < 4:
            continue
        if fr.seg_seg_dist(pos[a], pos[b], pos[c], pos[d]) < CROSS_CLEAR:
            n += 1
    return n


orbits = {o: v for o, v in orbits.items() if crossing_count(v) == 0}
olist = list(orbits)
osize = {o: len(orbits[o]) for o in olist}
ORIG = {frozenset(m) for m in fr.base_members()}

LOCK = [("HT", "HB"), ("DL", "DR")]
for sfx in "LR":
    LOCK += [("HT", "S" + sfx), ("S" + sfx, "C" + sfx), ("M", "C" + sfx), ("M", "D" + sfx)]
lock = set()
for e in LOCK:
    o = orbit_of(e)
    orbits.setdefault(o, [tuple(sorted(x)) for x in o])
    osize[o] = len(orbits[o])
    lock.add(o)
olist = list(orbits)
print("allowed bars %d, symmetric groups %d, locked %d" % (len(allowed), len(olist), len(lock)))


def members_of(sel):
    return [e for o in sel for e in orbits[o]]


def cost_of(sel):
    mem = members_of(sel)
    if len(mem) != need:
        return 1e6
    if fr.rigidity_rank(names, pos, mem) < need:
        return 5e3
    sizes, loads, info, sol = fr.size_members(names, pos, mem, lambda sz: fr.masses(pos, mem, sz))
    if sol["min_eig"] < 1e-3:
        return 4e3
    rows = fr.member_table(names, pos, mem, sizes, sol, loads)
    mass = sum(r["length"] * math.pi / 4 * (r["od"] ** 2 - (r["od"] - 2 * r["wall"]) ** 2) * fr.RHO for r in rows)
    nfail = sum(1 for r in rows if r["sf_yield"] < fr.SF_MIN or r["sf_buckle"] < fr.SF_MIN)
    umax = max(sol["cases"][c]["u_max"] for c in loads)
    norig = sum(1 for m in mem if frozenset(m) in ORIG)
    return mass + 40 * nfail + 30 * crossing_count(mem) + umax - 0.1 * norig


random.seed(seed)
best = (1e18, None)
t0 = time.time()
while time.time() - t0 < budget:
    sel = set(lock)
    cnt = sum(osize[o] for o in sel)
    pool = [o for o in olist if o not in sel]
    random.shuffle(pool)
    for o in pool:
        if cnt + osize[o] <= need:
            sel.add(o)
            cnt += osize[o]
        if cnt == need:
            break
    if cnt != need:
        continue
    cur = cost_of(sel)
    T = 20.0
    for _ in range(400):
        movable = [o for o in sel if o not in lock]
        o_out = random.choice(movable)
        same = [o for o in olist if o not in sel and osize[o] == osize[o_out]]
        if not same:
            continue
        new = (sel - {o_out}) | {random.choice(same)}
        c2 = cost_of(new)
        if c2 < cur or random.random() < math.exp(-(c2 - cur) / max(T, 1e-3)):
            sel, cur = new, c2
        T *= 0.985
        if cur < best[0]:
            best = (cur, set(sel))
mem = members_of(best[1])
print("best cost %.2f after %.0f s" % (best[0], time.time() - t0))
side = sorted(e for e in mem if not any(n.endswith("R") for n in e))
cross = sorted(e for e in mem if any(n.endswith("R") for n in e) and any(n.endswith("L") for n in e) and mirror(e[0]) == e[1])
print("left-side and centre-line bars (mirror them for the right side):")
print(side)
print("left-right cross bars:", cross)
