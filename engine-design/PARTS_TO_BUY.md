# Parts to buy from the aftermarket (349 cc engine)

This is the shopping list for the engine in this folder. The 25 parts to be machined (case, head, crank, rod, covers, cams and so on) are **not** on this list: they come from a machining service using `parts/*.step`.

**Weight check (target under 40 kg):** the design is **26.9 kg dry, 28.7 kg with oil and coolant**. Adding the things on this list that the CAD does not contain (starter, valve guides and seats, seals, injector, sensors, small bolts) is about 2 kg more, so about 31 kg. With a radiator, fan, hoses and exhaust (about 6 kg, my estimate) the engine package is about 37 kg, still under 40 kg. The ECU, battery and wiring are bike parts and are not counted.

**Route:** A = catalogue part, buy as is. B = catalogue part but check the fit and adapt the CAD or the part. C = made to order from our dimensions.

**Order first (priority 1):** piston with rings and pin, valves, springs, rod bolts, and the valve guides and seats. They are made to order and take the longest. Bearing shells wait until the crank is ground.

Makers named are examples of who does this kind of work. I have not checked their current catalogues or prices; ask for quotes. Many of these parts must match custom machined parts, so send each supplier the STEP file or drawing, not just the name.

## Piston and rings

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Forged piston (2618 aluminium) | 1 | 92.0 mm bore, 22 mm pin, 13.5:1 CR dome, ring grooves 0.9 / 1.0 / 2.2 mm, about 256 g | C | 1 | Custom forging from a piston maker (examples: JE, CP-Carrillo, Wiseco, Arias, Vertex). Send them parts/ + crown shape from SPEC; ask them to make the ring set at the same time. |
| Piston ring set | 1 | 92.0 mm, top steel nitrided, second cast iron, 3-piece oil ring | C | 1 | Normally made with the piston |
| Piston pin | 1 | 22 x 13 x 66 mm, case-hardened steel, DLC coated, about 127 g | C | 1 | From the piston maker or a pin specialist |
| Pin circlips / wire locks | 2 | for a 22 mm pin | A | 3 | Not modelled; supplied with some pin kits |

## Valve train

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Intake valve, titanium Ti-6Al-4V | 2 | head 28 mm, stem 4 mm, length 74 mm, lift 7.0 mm, about 17 g | C | 1 | Custom valve maker (examples: Ferrea, Del West, Supertech, Manley). Ask about the stem coating and seat-face hardening |
| Exhaust valve, titanium Ti-6Al-4V, coated | 2 | head 24 mm, stem 4 mm, length 74 mm, lift 6.0 mm, about 13 g | C | 1 | Same maker |
| Valve spring, outer (intake x2, exhaust x2) | 4 | intake: wire 3.3, mean dia 16.5, 3.6 active coils; exhaust: wire 3.0, mean dia 15.0, 3.6 active coils; Cr-Si, shot-peened | C | 1 | Custom spring maker (examples: Kelford, Pac Racing, Supertech). Seat force 110 N, full-lift force 827 N intake / 670 N exhaust |
| Valve spring, inner (intake x2, exhaust x2) | 4 | intake: wire 2.0, mean dia 8.0, 10.1 active coils; exhaust: wire 1.8, mean dia 7.0, 10.8 active coils | C | 1 | Same maker, same order |
| Spring retainer, titanium | 4 | for 4 mm stem, about 2.2 g each | B | 2 | Order with the valves so the keeper groove matches |
| Valve keepers (collets) | 4 | for 4 mm stem, matched to the retainer | B | 2 | Same order |
| Lash caps / shims | 4 | hardened steel, thickness range for 0.10-0.20 mm cold lash | B | 2 | Buy a shim set in a few thicknesses |
| Follower pivot shaft (ground steel) | 2 | per follower_shaft design, hardened and ground | C | 2 | A ground-shaft shop, or CNC then grind. Not a catalogue part |
| Valve guides and seat inserts | 4 | bronze guides and hard seat inserts for 28 / 24 mm titanium valves, pressed into the head | B | 1 | Not modelled; ask the valve maker which guide and seat materials suit titanium. The head must be machined to their sizes first |
| Valve stem seals | 4 | for 4 mm stem | A | 3 | Not modelled |

## Bearings

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Main bearing shells, upper and lower | 4 | 38 mm journal, 20 mm wide, 1.8 mm tri-metal | B | 2 | Order only after the crank is ground (shell size depends on it). Bearing makers (examples: Clevite, King, ACL) can make a semi-custom size |
| Connecting-rod shells, upper and lower | 2 | 36 mm pin, 19 mm wide, 1.5 mm tri-metal | B | 2 | Same, after the crank is ground and the rod is bored |
| Small-end bush (bronze) | 1 | for the 22 mm pin, per rod drawing | B | 2 | Ask the rod machinist; a standard bronze bush can be pressed in and honed |
| Balance-shaft bearing shells, upper and lower | 4 | 22 mm shaft, 8.5 mm long each side | B | 2 | Bronze or tri-metal sleeve bearings; semi-custom |

## Fasteners

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Connecting-rod bolts 7/16-20 | 2 | premium alloy steel, length to the rod drawing | B | 1 | ARP-type rod bolts (an ARP 2000 or Custom Age 625+ part with matching length). Stretch figure goes with them |
| Head studs M10 x 228, grade 12.9 | 4 | with 4 nuts and 4 hardened washers | A | 2 | Any good fastener supplier; rolled thread preferred |
| Main-cap bolts M10, grade 12.9 | 4 | length per bedplate drawing | A | 2 |  |
| Case bolts M8, grade 12.9 | 12 |  | A | 2 |  |
| Output flange bolts M8, grade 12.9 | 6 |  | A | 2 |  |
| Cam ladder bolts M6, grade 10.9 | 8 |  | A | 2 |  |
| Oil pan bolts M6, grade 10.9 | 12 |  | A | 2 |  |
| Cover and misc. bolts M6 with washers | 40 | about 40 for the covers, pump cover, plugs (not modelled) | A | 3 | Buy a box of M6 x 12-30 mm stainless or 10.9 |
| Dowel pins | 6 | for the bedplate, covers and head (not modelled) | A | 3 | Add them to the drawings first |

## Cam drive

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Cam chain ISO 04C-1 (ANSI 25), 112 links with master link | 1 | 6.35 mm pitch | A | 2 | Any roller chain maker (examples: Tsubaki, DID, Renold) |
| Chain tensioner | 1 | spring-loaded, per chain_tensioner | B | 2 | Adapt a motorcycle cam-chain tensioner or make it |

## Head and gaskets

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| MLS head gasket, 3 layers | 1 | 92 mm bore, cut from the head and barrel faces | C | 2 | A gasket maker (example: Cometic) cuts one from a DXF |
| O-rings, liner and coolant passages, crank oil seals (2) | 1 | set, sizes from the final drawings (not modelled) | A | 3 | Nitrile or Viton O-ring set; double-lip crank seals |

## Oil system

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Gerotor oil pump rotors, inner and outer | 1 | sintered steel, about 3.6 cc per revolution | B | 2 | Catalogue gerotor set of this displacement, or sintered-part maker. Check the pump pocket matches |
| Spin-on oil filter | 1 | small motorcycle filter, check boss thread | B | 3 | Choose the filter first, then set the oil-filter boss thread in the CAD to match |
| Oil: 1.0 L synthetic 10W-40 or 10W-50 (racing) | 1 | plus assembly lube | A | 3 |  |

## Fuel and ignition

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Throttle body 44 mm with throttle position sensor | 1 | single, with injector boss | B | 2 | Sport-bike throttle body (examples: Keihin, Mikuni, Bosch style); check the flange and port |
| Fuel injector | 1 | about 200-250 cc/min (my estimate for about 45 hp) | A | 2 | Bosch-style injector; confirm flow with the ECU maker |
| Fuel pump, rail, pressure regulator, fuel filter | 1 | set | A | 3 | Motorcycle EFI kit |
| Spark plug M10, iridium | 1 | reach to match the head (check the thread length in the head) | B | 2 | Sport-bike plug (examples: NGK, Denso) |
| Ignition coil, coil-on-plug | 1 | pencil coil that fits the 20 mm plug well | B | 2 | Motorcycle coil-on-plug |
| Standalone ECU (single cylinder, 15,000 rpm capable) | 1 | reads a 36-2 crank wheel, one injector, one coil, wideband, 36-2 at 15,000 rpm is a 9 kHz tooth signal | A | 2 | Check the ECU's maximum rpm and tooth rate |
| Crank position sensor (VR or Hall) | 1 | for the 36-2 trigger wheel | A | 2 |  |
| Sensors: coolant temp, air temp, MAP, oil pressure, wideband O2 + bung | 1 | set | A | 3 |  |

## Electrics

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Alternator rotor and stator | 1 | flywheel-type generator, about 740 g rotor and 610 g stator (as modelled) | B | 2 | Pick a catalogue generator first (rotor OD and taper) and update the cover and crank taper in the CAD |
| Regulator/rectifier, battery, wiring harness | 1 |  | A | 3 | Not part of the engine mass |
| Starter motor, one-way clutch and gears | 1 | not modelled; about 1.5-2.5 kg together (my estimate) | B | 2 | Take from a small motorcycle; the engine needs a starter boss and gear mesh added |

## Cooling

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Radiator (aluminium), electric fan, cap | 1 | heat to coolant about 40 kW at full power (calculation) | A | 2 | Motorcycle or small-car radiator with an electric fan |
| Thermostat and housing, hoses, clamps, overflow bottle | 1 | water-pump flow about 105 L/min from the 36 mm impeller | A | 3 |  |
| Coolant 0.9 L + radiator volume | 1 | 50:50 ethylene glycol | A | 3 |  |

## Exhaust

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Header and silencer | 1 | exhaust flange at engine x = 70, z = 185 (see interface.json); about 40 mm bore header | C | 3 | Made by an exhaust fabricator to the bike layout; include an O2 sensor bung |

## Consumables and tools

| Item | Qty | Specification | Route | Prio | Where / note |
|---|---|---|---|---|---|
| Threadlocker, anaerobic flange sealant, RTV, assembly lube, Plastigage | 1 |  | A | 3 |  |
| Torque wrench (5-100 N.m), piston ring compressor, cam timing pin, dial gauge | 1 | special tools used in the assembly steps | A | 3 |  |

## Fit problems to settle before ordering

- **Alternator, oil filter, throttle body, starter:** the CAD models them as generic shapes. Pick the real catalogue part first, then change the cover pocket, boss thread or flange in the CAD (`params.py`, `p_static.py`) and rebuild with `build.py`.
- **Valve guides and seats** go into the head, so the head cannot be finished until the valve maker confirms the sizes.
- **Bearing shells** are sized from the finished crank and rod; order after grinding and measuring.
- **Dowels and keyways** are not in the CAD yet (see the report); add them before ordering the machined parts.

The same list as a spreadsheet: `parts_to_buy.csv`.
