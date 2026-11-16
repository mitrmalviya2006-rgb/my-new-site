"""
Single source of truth for the 349 cc engine (mm, kg, N, s, degrees).

Engine frame: x forward, y left, z up (right-handed). Origin = crank axis, on the cylinder axis.
Sides are named by function: the OUTPUT side (+y) carries the gear cover, pumps and output flange and faces the
bike's LEFT when the engine is installed as in the chassis; the ALTERNATOR side (-y) carries the cam chain and alternator
and faces the bike's RIGHT.
The crank axis runs along y; the cylinder axis is vertical (z).
theta = crank angle measured from gas-exchange TDC (0), firing TDC = 360.
"""
import math

# ---------------------------------------------------------------- targets
RPM_REDLINE = 15000
RPM_CHECK = 16500          # 110 % overspeed check for valvetrain and rods
CR_TARGET = 13.5

# ---------------------------------------------------------------- cylinder
BORE = 92.0
STROKE = 52.5
ROD = 95.0                 # centre to centre
R = STROKE / 2.0
LAM = R / ROD
VD_CC = math.pi / 4 * BORE ** 2 * STROKE / 1000.0

# ---------------------------------------------------------------- piston, pin
CH = 28.0                  # pin centre to flat crown reference
PISTON_D = BORE - 0.06
SKIRT_BELOW_PIN = 18.0
PIN_D, PIN_BORE, PIN_LEN = 22.0, 13.0, 66.0
BOSS_R = 16.5              # pin boss outer radius
BOSS_Y_IN = 11.5           # inner face of each boss (|y|)
CROWN_CEIL = 17.0          # underside ceiling above the pin axis
RING_GROOVES = [(3.6, 0.9), (6.6, 1.0), (9.8, 2.2)]   # (depth below crown, width)
DECK_CLEAR = 0.25          # crown below liner top at TDC
GASKET_T = 0.35

Z_PIN_TDC = R + ROD
Z_CROWN_TDC = Z_PIN_TDC + CH
Z_DECK = Z_CROWN_TDC + DECK_CLEAR
Z_HEAD_DECK = Z_DECK + GASKET_T

# ---------------------------------------------------------------- connecting rod
ROD_BIG_BORE = 39.0        # journal 36 + two 1.5 mm shells
ROD_BIG_OR = 25.5
ROD_BIG_W = 21.0
ROD_SMALL_BORE = 24.0
ROD_SMALL_OR = 17.5
ROD_SMALL_W = 22.0
ROD_BEAM_X, ROD_BEAM_Y = 19.0, 19.0
ROD_WEB_T, ROD_FLANGE_T = 5.0, 5.5
ROD_BOLT_X = 27.0
ROD_BOLT_D = 11.11          # 7/16-20 UNF premium rod bolts
ROD_LUG_HALF = 9.0

# ---------------------------------------------------------------- crankshaft
MAIN_D = 38.0
MAIN_Y = (33.5, 53.5)      # |y| range of each main journal
MAIN_SHELL_T = 1.8
PIN_JOURNAL_D = 36.0
PIN_W = 19.0
ROD_SHELL_T = 1.5
WEB_Y = (11.5, 33.5)       # |y| range of each web (thickness 22)
HUB_R = 25.0
LOBE_R = 20.0
CW_R_CENTRE = 49.5         # counterweight radius at the centre (limited by piston boss clearance at BDC)
CW_R_FLANK_MAX = 58.0      # flank radius limit (case top opening)
CW_HALF_ANGLE = 95.0       # degrees

# crank ends (+y = output side, -y = chain/alternator side)
WALL_Y = 62.0              # case, barrel, head and cover mating plane (|y|)
OUT_NECK_D = 34.0
GEAR_SEAT = (64.0, 76.0, 36.0)       # y0, y1, diameter
SEAL_JOURNAL = (76.0, 90.0, 40.0)
FLANGE = (90.0, 100.0, 72.0)         # y0, y1, diameter (bolt-on output flange)
FLANGE_BOLT_PCD, FLANGE_BOLT_N, FLANGE_BOLT_D = 56.0, 6, 8.0     # outer circle for the clutch, CVT or drive
FLANGE_MOUNT_PCD = 30.0                                          # six M8 bolts into the crank end
ALT_NECK_D = 28.0
SPROCKET_SEAT = (-64.0, -72.0, 20.0)
TRIGGER_SEAT = (-72.0, -78.0, 20.0)
ROTOR_TAPER = (-78.0, -100.0, 20.0)
ALT_END = (-100.0, -120.0, 16.0)

# ---------------------------------------------------------------- balance shaft and gears
BAL_X, BAL_Z = -92.0, 0.0
GEAR_M, GEAR_Z, GEAR_W = 2.0, 46, 12.0      # 46 teeth, module 2 -> pitch dia 92
GEAR_Y = (64.0, 76.0)
BAL_SHAFT_D = 22.0
BAL_BEARING_Y = (53.5, 62.0)                 # bush length each side (|y|)
BAL_WEIGHT_R = 32.0
BAL_WEIGHT_Y0 = 26.5                         # inner |y| of each half-disc weight; thickness is solved (BAL_T)
BAL_T = 23.7

# ---------------------------------------------------------------- cylinder stack
LINER_ID, LINER_OD = BORE, 98.0
LINER_Z0 = 62.0
LINER_FLANGE = (102.0, 3.0)                  # diameter, thickness
BARREL_R = 60.0
JACKET_R = 55.0
STUD_XY = (58.0, 48.0)
STUD_D = 10.0
STUD_Z0 = 44.0
CASE_TOP_Z = 62.0
CASE_X = (-138.0, 90.0)
CASE_Y = 62.0
SUMP_Z = -100.0
CAVITY_UP, CAVITY_LOW = 77.0, 77.0     # crank chamber radius above / below the split plane
AXIAL_CLEAR = 0.4                       # crank web to bulkhead gap on each side

# ---------------------------------------------------------------- head and valves
HEAD_X = 70.0
VALVE_TILT = 14.0                            # degrees from the cylinder axis, stems lean outward
IN_SEAT = (-21.0, 18.0)                      # x, |y|
EX_SEAT = (21.0, 16.5)
VALVE_IN = dict(d=28.0, stem=4.0, length=74.0, lift=7.0, duration=320.0, mat="Ti-6Al-4V")
VALVE_EX = dict(d=24.0, stem=4.0, length=74.0, lift=6.0, duration=300.0, mat="Ti-6Al-4V (coated)")
RAMP_CRANK, RAMP_H, PROFILE_U1 = 26.0, 0.10, 0.35
LCA_IN, LCA_EX = 112.0, 612.0                # crank angle of max lift (from gas-exchange TDC)
PLUG_WELL_D, PLUG_THREAD_D = 20.0, 10.0
SPRING_POCKET_S0 = 31.0                      # axial position of the spring pocket floor along the valve axis
SPRING_PRELOAD = 110.0                       # N at the seat
SPRING_MARGIN = 1.15                         # spring force / inertia force at RPM_CHECK
TAU_ALLOW = 1000.0                           # MPa, shot-peened Cr-Si spring wire at solid

# cam / follower geometry
CAM_X = 33.0
PIVOT_X = 18.0
CAM_BASE_R = 11.5
CAM_JOURNAL_D = 22.0
CAM_BEARING_Y = (-47.0, 0.0, 47.0)
LASH_CAP_T = 2.5
FOLLOWER_T = 7.2
FOLLOWER_W = 12.0
LASH = 0.2
SHAFT_D = 8.0

# ---------------------------------------------------------------- cam drive (04C roller chain, 6.35 pitch)
CHAIN_PITCH = 6.35
SPROCKET_Z_CRANK, SPROCKET_Z_CAM = 14, 28
SPROCKET_Y = -68.0

# ---------------------------------------------------------------- fluids and misc
OIL_L, COOLANT_L = 1.0, 0.9
RHO = dict(al=2.81e-3, steel=7.85e-3, ti=4.43e-3, bronze=8.8e-3, cu=8.9e-3, nbr=1.2e-3)   # g/mm3


def derived():
    """Geometry that follows from the parameters (valve axes, tips, cam height ...)."""
    t = math.radians(VALVE_TILT)
    z_ridge = Z_HEAD_DECK + (BORE / 2 + 0.5) * math.tan(t)

    def seat_z(x):
        return z_ridge - abs(x) * math.tan(t)

    valves = []
    for kind, v, seat in (("in", VALVE_IN, IN_SEAT), ("ex", VALVE_EX, EX_SEAT)):
        for sy in (1, -1):
            sx = seat[0]
            sgn = -1.0 if sx < 0 else 1.0
            axis = (sgn * math.sin(t), 0.0, math.cos(t))      # from seat towards stem tip
            s = (sx, sy * seat[1], seat_z(sx))
            tip = tuple(s[i] + axis[i] * v["length"] for i in range(3))
            valves.append(dict(kind=kind, side=sy, seat=s, axis=axis, tip=tip, d=v["d"], lift=v["lift"], length=v["length"], stem=v["stem"]))
    z_tip = valves[0]["tip"][2]
    follower_top = z_tip + LASH_CAP_T + 1.1 + FOLLOWER_T
    z_cam = round(follower_top + CAM_BASE_R + LASH, 1)
    tip_x = abs(valves[0]["tip"][0])
    lever = (tip_x - PIVOT_X) / (CAM_X - PIVOT_X)
    return dict(z_ridge=z_ridge, valves=valves, z_tip=z_tip, z_cam=z_cam, tip_x=tip_x,
                lever_ratio=lever, follower_top=follower_top)


if __name__ == "__main__":
    d = derived()
    print("Vd %.2f cc  deck z %.2f  head deck %.2f  ridge z %.2f" % (VD_CC, Z_DECK, Z_HEAD_DECK, d["z_ridge"]))
    print("tip z %.2f tip x %.2f  cam z %.1f  lever ratio %.2f" % (d["z_tip"], d["tip_x"], d["z_cam"], d["lever_ratio"]))
    for v in d["valves"]:
        print(v["kind"], v["side"], [round(a, 2) for a in v["seat"]], [round(a, 2) for a in v["tip"]])
