# Build and inspection checklist

## Before ordering
- [ ] Confirm the tube: ERW mild steel 19 x 1.6 mm (37 pcs), 28 x 2 mm (1), 50 x 3 mm (1). Ask for mill test certificates if available.
- [ ] Get 2 to 3 written quotes for cutting, jig, welding and coating (see `../FABRICATION.md`).
- [ ] Decide who cuts the tubes: a tube-laser shop (send `tubes/*.step` and `tube_table.csv`) or the welder by hand (send `notch_templates.pdf`).

## Cutting
- [ ] Cut each tube square to the **long side** in `tube_table.csv` (kerf included in the length, tolerance +-0.5 mm), then cope the ends. Mark the reference line along each tube first.
- [ ] Plates: laser cut from `plates.dxf` (6 mm mild steel). Four lug plates (two patterns), two pivot plates, two peg plates, one shock plate.
- [ ] Spacers: 4 pieces of 24 mm tube with a 13 mm bore, cut square to the length in `BOM.csv` (about 49 mm); face both ends flat.

## Jig and fit-up
- [ ] Set node posts on a flat table from `jig_table.csv` (table x, table y, post height). Clamp tubes at the node points.
- [ ] Tack the head tube HT-HB and the pivot tube DL-DR first, then each side, then the cross tubes (CL-CR) and node M. Check fit-up gaps (1 mm or less) before welding.
- [ ] Slide the plates onto the tubes at E, F, D and tack them. **Hang a wooden or MDF template of the engine ears (14 mm holes at the engine's mounting positions) from E and F before final welding** so the plate holes line up with the ears.
- [ ] Weld in a balanced order (alternate sides) to limit distortion; full-perimeter welds.

## Inspection (before coating)
- [ ] Node-to-node distances from `drawings.pdf` sheet 5 within +-1.5 mm.
- [ ] No cracks, undercut or missing fusion at any joint; check every node.
- [ ] Engine mount holes: M12 bolts pass through ear, spacer and plate without force.
- [ ] Proof load test by a qualified person before anyone rides.

## Still open (not designed in this project)
- Shock mount at M: the pack has a placeholder plate; a real shock needs a clevis of two plates sized to its eye.
- Swingarm pivot: bearings, bolt and the length of the tube DL-DR beyond the plates; the swingarm itself is not designed.
- Footpeg, brake pedal and gear lever brackets, seat, tank, bodywork, number plate and light mounts.
- Engine shake (about 1.1 tonnes-force at 15,000 rpm, mostly at twice engine speed) is not in the analysis: use rubber-bushed mounts or run at low rpm first.
- No weld, fatigue, lateral-load or crash analysis. This is not a certified motorcycle frame.
