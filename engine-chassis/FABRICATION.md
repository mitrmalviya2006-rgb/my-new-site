# Getting the frame built (India)

The frame is a **welding job, not CNC machining**: 39 straight tubes (37 x 19x1.6 mm, 1 x 28x2 pivot tube, 1 x 50x3 head tube, about 9.3 kg), 9 plates of 6 mm mild steel, 4 spacer tubes. JLCCNC-type machining services are the wrong tool for it.

## Where to go (best first)

1. **Local tube-frame fabricator with TIG or MIG and a jig table.** Search for "chassis fabrication", "go-kart / BAJA SAE / roll-cage fabrication" and "custom motorcycle frame builder" near you. Such shops cluster in Pune, Bengaluru, Chennai, Coimbatore, Delhi NCR, Ahmedabad and Mumbai. Custom-bike shops such as Singh Precisions (Delhi) and J&D Custom Co. (Vadodara) advertise hand-built frames; I could not verify their quality, so ask for photos of frames they have built and which welding process they use.
2. **Tube laser cutting + a welder (better accuracy).** IndiaMART lists tube laser cutting job work in many cities (listed prices of about Rs 50 per piece or Rs 25 per minute are unverified advertisements). The laser shop cuts and copes the 39 tubes, the welder only assembles. Check that they handle 19 x 1.6 mm and can cut the end angles in `cutlist.csv`.
3. **Plates:** any local laser or waterjet shop, from `frame.dxf` (plate flat patterns at the bottom of the drawing). JLCCNC sheet metal can cut plates, but I found no tube cutting there and could not confirm shipping to India: check their site first.
4. **Avoid for a first prototype:** overseas tube-frame fabricators (shipping, duty, no way to inspect a weld before it arrives).

Get two or three written quotes. The earlier Rs 8,000 to 20,000 figure was a guess; a shop that builds a proper jig will cost more.

## What to send

| File | Use |
|---|---|
| `frame.step` | 3D model (tubes are node-to-node cylinders, not yet coped; engine boxes are only for reference) |
| `frame.dxf` | side, top and front wireframes and plate flat patterns |
| `cutlist.csv` | each tube: size, centreline length, cut length, end angles, which tube each end is coped onto |
| `SPEC.md` | node coordinates (section 4) and fabrication notes |

## Quote request (copy and paste)

> Hello, I need one prototype motorcycle frame built to the attached drawings: 39 mild-steel ERW tubes (37 x 19x1.6 mm, 1 x 28x2 mm, 1 x 50x3 mm), 9 plates 6 mm, 4 spacer tubes. All tube ends coped to fit, jig-built, TIG or MIG welded, node positions within +-1 mm of the drawing. Please quote cutting, jig, welding and powder coating separately, tell me which welding process you use, and send photos of similar frames you have built. Delivery to <city>.

Hinglish: "Mujhe ek prototype motorcycle frame banwana hai, drawings attached hain: 39 mild-steel tubes, 9 plates 6 mm, 4 spacer. Tube ends coped, jig pe weld (TIG ya MIG), node positions +-1 mm. Cutting, jig, welding aur powder coat ka alag-alag rate bataiye, aur pehle ke frames ki photos bhejiye."

## Fabricator checklist

- Build on a flat jig, in the order given in `SPEC.md` section 7.
- Check the node coordinates (SPEC.md section 4) and the diagonals before final welding.
- **Hang a wooden or MDF template of the engine ears from E and F before final welding** so the lug plates line up with the engine: ear holes 14 mm, spacers about 49 mm, M12 bolts.
- Weld inspection (no cracks, full penetration at the joints) and a proof load test by a qualified person before anyone rides it.

## Legal note

A one-off home-built motorcycle is hard to register for road use in India. Plan for track or private-land testing first, and check with your local RTO before building for the road.
