# 349 cc single-cylinder engine: design report

A small liquid-cooled petrol engine with one cylinder, four valves and a 15,000 rpm redline, drawn as a full 3D assembly of 138 pieces (65 different parts). It is designed to be easy to put together and to have as few parts as it can get away with. The clutch, gearbox or CVT are **not** part of it: the crank ends in a bolt-on output flange so any of them can be added later.

Axes used everywhere: x forward, y left, z up, origin at the crank axis, millimetres. Sides are named by what is on them: the **output side** (+y: gear cover, pumps, output flange) faces the bike's **left** when the engine is installed as in the chassis, and the **alternator side** (-y: cam chain, alternator) faces the bike's **right**. Everything here is a design and a set of hand calculations. Nothing has been built, tested on a dyno or checked with FEA, so treat the numbers as the starting point for testing.

## 1. The engine in numbers

| Item | Value | In plain words |
|---|---|---|
| Displacement | 349.0 cc | the total volume the piston sweeps |
| Bore x stroke | 92.0 x 52.5 mm | cylinder width x how far the piston travels; wide and short so it can spin fast |
| Compression ratio | 13.5 : 1 | how hard the fuel-air mix is squeezed; needs premium petrol |
| Redline | 15,000 rpm | the highest speed the engine is meant to turn |
| Piston speed at redline | 26.3 m/s | racing-class; ordinary road engines stay near 15 to 20 |
| Valves | 2 intake 28 mm, 2 exhaust 24 mm, titanium | four valves, two to breathe in and two to breathe out |
| Power (estimate) | 57 hp at 11,000 rpm | 44 hp at the 15,000 rpm redline; the engine runs out of breath before it runs out of revs |
| Torque (estimate) | 38 N·m at 10,000 rpm | the twisting force |
| Mass, dry | 26.9 kg | engine alone: no radiator, exhaust, ECU, clutch or gearbox; 28.7 kg with oil and coolant |
| Size | 309 x 240 x 396 mm | length x width x height including intake, oil filter and coil |
| Parts | 65 different, 25 to machine, 40 to buy | plus 138 modelled pieces in total |

The power and torque figures come from a simple single-zone combustion model tuned to typical racing-engine values. Expect them to be right within about 15 percent at best. Only a dyno gives real numbers.

## 2. How it is laid out, and why

- **One cylinder, standing upright.** Fewest parts of any layout, and a vertical cylinder is the easiest to machine and to assemble.
- **Four valves with two overhead cams.** Four small valves open faster and breathe better than two big ones. They are lighter, which matters at 15,000 rpm.
- **Finger followers between the cams and the valves.** They are lighter than the bucket-shaped followers used in many engines, so the valve springs can keep up at high speed.
- **A one-piece crankshaft on plain (sliding) bearings.** No pressed-together crank and no roller bearings. The rod and the crank run on thin replaceable shell bearings, as in most modern sports-bike engines.
- **Cases that stack in one direction.** Bedplate, upper case, cylinder barrel, gasket, head, cam ladder and cover are built up like a layer cake. Four long studs clamp the barrel and head to the upper case, so there are very few bolts.
- **A wet liner.** The cylinder wall is a separate steel tube with coolant flowing round it. It can be replaced, and the aluminium barrel needs no special coating.
- **One balance shaft that does three jobs.** It cancels most of the shaking a single cylinder makes, and the same shaft drives the water pump at one end and the oil pump at the other. No extra pump drives.
- **The crank carries its own gear and the balance gear sits on the shaft.** Both gears are on the output side, under one cover.
- **A bolt-on output flange** on the output end of the crank. The clutch, the CVT you asked about, or a gearbox can bolt straight to it.
- **Chain drive for the cams, coil on plug, wet sump, fuel injection.** All standard, catalogue-type parts.
- **Only three bolt sizes for the structure (M6, M8, M10)**, plus the rod bolts and the output flange bolts.

## 3. Do the numbers hold up? (all checks)

| Check | Result | Limit |  | How |
|---|---|---|---|---|
| Rod journal peak pressure | 129.05 MPa | 140 | pass | 36 x 19 mm Cu-Pb tri-metal shell, peak limit about 140 MPa |
| Shaking force with balance shaft | 10,932 N | 25,542 | pass | unbalanced 72976 N, counterweights only 29153 N |
| Rod buckling safety factor | 39.73 | 2 | pass | Euler, pinned ends, peak gas load |
| Rod fatigue safety factor (Goodman) | 1.56 | 1.5 | pass | 42CrMo4 Q&T, shot-peened, 16,500 rpm |
| Rod bolt preload safety factor | 2.06 | 2 | pass | 7/16-20 premium bolts at 70% of yield, 16,500 rpm |
| Head stud preload vs gas load | 2.63 | 2 | pass | 4 x M10 12.9 |
| Piston pin bending safety factor | 1.77 | 1.6 | pass | 22 x 12 mm case-hardened pin |
| Valve spring intake force / inertia at 16500 rpm | 1.31 | 1.15 | pass | m_eff 35.2 g, spring 827 N at full lift |
| Valve float onset, intake (lumped dynamic model) | 16,000 rpm | 15,000 | pass | first rpm with loss of cam contact; indicative only |
| Valve spring exhaust force / inertia at 16500 rpm | 1.3 | 1.15 | pass | m_eff 28.8 g, spring 670 N at full lift |
| Valve float onset, exhaust (lumped dynamic model) | 15,500 rpm | 15,000 | pass | first rpm with loss of cam contact; indicative only |
| Chain speed at redline | 22.23 m/s | 30 | pass | 04C chain, 14 teeth on the crank |
| Piston speed at redline | 26.25 m/s | 27 | pass | racing class above about 22 |
| Swept volume from CAD (bore 92.00 mm x stroke 52.50 mm) | 349 cc | 349 | pass | liner slice and crank pin offset |
| Compression ratio from CAD volumes | 13.5 | 13.5 | pass | chamber 27.92 cc, crown gap 4.00 mm |
| Crank counterweight moment vs target | 17,761 g*mm | 18,138 | pass | flank radius 58.0 mm |
| Balance weight moment vs target | 7,385 g*mm | 7,367 | pass | 22.5 mm thick each |
| Overlaps between parts (assembled pose) | 0 pairs | 0 | pass | intersection volume > 1 mm3 |
| Moving parts vs case and liner, 36 crank angles | 0 interferences | 0 | pass | crank, rod, bolts, piston, balance shaft |
| Minimum gap, crank to case | 0.4 mm | 0.3 | pass | axial gap to bulkheads is the smallest |
| Minimum gap, rod and bolts to case | 1.95 mm | 1 | pass | sweep at 30 degree steps |
| Piston to valve clearance through overlap | 4.2 mm | 1.5 | pass | worst at crank angle 0 deg |
| Assembly moves without interference | 23 of 23 | 23 | pass | each part or sub-assembly slid in along one straight line |
| Engine mass (dry, no radiator, exhaust, ECU) | 26.91 kg | 40 | pass | target from the chassis: 60 kg including ancillaries |

All 24 checks pass.
Two limits are tight and worth knowing about: the exhaust valve train starts to lose contact at about 15,500 rpm in the model (only 3% above the redline), and the rod journal sees about 129 MPa at the peak of the firing stroke against a limit of 140.

## 4. What changed from the plan, and why

- **Valves are 28 mm intake and 24 mm exhaust, both titanium**, not 30 and 25 mm with steel exhaust valves. In the first spring sweep a hollow steel 24 mm exhaust valve needed about 840 N of spring force at 16,500 rpm against about 570 N for titanium, which is more than a spring of this size can safely give. Smaller, lighter valves keep the valve train under control.
- **The power peaks at about 11,000 rpm, not at 13,500 to 14,000 rpm.** The smaller valves restrict breathing at high speed, so the engine reaches 15,000 rpm but makes only about 44 hp there. In practice a shift point around 12,500 to 13,000 rpm would use the engine best.
- **The crank webs are 22 mm thick** and the case is 4 mm wider than first sketched. The counterweights need to be that big to balance a 431 g piston and pin. Without it the only way is tungsten inserts, which cost more and add parts.
- **The case top is 62 mm above the crank axis** instead of 36 mm, so the counterweights never swing up into the cylinder bore.
- **The crank gear is cut into the crank itself and the output flange bolts on.** Otherwise the gear and the gear cover could not be fitted.
- **Rod bolts are 7/16 inch**, the piston pin is 22 mm and the rod beam is 19 x 19 mm, all sized up once the real CAD masses were known (the reciprocating mass came out at 561 g).

## 5. Valves, cams and springs

|  | Intake | Exhaust |
|---|---|---|
| Valve diameter | 28 mm x 2 | 24 mm x 2 |
| Lift | 7.0 mm | 6.0 mm |
| Open duration (crank degrees) | 320 | 300 |
| Lobe centre (crank degrees after gas-exchange TDC) | 112 | -108 |
| Moving mass at the valve | 35.2 g | 28.8 g |
| Spring force, seat / full lift | 110 / 827 N | 110 / 670 N |
| Outer spring (wire x mean diameter x active coils) | 3.3 x 16.5 x 3.6 | 3.0 x 15.0 x 3.6 |
| Inner spring | 2.0 x 8.0 x 10.1 | 1.8 x 7.0 x 10.8 |
| Valve train loses cam contact from (model) | 16,000 rpm | 15,500 rpm |
| Seating speed at 15,000 rpm | 0.43 m/s | 0.40 m/s |

Spring wire is Cr-Si, shot-peened, worked to about 1,000 MPa at full compression. The springs in the 3D model are drawn as plain tubes. The lever ratio of the finger followers is 1.39 and each follower swings about 20 degrees at full lift. The spring surge frequency is only 7.6 to 8.4 times the cam frequency, so a cam profile with little high-frequency content and a damped inner spring matter. Lash (cold): 0.10 to 0.15 mm intake, 0.15 to 0.20 mm exhaust, set with the lash caps.

## 6. Balance (the shaking)

A single cylinder shakes itself. At 15,000 rpm the moving piston and rod would shake the engine with a peak force of about 7.4 tonnes-force if nothing were balanced. The crank counterweights bring that to about 3.0 tonnes-force, and the balance shaft to about 1.1 tonnes-force. The part that is left is the shake at twice engine speed, which a single balance shaft cannot remove. It shows up as a high buzz that the frame and the mounts have to live with.

Counterweight moment 17.8 kg·mm (target 18.1), flank radius 58.0 mm. Balance weights 22.5 mm thick each, moment 7.4 kg·mm (target 7.4).

## 7. How to assemble it

Twelve steps. Every part goes in along one straight line, and the only special tools are a torque wrench, a cam-timing mark or pin, and a piston ring compressor. One honest gap: **dowel pins and keyways that would make a wrong fit impossible (case halves, covers, balance-shaft phase, cam timing) are not modelled yet.** Today the model proves each part can go in along its path; it does not stop you fitting a part the wrong way round. Add dowels and keys before ordering parts.

1. Upper case on a stand. Press the upper main shells and balance-shaft shells into their saddles.
2. On the bench: fit the rod shells and bush, bolt the rod cap onto the crank pin with the two 7/16 rod bolts.
3. Lower the crank and rod from below into the upper case, then the balance shaft (weights down).
4. Fit the lower shells, set the bedplate on the upper case (add two dowel pins here in the real build, not modelled yet), fit and torque the M10 main-cap bolts and M8 case bolts.
5. Set the piston on the rod small end from above, push the pin in from the side, fit the rings.
6. Press the liner into the barrel, lower the barrel over the piston (ring compressor), then the head gasket.
7. Head with valves, springs, retainers and keepers built on the bench; lower it onto the four studs, washers and nuts.
8. Set the four followers on the valve tips, slide in the pivot shafts, lower the cams, fit the ladder and its bolts.
9. Cam cover, spark plug and coil.
10. Output side (+y, the bike's left): balance gear onto the shaft, water impeller, gear cover and pump cover, then the output flange.
11. Alternator side (-y, the bike's right): oil pump rotors, crank sprocket, cam sprockets, chain with master link, guide, tensioner, trigger wheel, rotor, chain and alternator cover with stator.
12. Oil pan, oil filter and throttle body.

Each move was checked in the 3D model by sliding the part along its path and testing for any contact (23 moves, none blocked).

| Fastener | Starting torque (confirm with the fastener supplier) |
|---|---|
| M10 head studs, nuts, main-cap bolts | 70 N·m, oiled threads |
| M8 case bolts and output flange bolts | 25 N·m |
| M6 bolts (oil pan, ladder, covers) | 10 N·m |
| Rod bolts 7/16-20 | to the bolt maker's stretch figure (about 0.17 mm), not by torque |

## 8. Parts list

**To machine (25 parts).** Aluminium parts are 7075-T6 or 6061-T6 billet, which a CNC service such as JLCCNC can quote from the STEP files in `parts/`. The crank, rod, balance shaft and gears need heat treatment and grinding at a local shop afterwards.

| Part | Qty | Material | Process | Mass each |
|---|---|---|---|---|
| Balance gear (46T, m2) | 1 | Case-hardened steel | CNC + grind | 581 g |
| Cam sprocket (28T) | 2 | Steel, hardened | CNC | 99.2 g |
| Chain guide | 1 | Steel + polymer pad | CNC | 55.1 g |
| Crank sprocket (14T) | 1 | Steel, hardened | CNC | 14.1 g |
| Water pump impeller | 1 | Al 6061 | CNC | 5.9 g |
| Trigger wheel (36-2) | 1 | Steel | CNC | 128 g |
| Connecting rod | 1 | 42CrMo4, shot-peened | CNC 5-axis, hone | 298 g |
| Rod cap | 1 | 42CrMo4, shot-peened | CNC 5-axis, hone | 126 g |
| Balance shaft | 1 | 42CrMo4, nitrided | CNC turn-mill, grind | 971 g |
| Crankshaft (one piece) | 1 | 42CrMo4, nitrided | CNC 5-axis, heat treat, grind | 3,854 g |
| Output flange (bolt-on) | 1 | 42CrMo4 | CNC turn-mill | 267 g |
| Upper crankcase | 1 | Al 7075-T6 | CNC 5-axis + line bore | 3,082 g |
| Bedplate (main caps) | 1 | Al 7075-T6 | CNC + line bore with upper case | 1,815 g |
| Cylinder barrel | 1 | Al 7075-T6 | CNC turn-mill | 867 g |
| Cylinder liner (wet) | 1 | 42CrMo4, nitrided | CNC turning, nitride, hone | 611 g |
| Cylinder head | 1 | Al 7075-T6 | CNC 5-axis | 3,746 g |
| Cam ladder (bearing caps) | 1 | Al 7075-T6 | CNC 3-axis | 347 g |
| Cam cover | 1 | Al 6061-T6 | CNC 3-axis | 472 g |
| Gear and pump cover (bike's left side) | 1 | Al 6061-T6 | CNC 3-axis | 575 g |
| Water pump cover | 1 | Al 6061-T6 | CNC 3-axis | 86.3 g |
| Chain and alternator cover (bike's right side) | 1 | Al 6061-T6 | CNC 3-axis | 1,803 g |
| Oil pan | 1 | Al 6061-T6 | CNC 3-axis | 1,349 g |
| Exhaust camshaft | 1 | Steel, DLC | CNC, harden, grind | 391 g |
| Finger follower | 4 | Steel, DLC | CNC, grind | 18.5 g |
| Intake camshaft | 1 | Steel, DLC | CNC, harden, grind | 395 g |

**To buy (40 parts).**

| Part | Qty | Material | Note |
|---|---|---|---|
| Cam roller chain 04C, 112 links | 1 | Roller chain | Buy |
| Chain tensioner | 1 | Steel + spring | Buy / CNC |
| Oil pump inner rotor | 1 | Sintered steel | Buy |
| Oil pump outer rotor | 1 | Sintered steel | Buy |
| Oil filter (spin-on) | 1 | - | Buy |
| Main cap bolt M10 | 4 | 12.9 steel | Buy |
| Case bolt M8 | 12 | 12.9 steel | Buy |
| Nut M10 | 4 | 12.9 steel | Buy |
| Head stud M10 x 228 | 4 | 12.9 steel | Buy |
| Washer M10 | 4 | Hardened steel | Buy |
| Ladder bolt M6 | 8 | 10.9 steel | Buy |
| Output flange bolt M8 | 6 | 12.9 steel | Buy |
| Oil pan bolt M6 | 12 | 10.9 steel | Buy |
| Coil-on-plug | 1 | - | Buy |
| Spark plug M10 | 1 | Iridium | Buy |
| Alternator rotor | 1 | Steel + magnets | Buy |
| Alternator stator | 1 | Laminations + copper | Buy |
| Throttle body 44 mm | 1 | Al | Buy |
| Balance shaft shell, upper | 2 | Tri-metal | Buy |
| Main shell, upper | 2 | Tri-metal | Buy |
| Rod bolt 7/16-20 | 2 | Premium alloy steel | Buy (ARP-type) |
| Rod shell, lower | 1 | Tri-metal | Buy |
| Rod shell, upper | 1 | Tri-metal | Buy |
| Small-end bush | 1 | Bronze | Buy |
| Balance shaft shell, lower | 2 | Tri-metal | Buy |
| Main shell, lower | 2 | Tri-metal | Buy |
| Piston (forged) | 1 | Al 2618 forged | Buy (custom forging) |
| Piston pin | 1 | Case-hardened steel, DLC | Buy |
| Oil ring | 1 | Steel rails + expander | Buy |
| Second ring | 1 | Cast iron | Buy |
| Top ring | 1 | Steel, nitrided | Buy |
| Head gasket (MLS) | 1 | Stainless MLS, 3 layers | Laser cut, buy |
| Keepers | 4 | Steel | Buy |
| Spring retainer | 4 | Ti-6Al-4V | Buy |
| Valve spring, inner | 4 | Cr-Si wire, peened | Buy (custom) |
| Valve spring, outer | 4 | Cr-Si wire, peened | Buy (custom) |
| Exhaust valve | 2 | Ti-6Al-4V, coated | Buy (custom) |
| Intake valve | 2 | Ti-6Al-4V | Buy (custom) |
| Follower pivot shaft | 2 | Steel, ground | Buy / CNC |
| Lash cap (shim) | 4 | Steel, hardened | Buy |

Not modelled, but needed: valve guides and seat inserts (pressed into the head), valve stem seals, O-rings for the liner, crank oil seals, piston pin clips, dowel pins and keyways (they are what would stop wrong-way fitting), injector and rail, sensors, cover bolts (about 40 x M6), the starter motor and its one-way clutch, radiator and hoses, and the exhaust.

## 9. Machining notes

The one step that is not plain CNC work: **the two main-bearing bores and the balance-shaft bearing bores are finished in one setup with the upper case and bedplate bolted together**, so they line up. A local engine shop with a line-boring or honing machine can do this.

| Feature | Target |
|---|---|
| Liner bore | 92.000 +0.010 / 0 mm, plateau-honed, round within 0.005 mm |
| Piston to bore | 0.06 mm clearance; the piston maker's figure governs |
| Main bearing housings | 41.600 mm H6, line-bored with the bedplate fitted, straight within 0.01 mm |
| Balance shaft shell bores | 26.000 mm H7, same setup, 92.00 +/- 0.02 mm behind the crank axis |
| Crank journals | main 38.000 and pin 36.000 mm, minus 0.020 to 0.030; run-out under 0.02 mm; ground and nitrided |
| Rod big end | 39.000 mm H6 with the cap bolted at full stretch; small end bush 22.02 mm |
| Gear centre distance | 92.00 +/- 0.02 mm |
| Deck height (crank axis to head face) | 149.50 +/- 0.05 mm; 0.05 mm changes the compression ratio by about 0.15 |

## 10. First start and break-in

- Turn the engine over by hand with the plug out. Check compression and for leaks before any fuel.
- Prime the oil system and check pressure while cranking (starter or drill).
- First runs on a test stand, **behind a guard**, with a temporary exhaust and a radiator or heat exchanger. Keep below 8,000 rpm for the first heat cycles.
- Step up in rpm in stages. Drain and inspect the oil and filter after every session, and check valve lash after the first two hours.
- Do not go near 15,000 rpm until the valve train has been checked with a strobe or a sensor. The model says the margin is small.

## 11. Fit in the chassis

Engine mounting holes (14 mm, along y): **upper front** at x = 83, z = 163, and **rear** at x = -125, z = 78, each on both sides at |y| = 62 to 82. The crank output flange is on the +y side at y = 90 to 100. Centre of gravity (dry): x -16, y -6, z 62.

The chassis in `../engine-chassis` has been refitted to this engine: 39 members, isostatic, smallest safety factor 3.16, smallest gap to the engine 22 mm.

In the bike the crank axis sits at x = 300, z = -20 (same height as the wheel axles). The engine hangs from the four ears on M12 through-bolts with spacers, so the alternator side (bike's right) can bulge out without touching the frame. The output flange faces the bike's left, which suits a chain drive on that side. The chassis treats the engine as dead weight (28.7 kg wet plus 9 kg of exhaust, radiator and wiring, plus a 20 kg allowance for the gearbox or CVT). **Its shake is not analysed in the frame**: about 1.1 tonnes-force at 15,000 rpm remains after balancing, nearly all at twice engine speed. Use rubber mounts or run at low rpm first.

## 12. Files

| File | What it is |
|---|---|
| `engine.step` | the full assembly, every piece named |
| `parts/*.step` | one file per machined part, for quotes |
| `bom.csv` | parts list with material, process, quantity and mass |
| `preview.html` | the 3D viewer (published as an artifact) |
| `params.py`, `calc.py` | every dimension, and the physics |
| `p_*.py`, `assembly.py`, `checks.py`, `build.py` | the CAD builders, the checks and the exporter |
| `results.json`, `interface.json` | all results, and the numbers the chassis reads |

Rebuild everything with `python build.py && python build_preview.py && python gen_spec.py` (needs numpy and cadquery).
