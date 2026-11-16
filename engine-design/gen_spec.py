#!/usr/bin/env python3
"""Write SPEC.md (plain-language design report) from results.json, bom.csv and the chassis results if present."""
import csv
import json
import math
import os

import params as P

d = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(d, "results.json")))
bom = R["bom"]
ctx = R["ctx"]
env = R["envelope"]
vt = R["valvetrain"]
bal = R["balance"]
pk, tq = R["power_peak"], R["torque_peak"]
red = [r for r in R["power"] if r["rpm"] == 15000][0]
chassis_path = os.path.join(d, "..", "engine-chassis", "results.json")
chassis = json.load(open(chassis_path)) if os.path.exists(chassis_path) else None

L = []
a = L.append


def tbl(head, rows):
    a("| " + " | ".join(head) + " |")
    a("|" + "|".join("---" for _ in head) + "|")
    for r in rows:
        a("| " + " | ".join(str(x) for x in r) + " |")
    a("")


def f0(x):
    return "{:,}".format(int(round(x)))


a("# 349 cc single-cylinder engine: design report\n")
a("A small liquid-cooled petrol engine with one cylinder, four valves and a 15,000 rpm redline, drawn as a full 3D assembly of %d pieces (%d different parts). "
  "It is designed to be easy to put together and to have as few parts as it can get away with. The clutch, gearbox or CVT are **not** part of it: "
  "the crank ends in a bolt-on output flange so any of them can be added later.\n" % (R["counts"]["pieces"], R["counts"]["unique"]))
a("Axes used everywhere: x forward, y left, z up, origin at the crank axis, millimetres. Sides are named by what is on them: the **output side** (+y: gear cover, pumps, output flange) faces the bike's **left** when the engine is installed as in the chassis, and the **alternator side** (-y: cam chain, alternator) faces the bike's **right**. Everything here is a design and a set of hand calculations. "
  "Nothing has been built, tested on a dyno or checked with FEA, so treat the numbers as the starting point for testing.\n")

a("## 1. The engine in numbers\n")
tbl(["Item", "Value", "In plain words"], [
    ["Displacement", "%.1f cc" % P.VD_CC, "the total volume the piston sweeps"],
    ["Bore x stroke", "%.1f x %.1f mm" % (P.BORE, P.STROKE), "cylinder width x how far the piston travels; wide and short so it can spin fast"],
    ["Compression ratio", "%.1f : 1" % ctx["cr"], "how hard the fuel-air mix is squeezed; needs premium petrol"],
    ["Redline", "%s rpm" % f0(P.RPM_REDLINE), "the highest speed the engine is meant to turn"],
    ["Piston speed at redline", "%.1f m/s" % (R["piston_speed_15k"] + 1e-9), "racing-class; ordinary road engines stay near 15 to 20"],
    ["Valves", "2 intake %.0f mm, 2 exhaust %.0f mm, titanium" % (P.VALVE_IN["d"], P.VALVE_EX["d"]), "four valves, two to breathe in and two to breathe out"],
    ["Power (estimate)", "%.0f hp at %s rpm" % (pk["hp"], f0(pk["rpm"])), "%.0f hp at the 15,000 rpm redline; the engine runs out of breath before it runs out of revs" % red["hp"]],
    ["Torque (estimate)", "%.0f N·m at %s rpm" % (tq["nm"], f0(tq["rpm"])), "the twisting force"],
    ["Mass, dry", "%.1f kg" % R["mass"]["dry_kg"], "engine alone: no radiator, exhaust, ECU, clutch or gearbox; %.1f kg with oil and coolant" % R["mass"]["wet_kg"]],
    ["Size", "%s x %s x %s mm" % (f0(env["x"][1] - env["x"][0]), f0(env["y"][1] - env["y"][0]), f0(env["z"][1] - env["z"][0])), "length x width x height including intake, oil filter and coil"],
    ["Parts", "%d different, %d to machine, %d to buy" % (R["counts"]["unique"], R["counts"]["make"], R["counts"]["buy"]), "plus %d modelled pieces in total" % R["counts"]["pieces"]],
])
a("The power and torque figures come from a simple single-zone combustion model tuned to typical racing-engine values. Expect them to be right within about 15 percent at best. Only a dyno gives real numbers.\n")

a("## 2. How it is laid out, and why\n")
for t in [
    "**One cylinder, standing upright.** Fewest parts of any layout, and a vertical cylinder is the easiest to machine and to assemble.",
    "**Four valves with two overhead cams.** Four small valves open faster and breathe better than two big ones. They are lighter, which matters at 15,000 rpm.",
    "**Finger followers between the cams and the valves.** They are lighter than the bucket-shaped followers used in many engines, so the valve springs can keep up at high speed.",
    "**A one-piece crankshaft on plain (sliding) bearings.** No pressed-together crank and no roller bearings. The rod and the crank run on thin replaceable shell bearings, as in most modern sports-bike engines.",
    "**Cases that stack in one direction.** Bedplate, upper case, cylinder barrel, gasket, head, cam ladder and cover are built up like a layer cake. Four long studs clamp the barrel and head to the upper case, so there are very few bolts.",
    "**A wet liner.** The cylinder wall is a separate steel tube with coolant flowing round it. It can be replaced, and the aluminium barrel needs no special coating.",
    "**One balance shaft that does three jobs.** It cancels most of the shaking a single cylinder makes, and the same shaft drives the water pump at one end and the oil pump at the other. No extra pump drives.",
    "**The crank carries its own gear and the balance gear sits on the shaft.** Both gears are on the output side, under one cover.",
    "**A bolt-on output flange** on the output end of the crank. The clutch, the CVT you asked about, or a gearbox can bolt straight to it.",
    "**Chain drive for the cams, coil on plug, wet sump, fuel injection.** All standard, catalogue-type parts.",
    "**Only three bolt sizes for the structure (M6, M8, M10)**, plus the rod bolts and the output flange bolts.",
]:
    a("- " + t)
a("")

a("## 3. Do the numbers hold up? (all checks)\n")
rows = []
for c in R["checks"]:
    v = c["value"]
    try:
        v = f0(v) if abs(float(v)) >= 1000 else ("%.2f" % float(v)).rstrip("0").rstrip(".")
    except Exception:
        pass
    lim = c["limit"]
    try:
        lim = f0(lim) if abs(float(lim)) >= 1000 else ("%g" % round(float(lim), 2))
    except Exception:
        pass
    rows.append([c["name"], (str(v) + " " + c["unit"]).strip(), lim, "pass" if c["ok"] else "**FAIL**", c["note"]])
tbl(["Check", "Result", "Limit", "", "How"], rows)
nf = [c for c in R["checks"] if not c["ok"]]
a("All %d checks pass." % len(R["checks"]) if not nf else "%d check(s) fail, see above." % len(nf))
a("Two limits are tight and worth knowing about: the exhaust valve train starts to lose contact at about %s rpm in the model (only %.0f%% above the redline), "
  "and the rod journal sees about %.0f MPa at the peak of the firing stroke against a limit of 140.\n" %
  (f0(vt["ex"]["float_onset_rpm"]), 100.0 * (vt["ex"]["float_onset_rpm"] / P.RPM_REDLINE - 1), R["loads"]["pin_peak"] / (P.PIN_JOURNAL_D * P.PIN_W)))

a("## 4. What changed from the plan, and why\n")
for t in [
    "**Valves are 28 mm intake and 24 mm exhaust, both titanium**, not 30 and 25 mm with steel exhaust valves. In the first spring sweep a hollow steel 24 mm exhaust valve needed about 840 N of spring force at 16,500 rpm against about 570 N for titanium, which is more than a spring of this size can safely give. Smaller, lighter valves keep the valve train under control.",
    "**The power peaks at about %s rpm, not at 13,500 to 14,000 rpm.** The smaller valves restrict breathing at high speed, so the engine reaches 15,000 rpm but makes only about %.0f hp there. In practice a shift point around 12,500 to 13,000 rpm would use the engine best." % (f0(pk["rpm"]), red["hp"]),
    "**The crank webs are 22 mm thick** and the case is 4 mm wider than first sketched. The counterweights need to be that big to balance a %.0f g piston and pin. Without it the only way is tungsten inserts, which cost more and add parts." % (ctx["piston_group"] * 1000),
    "**The case top is 62 mm above the crank axis** instead of 36 mm, so the counterweights never swing up into the cylinder bore.",
    "**The crank gear is cut into the crank itself and the output flange bolts on.** Otherwise the gear and the gear cover could not be fitted.",
    "**Rod bolts are 7/16 inch**, the piston pin is 22 mm and the rod beam is 19 x 19 mm, all sized up once the real CAD masses were known (the reciprocating mass came out at %.0f g)." % (ctx["m_rec"] * 1000),
]:
    a("- " + t)
a("")

a("## 5. Valves, cams and springs\n")
tbl(["", "Intake", "Exhaust"], [
    ["Valve diameter", "%.0f mm x 2" % P.VALVE_IN["d"], "%.0f mm x 2" % P.VALVE_EX["d"]],
    ["Lift", "%.1f mm" % P.VALVE_IN["lift"], "%.1f mm" % P.VALVE_EX["lift"]],
    ["Open duration (crank degrees)", "%.0f" % P.VALVE_IN["duration"], "%.0f" % P.VALVE_EX["duration"]],
    ["Lobe centre (crank degrees after gas-exchange TDC)", "%.0f" % P.LCA_IN, "%.0f" % (P.LCA_EX - 720)],
    ["Moving mass at the valve", "%.1f g" % vt["in"]["m_eff"], "%.1f g" % vt["ex"]["m_eff"]],
    ["Spring force, seat / full lift", "%.0f / %.0f N" % (P.SPRING_PRELOAD, vt["in"]["f_open"]), "%.0f / %.0f N" % (P.SPRING_PRELOAD, vt["ex"]["f_open"])],
    ["Outer spring (wire x mean diameter x active coils)", "%.1f x %.1f x %.1f" % (vt["in"]["spring"]["outer"]["d"], vt["in"]["spring"]["outer"]["D"], vt["in"]["spring"]["outer"]["na"]),
     "%.1f x %.1f x %.1f" % (vt["ex"]["spring"]["outer"]["d"], vt["ex"]["spring"]["outer"]["D"], vt["ex"]["spring"]["outer"]["na"])],
    ["Inner spring", "%.1f x %.1f x %.1f" % (vt["in"]["spring"]["inner"]["d"], vt["in"]["spring"]["inner"]["D"], vt["in"]["spring"]["inner"]["na"]),
     "%.1f x %.1f x %.1f" % (vt["ex"]["spring"]["inner"]["d"], vt["ex"]["spring"]["inner"]["D"], vt["ex"]["spring"]["inner"]["na"])],
    ["Valve train loses cam contact from (model)", "%s rpm" % f0(vt["in"]["float_onset_rpm"]), "%s rpm" % f0(vt["ex"]["float_onset_rpm"])],
    ["Seating speed at 15,000 rpm", "%.2f m/s" % abs(vt["in"]["seat_velocity_15k"]), "%.2f m/s" % abs(vt["ex"]["seat_velocity_15k"])],
])
a("Spring wire is Cr-Si, shot-peened, worked to about 1,000 MPa at full compression. The springs in the 3D model are drawn as plain tubes. "
  "The lever ratio of the finger followers is %.2f and each follower swings about 20 degrees at full lift. The spring surge frequency is only %.1f to %.1f times the cam frequency, "
  "so a cam profile with little high-frequency content and a damped inner spring matter. Lash (cold): 0.10 to 0.15 mm intake, 0.15 to 0.20 mm exhaust, set with the lash caps.\n" %
  (P.derived()["lever_ratio"], vt["in"]["surge_ratio_15k"], vt["ex"]["surge_ratio_15k"]))

a("## 6. Balance (the shaking)\n")
a("A single cylinder shakes itself. At 15,000 rpm the moving piston and rod would shake the engine with a peak force of about %.1f tonnes-force if nothing were balanced. "
  "The crank counterweights bring that to about %.1f tonnes-force, and the balance shaft to about %.1f tonnes-force. The part that is left is the shake at twice engine speed, "
  "which a single balance shaft cannot remove. It shows up as a high buzz that the frame and the mounts have to live with.\n" %
  (bal["peak_none"] / 9810.0, bal["peak_cw_only"] / 9810.0, bal["peak_with"] / 9810.0))
a("Counterweight moment %.1f kg·mm (target %.1f), flank radius %.1f mm. Balance weights %.1f mm thick each, moment %.1f kg·mm (target %.1f).\n" %
  (ctx["crank_moment"] / 1000, ctx["cw_target"] / 1000, ctx["flank"], ctx["bal_t"], ctx["bal_moment"] / 1000, ctx["bal_target"] / 1000))

a("## 7. How to assemble it\n")
a("Twelve steps. Every part goes in along one straight line, and the only special tools are a torque wrench, a cam-timing mark or pin, and a piston ring compressor. "
  "One honest gap: **dowel pins and keyways that would make a wrong fit impossible (case halves, covers, balance-shaft phase, cam timing) are not modelled yet.** "
  "Today the model proves each part can go in along its path; it does not stop you fitting a part the wrong way round. Add dowels and keys before ordering parts.\n")
for k in sorted(R["steps"], key=int):
    a("%s. %s" % (k, R["steps"][k]))
a("")
a("Each move was checked in the 3D model by sliding the part along its path and testing for any contact (%d moves, none blocked).\n" % len(R["insertion"]))
tbl(["Fastener", "Starting torque (confirm with the fastener supplier)"], [
    ["M10 head studs, nuts, main-cap bolts", "70 N·m, oiled threads"],
    ["M8 case bolts and output flange bolts", "25 N·m"],
    ["M6 bolts (oil pan, ladder, covers)", "10 N·m"],
    ["Rod bolts 7/16-20", "to the bolt maker's stretch figure (about 0.17 mm), not by torque"],
])

a("## 8. Parts list\n")
a("**To machine (%d parts).** Aluminium parts are 7075-T6 or 6061-T6 billet, which a CNC service such as JLCCNC can quote from the STEP files in `parts/`. "
  "The crank, rod, balance shaft and gears need heat treatment and grinding at a local shop afterwards.\n" % R["counts"]["make"])
tbl(["Part", "Qty", "Material", "Process", "Mass each"], [[b["name"], b["qty"], b["material"], b["process"], "%s g" % f0(b["mass_each_g"]) if b["mass_each_g"] >= 100 else "%.1f g" % b["mass_each_g"]] for b in bom if b["source"] == "make"])
a("**To buy (%d parts).**\n" % R["counts"]["buy"])
tbl(["Part", "Qty", "Material", "Note"], [[b["name"], b["qty"], b["material"], b["process"]] for b in bom if b["source"] == "buy"])
a("Not modelled, but needed: valve guides and seat inserts (pressed into the head), valve stem seals, O-rings for the liner, crank oil seals, piston pin clips, dowel pins and keyways (they are what would stop wrong-way fitting), injector and rail, sensors, "
  "cover bolts (about 40 x M6), the starter motor and its one-way clutch, radiator and hoses, and the exhaust.\n")

a("## 9. Machining notes\n")
a("The one step that is not plain CNC work: **the two main-bearing bores and the balance-shaft bearing bores are finished in one setup with the upper case and bedplate bolted together**, "
  "so they line up. A local engine shop with a line-boring or honing machine can do this.\n")
tbl(["Feature", "Target"], [
    ["Liner bore", "92.000 +0.010 / 0 mm, plateau-honed, round within 0.005 mm"],
    ["Piston to bore", "0.06 mm clearance; the piston maker's figure governs"],
    ["Main bearing housings", "41.600 mm H6, line-bored with the bedplate fitted, straight within 0.01 mm"],
    ["Balance shaft shell bores", "26.000 mm H7, same setup, 92.00 +/- 0.02 mm behind the crank axis"],
    ["Crank journals", "main 38.000 and pin 36.000 mm, minus 0.020 to 0.030; run-out under 0.02 mm; ground and nitrided"],
    ["Rod big end", "39.000 mm H6 with the cap bolted at full stretch; small end bush 22.02 mm"],
    ["Gear centre distance", "92.00 +/- 0.02 mm"],
    ["Deck height (crank axis to head face)", "149.50 +/- 0.05 mm; 0.05 mm changes the compression ratio by about 0.15"],
])

a("## 10. First start and break-in\n")
for t in ["Turn the engine over by hand with the plug out. Check compression and for leaks before any fuel.",
          "Prime the oil system and check pressure while cranking (starter or drill).",
          "First runs on a test stand, **behind a guard**, with a temporary exhaust and a radiator or heat exchanger. Keep below 8,000 rpm for the first heat cycles.",
          "Step up in rpm in stages. Drain and inspect the oil and filter after every session, and check valve lash after the first two hours.",
          "Do not go near 15,000 rpm until the valve train has been checked with a strobe or a sensor. The model says the margin is small."]:
    a("- " + t)
a("")

a("## 11. Fit in the chassis\n")
iface = R["interface"]
m = iface["mounts"]
a("Engine mounting holes (14 mm, along y): **upper front** at x = %.0f, z = %.0f, and **rear** at x = %.0f, z = %.0f, each on both sides at |y| = %.0f to %.0f. "
  "The crank output flange is on the +y side at y = %.0f to %.0f. Centre of gravity (dry): x %.0f, y %.0f, z %.0f.\n" %
  (m["upper"]["x"], m["upper"]["z"], m["rear"]["x"], m["rear"]["z"], m["upper"]["y_inner"], m["upper"]["y_outer"], P.FLANGE[0], P.FLANGE[1], *iface["cg"]))
if chassis:
    s = chassis["summary"]
    ce = s["engine"]
    a("The chassis in `../engine-chassis` has been refitted to this engine: %d members, %s, smallest safety factor %.2f, smallest gap to the engine %.0f mm.\n" %
      (s["members"], "isostatic" if s["redundant_members"] == 0 else "%d redundant" % s["redundant_members"], min(s["min_sf_yield"], s["min_sf_buckle"]), s["min_gap_to_engine_mm"]))
    a("In the bike the crank axis sits at x = %.0f, z = %.0f (same height as the wheel axles). The engine hangs from the four ears on M12 through-bolts with spacers, so the alternator side (bike's right) can bulge out without touching the frame. "
      "The output flange faces the bike's left, which suits a chain drive on that side. The chassis treats the engine as dead weight (%.1f kg wet plus %.0f kg of exhaust, radiator and wiring, plus a %.0f kg allowance for the gearbox or CVT). "
      "**Its shake is not analysed in the frame**: about %.1f tonnes-force at 15,000 rpm remains after balancing, nearly all at twice engine speed. Use rubber mounts or run at low rpm first.\n" %
      (ce["origin_mm"][0], ce["origin_mm"][2], ce["wet_kg"], ce["extras_kg"], ce["drivetrain_allowance_kg"], R["balance"]["peak_with"] / 9806.65))

a("## 12. Files\n")
tbl(["File", "What it is"], [
    ["`engine.step`", "the full assembly, every piece named"],
    ["`parts/*.step`", "one file per machined part, for quotes"],
    ["`bom.csv`", "parts list with material, process, quantity and mass"],
    ["`preview.html`", "the 3D viewer (published as an artifact)"],
    ["`params.py`, `calc.py`", "every dimension, and the physics"],
    ["`p_*.py`, `assembly.py`, `checks.py`, `build.py`", "the CAD builders, the checks and the exporter"],
    ["`results.json`, `interface.json`", "all results, and the numbers the chassis reads"],
])
a("Rebuild everything with `python build.py && python build_preview.py && python gen_spec.py` (needs numpy and cadquery).")
open(os.path.join(d, "SPEC.md"), "w").write("\n".join(L) + "\n")
print("SPEC.md written,", len(L), "lines")
