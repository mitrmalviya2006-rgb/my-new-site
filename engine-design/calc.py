"""
Engine physics: kinematics, gas and inertia loads, balance, bearings, rod and bolt checks,
valve lift curves, valvetrain spring design and dynamics, gas-flow index, pumps, power estimate.
numpy only, so it runs without CadQuery. Masses can be fed back from the CAD (second pass).
Every result is a hand calculation, not a measurement.
"""
import math
import numpy as np
import params as P

G_SPR = 79.3e3            # N/mm2 spring steel shear modulus
E_STEEL = 205e3           # N/mm2
RHO_STEEL, RHO_TI = 7.85e-3, 4.43e-3   # g/mm3
AP = math.pi / 4 * P.BORE ** 2


# ------------------------------------------------------------------ kinematics
def piston_z(theta_deg):
    t = np.radians(theta_deg)
    return P.R * np.cos(t) + np.sqrt(P.ROD ** 2 - (P.R * np.sin(t)) ** 2)     # pin height above crank axis


def piston_acc(theta_deg, rpm):
    """piston acceleration along z (m/s2), exact by differentiating the position"""
    th = np.asarray(theta_deg, float)
    h = 0.05
    z0, z1, z2 = piston_z(th - h), piston_z(th), piston_z(th + h)
    w = 2 * math.pi * rpm / 60.0
    return (z2 - 2 * z1 + z0) * 1e-3 / (math.radians(h) / w) ** 2


def mean_piston_speed(rpm):
    return P.STROKE * rpm / 30000.0


# ------------------------------------------------------------------ gas pressure (single zone, Wiebe)
def cylinder_pressure(rpm, p_ivc_bar, vc_mm3, ign_btdc=25.0, burn=59.0, heat_frac=0.82, ivc_deg=240.0, evo_deg=478.0):
    """Closed-cycle pressure, bar abs, vs crank angle (0..720 step 1). Returns theta, p_bar, imep_gross_bar."""
    th = np.arange(0.0, 721.0, 1.0)
    z = piston_z(th)
    v = vc_mm3 + AP * ((P.R + P.ROD) - z)                    # mm3
    p = np.full_like(th, 1.0)
    i0 = int(ivc_deg)
    t_ivc = 340.0
    m = p_ivc_bar * 1e5 * v[i0] * 1e-9 / (287.0 * t_ivc)     # kg of charge
    afr = 14.7 * 0.90
    qtot = m / (1 + afr) * 43e6 * 0.95 * heat_frac           # J released (after losses)
    th0 = 360.0 - ign_btdc
    a_w, m_w = 5.0, 2.0
    p[i0] = p_ivc_bar
    work = 0.0
    xb_prev = 0.0
    for i in range(i0, int(evo_deg)):
        x = (th[i] + 0.5 - th0) / burn
        xb = 0.0 if x <= 0 else 1 - math.exp(-a_w * x ** (m_w + 1))
        if x >= 1.4:
            xb = 1 - math.exp(-a_w * 1.4 ** (m_w + 1))
        dq = qtot * (xb - xb_prev)
        xb_prev = xb
        tgas = p[i] * 1e5 * v[i] * 1e-9 / (m * 287.0)
        gam = 1.38 - 0.00006 * (tgas - 300.0)
        gam = max(1.22, gam)
        dv = v[i + 1] - v[i]
        vm = 0.5 * (v[i] + v[i + 1])
        dp = ((gam - 1) / (vm * 1e-9) * dq - gam * p[i] * 1e5 / vm * dv) * 1e-5   # bar per degree step
        p[i + 1] = p[i] + dp
        work += 0.5 * (p[i] + p[i + 1]) * 1e5 * dv * 1e-9
    # exhaust blow-down then back to ~1.1 bar
    for i in range(int(evo_deg), len(th)):
        k = (i - evo_deg) / 40.0
        p[i] = max(1.1, p[int(evo_deg)] * math.exp(-4.0 * k)) if k < 1.2 else 1.1
    for i in range(0, i0):
        p[i] = 1.05 if i < i0 else p_ivc_bar
    imep = work / (P.VD_CC * 1e-6) * 1e-5
    return th, p, imep


# ------------------------------------------------------------------ power estimate
def flow_index(rpm, d_in=None):
    d_in = d_in or P.VALVE_IN["d"]
    ai = 2 * math.pi / 4 * d_in ** 2
    return (AP / ai) * (mean_piston_speed(rpm) / 340.0)


def p_ivc_model(rpm):
    z = flow_index(rpm)
    return 1.0 + 0.55 * math.exp(-((rpm - 10500.0) / 3800.0) ** 2) - 0.9 * max(0.0, z - 0.30)


def fmep_bar(rpm):
    return 0.6 + 0.07 * mean_piston_speed(rpm)


def power_curve(vc_mm3, rpms=None):
    rpms = rpms or list(range(4000, 16001, 1000))
    rows = []
    for rpm in rpms:
        th, p, imep = cylinder_pressure(rpm, p_ivc_model(rpm), vc_mm3)
        pmep = 0.12 + 0.035 * rpm / 1000.0
        bmep = imep - pmep - fmep_bar(rpm)
        kw = bmep * 1e5 * P.VD_CC * 1e-6 * (rpm / 60.0) / 2.0 / 1000.0
        rows.append(dict(rpm=rpm, imep=imep, bmep=bmep, kw=kw, hp=kw * 1.341, nm=kw * 1000.0 / (2 * math.pi * rpm / 60.0),
                         peak_bar=float(p.max()), p_ivc=p_ivc_model(rpm), z=flow_index(rpm)))
    return rows


# ------------------------------------------------------------------ loads on rod and bearings
def rod_loads(rpm, m_rec, m_rot, p_bar, theta):
    """Returns dict with rod axial force (N, +compression), pin load vector magnitude vs theta."""
    a = piston_acc(theta, rpm)
    gas = (np.asarray(p_bar) - 1.0) * 1e5 * AP * 1e-6          # N, net of crankcase pressure
    f_rod = m_rec * a + gas                                     # +compression
    t = np.radians(theta)
    phi = np.arcsin(P.R * np.sin(t) / P.ROD)
    w = 2 * math.pi * rpm / 60.0
    f_cf = m_rot * P.R * 1e-3 * w ** 2                          # centrifugal of rod big end (N)
    # components in x (fwd) and z (up); rod pushes the pin along the rod axis, axis direction from pin to crank
    ux = -np.sin(phi) * -1.0
    # pin position relative to crank axis: (R sin t, R cos t). rod axis unit (pin -> piston) = (-sin phi, cos phi)
    rx, rz = -np.sin(phi), np.cos(phi)
    fx = f_rod * (-rx) * -1.0
    fx = f_rod * rx * -1.0 * -1.0
    # force of the rod on the crank pin = -(rod axis) * compression
    fpx, fpz = -f_rod * rx, -f_rod * rz
    # centrifugal of the big-end mass acts outward along the crank arm
    cx, cz = f_cf * np.sin(t), f_cf * np.cos(t)
    return dict(f_rod=f_rod, pin_x=fpx + cx, pin_z=fpz + cz, pin=np.hypot(fpx + cx, fpz + cz), f_cf=f_cf, gas=gas)


# ------------------------------------------------------------------ balancing
def balance(rpm, m_rec, m_rot, crank_moment_kgmm, bal_moment_kgmm, phi_deg=None):
    """Force on the crankcase (N): x forward, z up, vs crank angle.
    crank_moment: net counterweight moment (positive = heavy side opposite the pin), includes pin and web lobes.
    bal_moment: moment of the counter-rotating balance shaft (both weights)."""
    w = 2 * math.pi * rpm / 60.0
    th = np.arange(0, 360, 1.0)
    t = np.radians(th)
    a = piston_acc(th, rpm)
    f_rec_z = -m_rec * a
    f_rot_x = m_rot * P.R * 1e-3 * w ** 2 * np.sin(t)
    f_rot_z = m_rot * P.R * 1e-3 * w ** 2 * np.cos(t)
    fx0 = f_rot_x - crank_moment_kgmm * 1e-3 * w ** 2 * np.sin(t)
    fz0 = f_rec_z + f_rot_z - crank_moment_kgmm * 1e-3 * w ** 2 * np.cos(t)

    def with_bal(phi):
        pb = np.radians(phi) - t
        return (fx0 + bal_moment_kgmm * 1e-3 * w ** 2 * np.sin(pb), fz0 + bal_moment_kgmm * 1e-3 * w ** 2 * np.cos(pb))
    best = None
    for phi in np.arange(0, 360, 2.0):
        fx, fz = with_bal(phi)
        pk = float(np.max(np.hypot(fx, fz)))
        if best is None or pk < best[0]:
            best = (pk, phi)
    fx, fz = with_bal(best[1])
    # unbalanced reference: no counterweights, no balancer
    fx_u = f_rot_x
    fz_u = f_rec_z + f_rot_z
    return dict(peak_with=float(np.max(np.hypot(fx, fz))), peak_cw_only=float(np.max(np.hypot(fx0, fz0))),
                peak_none=float(np.max(np.hypot(fx_u, fz_u))), phase=best[1],
                primary_unbalanced=float(m_rec * P.R * 1e-3 * w ** 2),
                secondary=float(m_rec * P.R * 1e-3 * w ** 2 * P.LAM))


def balance_targets(m_rec, m_rot):
    """Counterweight moment target (kg*mm, net opposing the pin side) and balance shaft moment."""
    cw = (m_rot + 0.5 * m_rec) * P.R
    bal = 0.5 * m_rec * P.R
    return cw, bal


# ------------------------------------------------------------------ valve events
def valve_profile(L, dur_crank, ramp_crank=None, ramp_h=None, u1=None, n=600):
    """Lift (mm) vs cam angle (rad), full event: constant-velocity ramp blended into a two-sine acceleration rise."""
    ramp_crank = P.RAMP_CRANK if ramp_crank is None else ramp_crank
    ramp_h = P.RAMP_H if ramp_h is None else ramp_h
    u1 = P.PROFILE_U1 if u1 is None else u1
    half_cam = math.radians(dur_crank / 2) / 2
    ramp_cam = math.radians(ramp_crank) / 2
    beta = half_cam - ramp_cam
    v0 = ramp_h * beta / ramp_cam
    dh = L - ramp_h
    a1 = math.pi * (dh - v0 * (1 + u1) / 2) / u1
    v1 = v0 + 2 * a1 * u1 / math.pi
    a2 = math.pi * v1 / (2 * (1 - u1))
    u = np.linspace(0, 1, n)
    du = u[1] - u[0]
    acc = np.where(u < u1, a1 * np.sin(np.pi * u / u1), -a2 * np.sin(np.pi * (u - u1) / (1 - u1)))
    vel = v0 + np.concatenate([[0], np.cumsum((acc[1:] + acc[:-1]) / 2 * du)])
    h = ramp_h + np.concatenate([[0], np.cumsum((vel[1:] + vel[:-1]) / 2 * du)])
    h = h * (L / h[-1])
    phi_r = np.linspace(0, ramp_cam, 30, endpoint=False)
    phi = np.concatenate([phi_r, ramp_cam + u * beta])
    lift = np.concatenate([ramp_h * phi_r / ramp_cam, h])
    phi_full = np.concatenate([phi, (2 * half_cam - phi[::-1])[1:]])
    lift_full = np.concatenate([lift, lift[::-1][1:]])
    return phi_full, lift_full


_PROFILES = {}


def profile(kind):
    if kind not in _PROFILES:
        v = P.VALVE_IN if kind == "in" else P.VALVE_EX
        _PROFILES[kind] = valve_profile(v["lift"], v["duration"])
    return _PROFILES[kind]


def valve_lift(theta_deg, kind):
    """Lift (mm) at crank angle theta (from gas-exchange TDC), cycle 720."""
    phi, lift = profile(kind)
    v = P.VALVE_IN if kind == "in" else P.VALVE_EX
    lca = P.LCA_IN if kind == "in" else P.LCA_EX
    d = ((np.asarray(theta_deg, float) - lca + 360.0) % 720.0) - 360.0      # crank deg from lobe centre
    cam_phi = phi[-1] / 2 + np.radians(d) / 2
    out = np.interp(cam_phi, phi, lift, left=0.0, right=0.0)
    return out


def cam_lobe_radius(kind, n=360):
    """Cam lobe radius (mm) vs angle from the nose, derived from the valve lift and the lever ratio."""
    phi, lift = profile(kind)
    ratio = P.derived()["lever_ratio"]
    ang = np.linspace(-phi[-1] / 2, phi[-1] / 2, n)
    r = P.CAM_BASE_R + np.interp(ang + phi[-1] / 2, phi, lift) / ratio
    return ang, r


# ------------------------------------------------------------------ valve train
def valve_mass_g(d, stem, length, rho, hollow=0.88):
    head = math.pi / 4 * d * d * 1.8
    h = 0.30 * d
    neck = math.pi * h / 12 * (d * d + d * stem + stem * stem)
    stm = math.pi / 4 * stem * stem * (length - h - 1.8)
    return (head + neck + stm * hollow) * rho


def _spring_stress(F, D, d):
    c = D / d
    kw = (4 * c - 1) / (4 * c - 4) + 0.615 / c
    return 8 * F * D * kw / (math.pi * d ** 3)


def dual_spring(f0, f_open, lift, clash=1.0, od_max=25.0, tau_allow=None):
    """Lightest outer+inner spring pair giving the required total rate and seat load."""
    tau_allow = tau_allow or P.TAU_ALLOW
    k = (f_open - f0) / lift
    best = None
    for share in (0.60, 0.65, 0.70):
        ko, ki = k * share, k * (1 - share)
        fo0, fi0 = f0 * share, f0 * (1 - share)
        for do in np.arange(2.4, 4.21, 0.1):
            for Do in np.arange(14.0, od_max - do + 0.01, 0.5):
                nao = G_SPR * do ** 4 / (8 * Do ** 3 * ko)
                if nao < 3.0:
                    continue
                fso = fo0 + ko * (lift + clash)
                if _spring_stress(fso, Do, do) > tau_allow:
                    continue
                mo = RHO_STEEL * (math.pi * do * do / 4) * (math.pi * Do) * (nao + 2)
                id_o = Do - do
                for di in np.arange(1.5, 3.01, 0.1):
                    for Di in np.arange(7.0, id_o - 1.5 - di + 0.01, 0.5):
                        nai = G_SPR * di ** 4 / (8 * Di ** 3 * ki)
                        if nai < 3.0:
                            continue
                        fsi = fi0 + ki * (lift + clash)
                        if _spring_stress(fsi, Di, di) > tau_allow:
                            continue
                        mi = RHO_STEEL * (math.pi * di * di / 4) * (math.pi * Di) * (nai + 2)
                        tot = mo + mi
                        if best is None or tot < best["mass"]:
                            best = dict(mass=tot, share=share, k=k, f0=f0, f_open=f_open,
                                        outer=dict(d=float(do), D=float(Do), na=float(nao), k=float(ko), mass=float(mo),
                                                   tau=_spring_stress(fso, Do, do), solid=float((nao + 2) * do)),
                                        inner=dict(d=float(di), D=float(Di), na=float(nai), k=float(ki), mass=float(mi),
                                                   tau=_spring_stress(fsi, Di, di), solid=float((nai + 2) * di)))
    return best


def static_rate(kind, rpm, m_eff_g, margin, f0):
    """Smallest spring rate (N/mm) keeping the follower on the cam: F_spring >= margin * m * (-a)."""
    phi, lift = profile(kind)
    w = 2 * math.pi * (rpm / 2) / 60.0
    y = lift * 1e-3
    yd = np.gradient(y, phi) * w
    ydd = np.gradient(yd, phi) * w
    need = margin * (m_eff_g * 1e-3) * np.maximum(-ydd, 0.0)
    mask = lift > 0.2
    kreq = np.max(np.where(mask, (need - f0) / np.maximum(lift, 1e-9), 0.0))
    return max(float(kreq), 10.0), float(ydd.max() / 9.81), float(ydd.min() / 9.81), float(np.max(need))


def design_valvetrain(kind, masses=None):
    """Spring design and effective mass for one valve type. masses: optional CAD masses in g."""
    v = P.VALVE_IN if kind == "in" else P.VALVE_EX
    rho = RHO_TI
    mv = (masses or {}).get("valve_" + kind) or valve_mass_g(v["d"], v["stem"], v["length"], rho)
    ret = (masses or {}).get("retainer", 2.2)
    kee = (masses or {}).get("keepers", 0.8)
    cap = (masses or {}).get("lash_cap", 0.7)
    fol = (masses or {}).get("follower_eff", 4.0)
    msp = 20.0
    res = None
    for _ in range(5):
        m_eff = mv + ret + kee + cap + fol + msp / 3.0
        k, a_pos, a_neg, f_need = static_rate(kind, P.RPM_CHECK, m_eff, P.SPRING_MARGIN, P.SPRING_PRELOAD)
        f_open = P.SPRING_PRELOAD + k * v["lift"]
        sp = dual_spring(P.SPRING_PRELOAD, f_open, v["lift"])
        if sp is None:
            return dict(kind=kind, fail=True, m_eff=m_eff, k=k, f_open=f_open)
        msp = sp["mass"]
        res = dict(kind=kind, m_valve=mv, m_eff=m_eff, k=k, f_open=f_open, spring=sp, a_pos_g=a_pos, a_neg_g=a_neg,
                   f_inertia_check=f_need / P.SPRING_MARGIN)
    # static margin at other speeds
    res["margin_at"] = {}
    for rpm in (13000, 14000, 15000, 16500):
        kk, _, _, fn = static_rate(kind, rpm, res["m_eff"], 1.0, P.SPRING_PRELOAD)
        res["margin_at"][rpm] = (P.SPRING_PRELOAD + res["k"] * 0) and (res["k"] / kk if kk > 0 else 99.0)
    # surge frequency (fixed-fixed): f = 0.5 sqrt(k/m)
    for key in ("outer", "inner"):
        s = res["spring"][key]
        s["surge_hz"] = 0.5 * math.sqrt(s["k"] * 1e3 / (s["mass"] * 1e-3))
    cam_hz = lambda rpm: rpm / 2 / 60.0
    res["surge_ratio_15k"] = res["spring"]["outer"]["surge_hz"] / cam_hz(15000)
    return res


def simulate_valve(kind, rpm, m_eff_g, f0, k_n_mm, kc=3.0e7, zeta=0.02, cycles=5):
    """Lumped valve-train model: cam -> stiff follower -> valve mass with spring and seat.
    Returns (min contact force N, number of float events > 30 microseconds, seat velocity m/s)."""
    phi, lift = profile(kind)
    w = 2 * math.pi * (rpm / 2) / 60.0
    tper = 2 * math.pi / w
    n = int(tper / 4e-6)
    dt = tper / n
    ph = (np.arange(n * cycles) * dt * w) % (2 * math.pi)
    y = np.interp(ph, phi, lift * 1e-3, right=0.0, left=0.0)
    y[ph > phi[-1]] = 0.0
    yd = np.gradient(y, dt)
    m = m_eff_g * 1e-3
    k = k_n_mm * 1e3
    c = 2 * zeta * math.sqrt(kc * m)
    ks = 5e7
    cs = 2 * 0.3 * math.sqrt(ks * m)
    x = v = 0.0
    last = n * (cycles - 1)
    min_p, run, events, seatv = 1e9, 0, 0, 0.0
    yl, yd_l = y.tolist(), yd.tolist()
    for i in range(len(yl)):
        p = kc * (yl[i] - x) + c * (yd_l[i] - v)
        if p < 0:
            p = 0.0
        fs = f0 + k * x
        nn = (-ks * x - cs * v) if x < 0 else 0.0
        a = (p - fs + nn) / m
        v += a * dt
        x += v * dt
        if i >= last:
            if yl[i] > 0.3e-3:
                min_p = min(min_p, p)
                if p == 0.0:
                    run += 1
                    if run == 8:           # 8 steps = 32 microseconds
                        events += 1
                else:
                    run = 0
            else:
                run = 0
            if x < 0 and v < seatv:
                seatv = v
    return (0.0 if min_p > 1e8 else min_p), events, seatv


def float_onset(kind, vt, rpm_lo=12000, rpm_hi=19000, step=500):
    for rpm in range(rpm_lo, rpm_hi + 1, step):
        pmin, ev, sv = simulate_valve(kind, rpm, vt["m_eff"], P.SPRING_PRELOAD, vt["k"])
        if ev > 0:
            return rpm
    return None


# ------------------------------------------------------------------ structure checks
def rod_checks(m_rec_g, m_rod_above_cap_g, rod_a_min, rod_i_y, rpm, p_peak_bar):
    """Buckling, tension at the neck and fatigue (Goodman) for a Q&T 42CrMo4 steel rod, shot-peened."""
    w = 2 * math.pi * rpm / 60.0
    f_t = (m_rec_g * 1e-3) * P.R * 1e-3 * w ** 2 * (1 + P.LAM)          # tension at gas-exchange TDC (piston group only)
    f_c = (p_peak_bar - 1.0) * 1e5 * AP * 1e-6                           # gas peak compression
    f_c = max(f_c - m_rec_g * 1e-3 * P.R * 1e-3 * w ** 2 * 0.3, f_c * 0.6)
    pcr = math.pi ** 2 * E_STEEL * rod_i_y / P.ROD ** 2
    sig_t, sig_c = f_t / rod_a_min, f_c / rod_a_min
    amp, mean = (sig_t + sig_c) / 2, (sig_c - sig_t) / 2
    uts, se = 1100.0, 330.0
    sf_fat = 1.0 / (amp / se + mean / uts) if (amp / se + mean / uts) > 0 else 99.0
    return dict(f_tension=f_t, f_comp=f_c, buckling_sf=pcr / f_c, sig_t=sig_t, sig_c=sig_c, fatigue_sf=sf_fat, pcr=pcr)


def bolt_check(m_above_cap_g, rpm, bolts=2, d=11.11, as_mm2=76.6, rp02=1400.0):
    w = 2 * math.pi * rpm / 60.0
    f = (m_above_cap_g * 1e-3) * P.R * 1e-3 * w ** 2 * (1 + P.LAM)
    per = f / bolts
    preload = 0.70 * rp02 * as_mm2
    return dict(load_per_bolt=per, preload=preload, sf=preload / per)


def stud_check(p_peak_bar, n=4, as_mm2=58.0, rp02=1100.0):
    f = (p_peak_bar - 1.0) * 1e5 * AP * 1e-6
    preload = 0.70 * rp02 * as_mm2 * n
    return dict(gas=f, preload=preload, sf=preload / f)


def pin_check(f_peak, pin_d=None, pin_bore=None):
    d, di = pin_d or P.PIN_D, pin_bore or P.PIN_BORE
    z = math.pi / 32 * (d ** 4 - di ** 4) / d
    span = 2 * ((P.BOSS_Y_IN + P.PIN_LEN / 2) / 2)
    m = f_peak / 2 * (span / 2 - P.ROD_SMALL_W / 4)
    sig = m / z
    return dict(sigma=sig, sf=1100.0 / sig)


def rod_section():
    """Area (mm2) and second moment about y (mm4, in-plane buckling) of the I-beam section from params."""
    x, y, tf, tw = P.ROD_BEAM_X, P.ROD_BEAM_Y, P.ROD_FLANGE_T, P.ROD_WEB_T
    a = 2 * y * tf + (x - 2 * tf) * tw
    i = 2 * (y * tf ** 3 / 12 + y * tf * ((x - tf) / 2) ** 2) + tw * (x - 2 * tf) ** 3 / 12
    return a, i


def bearing_pressure(pin_peak_n, d=None, w=None):
    d = d or P.PIN_JOURNAL_D
    w = w or P.PIN_W
    return pin_peak_n / (d * w)


# ------------------------------------------------------------------ chain
def chain_hull(n_per_circle=90):
    """Convex hull (x, z) of the three pitch circles: the chain path, and its perimeter (mm)."""
    zc = P.derived()["z_cam"]
    circles = [(0.0, 0.0, P.CHAIN_PITCH / (2 * math.sin(math.pi / P.SPROCKET_Z_CRANK))),
               (P.CAM_X, zc, P.CHAIN_PITCH / (2 * math.sin(math.pi / P.SPROCKET_Z_CAM))),
               (-P.CAM_X, zc, P.CHAIN_PITCH / (2 * math.sin(math.pi / P.SPROCKET_Z_CAM)))]
    pts = []
    for cx, cz, r in circles:
        for i in range(n_per_circle):
            a = 2 * math.pi * i / n_per_circle
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    pts = sorted(set(pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    per = sum(math.dist(hull[i], hull[(i + 1) % len(hull)]) for i in range(len(hull)))
    return hull, per


def chain_geometry():
    hull, per = chain_hull()
    links = int(round(per / P.CHAIN_PITCH / 2.0)) * 2
    return dict(r_crank=P.CHAIN_PITCH / (2 * math.sin(math.pi / P.SPROCKET_Z_CRANK)),
                r_cam=P.CHAIN_PITCH / (2 * math.sin(math.pi / P.SPROCKET_Z_CAM)), z_cam=P.derived()["z_cam"],
                length=per, links=links, speed_ms=rpm_chain_speed(P.RPM_REDLINE))


def rpm_chain_speed(rpm):
    return rpm * P.CHAIN_PITCH * 1e-3 * P.SPROCKET_Z_CRANK / 60.0


# ------------------------------------------------------------------ fluids
def pump_and_cooling(power_kw):
    q_cool_kw = 0.95 * power_kw                       # heat to coolant, rule of thumb 0.8-1.0 x brake power
    flow_l_min = q_cool_kw / (4.0 * 8.0) * 60.0       # dT = 8 K, cp 4 kJ/kg K -> kg/s -> L/min
    d_imp = 0.036
    n = P.RPM_REDLINE / 60.0
    q_imp = 0.15 * n * d_imp ** 3 * 1000 * 60         # L/min, flow coefficient 0.15
    gerotor_cc = 3.6
    q_oil = gerotor_cc * P.RPM_REDLINE / 1000.0       # L/min at redline (relief valve bypasses the excess)
    return dict(q_cool_kw=q_cool_kw, flow_needed_lpm=flow_l_min, impeller_lpm=q_imp, impeller_d_mm=36.0,
                oil_cc_rev=gerotor_cc, oil_lpm_redline=q_oil, relief_bar=4.5)


# ------------------------------------------------------------------ top-level run
def run(cad=None):
    """cad: optional dict of CAD-derived numbers (kg unless named)."""
    cad = cad or {}
    out = {"checks": []}

    def chk(name, value, limit, ok, unit="", note=""):
        out["checks"].append(dict(name=name, value=value, limit=limit, ok=bool(ok), unit=unit, note=note))

    vc = cad.get("vc_mm3") or P.VD_CC * 1000.0 / (P.CR_TARGET - 1.0)
    out["vc_cc"] = vc / 1000.0
    out["cr"] = (P.VD_CC * 1000.0 + vc) / vc
    out["piston_speed_15k"] = mean_piston_speed(15000)
    out["piston_speed_16k5"] = mean_piston_speed(16500)

    m_pist = cad.get("piston_group_kg", 0.300)
    m_rod = cad.get("rod_kg", 0.260)
    m_cap = cad.get("cap_kg", 0.075)
    rod_small_frac = cad.get("rod_small_frac", 0.30)
    m_rec = m_pist + rod_small_frac * m_rod
    m_rot = (1 - rod_small_frac) * m_rod + cad.get("rod_shells_kg", 0.025)
    out["masses"] = dict(m_rec=m_rec, m_rot=m_rot, piston_group=m_pist, rod=m_rod)

    # gas pressure at two operating points
    th, p10, imep10 = cylinder_pressure(10500, p_ivc_model(10500), vc)
    th, p14, imep14 = cylinder_pressure(14000, p_ivc_model(14000), vc)
    out["p_peak_bar"] = dict(r10500=float(p10.max()), r14000=float(p14.max()))
    out["pressure_curve_10500"] = [float(x) for x in p10[::4]]
    out["pressure_curve_14000"] = [float(x) for x in p14[::4]]
    p_peak = max(out["p_peak_bar"].values())

    # rod and bearing loads
    rl = {}
    for rpm in (10500, 15000, 16500):
        p = cylinder_pressure(min(rpm, 14000), p_ivc_model(min(rpm, 14000)), vc)[1]
        rl[rpm] = rod_loads(rpm, m_rec, m_rot, p, th)
    pin_peak = max(float(r["pin"].max()) for r in rl.values())
    out["loads"] = dict(rod_tension_16k5=float(-rl[16500]["f_rod"].min()), rod_comp_peak=float(max(r["f_rod"].max() for r in rl.values())),
                        pin_peak=pin_peak)
    pb = bearing_pressure(pin_peak)
    chk("Rod journal peak pressure", pb, 140.0, pb <= 140.0, "MPa", "36 x 19 mm Cu-Pb tri-metal shell, peak limit about 140 MPa")
    mean_p = float(np.mean(rl[14000 if 14000 in rl else 15000]["pin"] if False else rl[15000]["pin"]))
    out["pin_mean_15k"] = mean_p

    # balance
    cw_t, bal_t = balance_targets(m_rec, m_rot)
    crank_m = cad.get("crank_moment_kgmm", cw_t)
    bal_m = cad.get("bal_moment_kgmm", bal_t)
    b15 = balance(15000, m_rec, m_rot, crank_m, bal_m)
    out["balance"] = dict(targets=dict(cw=cw_t, bal=bal_t), crank_moment=crank_m, bal_moment=bal_m, **{k: v for k, v in b15.items()})
    chk("Shaking force with balance shaft", b15["peak_with"], 0.35 * b15["peak_none"], b15["peak_with"] <= 0.35 * b15["peak_none"], "N",
        "unbalanced %.0f N, counterweights only %.0f N" % (b15["peak_none"], b15["peak_cw_only"]))

    # rod
    rod_a, rod_i = rod_section()
    rod_a = cad.get("rod_a_min", rod_a)
    rod_i = cad.get("rod_i_y", rod_i)
    rc = rod_checks(m_pist * 1000, m_rod * 1000, rod_a, rod_i, P.RPM_CHECK, p_peak)
    out["rod"] = rc
    chk("Rod buckling safety factor", rc["buckling_sf"], 2.0, rc["buckling_sf"] >= 2.0, "", "Euler, pinned ends, peak gas load")
    chk("Rod fatigue safety factor (Goodman)", rc["fatigue_sf"], 1.5, rc["fatigue_sf"] >= 1.5, "", "42CrMo4 Q&T, shot-peened, 16,500 rpm")
    bc = bolt_check((m_pist + (m_rod - m_cap)) * 1000, P.RPM_CHECK)
    out["rod_bolt"] = bc
    chk("Rod bolt preload safety factor", bc["sf"], 2.0, bc["sf"] >= 2.0, "", "7/16-20 premium bolts at 70% of yield, 16,500 rpm")
    sc = stud_check(p_peak)
    out["studs"] = sc
    chk("Head stud preload vs gas load", sc["sf"], 2.0, sc["sf"] >= 2.0, "", "4 x M10 12.9")
    pc = pin_check(sc["gas"])
    out["pin"] = pc
    chk("Piston pin bending safety factor", pc["sf"], 1.6, pc["sf"] >= 1.6, "", "22 x 12 mm case-hardened pin")

    # valvetrain
    vt = {}
    for kind in ("in", "ex"):
        r = design_valvetrain(kind, cad.get("valve_masses"))
        vt[kind] = r
        if r.get("fail"):
            chk("Valve spring %s feasible" % kind, 0, 1, False, "", "no spring within stress limit")
            continue
        r["float_onset_rpm"] = float_onset(kind, r)
        pmin, ev, sv = simulate_valve(kind, 15000, r["m_eff"], P.SPRING_PRELOAD, r["k"])
        r["seat_velocity_15k"] = sv
        f_inertia_16k5 = r["f_inertia_check"]
        chk("Valve spring %s force / inertia at %d rpm" % ("intake" if kind == "in" else "exhaust", P.RPM_CHECK),
            r["f_open"] / max(f_inertia_16k5, 1.0), P.SPRING_MARGIN, r["f_open"] / max(f_inertia_16k5, 1.0) >= P.SPRING_MARGIN, "",
            "m_eff %.1f g, spring %.0f N at full lift" % (r["m_eff"], r["f_open"]))
        fo = r["float_onset_rpm"]
        chk("Valve float onset, %s (lumped dynamic model)" % ("intake" if kind == "in" else "exhaust"), fo or 19000, P.RPM_REDLINE,
            (fo is None) or fo >= P.RPM_REDLINE, "rpm", "first rpm with loss of cam contact; indicative only")
    out["valvetrain"] = vt
    out["flow"] = dict(z_15k=flow_index(15000), z_13k5=flow_index(13500), valve_area_pct=2 * math.pi / 4 * P.VALVE_IN["d"] ** 2 / AP * 100)
    out["chain"] = chain_geometry()
    chk("Chain speed at redline", out["chain"]["speed_ms"], 30.0, out["chain"]["speed_ms"] <= 30.0, "m/s", "04C chain, 14 teeth on the crank")

    # power
    pc_rows = power_curve(vc)
    out["power"] = pc_rows
    best = max(pc_rows, key=lambda r: r["kw"])
    out["power_peak"] = best
    out["torque_peak"] = max(pc_rows, key=lambda r: r["nm"])
    out["cooling"] = pump_and_cooling(best["kw"])
    chk("Piston speed at redline", out["piston_speed_15k"], 27.0, out["piston_speed_15k"] <= 27.0, "m/s", "racing class above about 22")
    return out


if __name__ == "__main__":
    r = run()
    for c in r["checks"]:
        print("%-52s %10.2f  limit %8.2f  %s  %s" % (c["name"], c["value"], c["limit"], "PASS" if c["ok"] else "FAIL", c["note"]))
    pk = r["power_peak"]
    print("power peak %.1f kW (%.0f hp) at %d rpm; torque peak %.1f Nm at %d rpm" % (pk["kw"], pk["hp"], pk["rpm"], r["torque_peak"]["nm"], r["torque_peak"]["rpm"]))
    for row in r["power"]:
        print("%6d rpm  imep %5.1f bmep %5.1f  %5.1f kW  %5.1f Nm  peak %5.1f bar  p_ivc %.2f  Z %.2f" % (row["rpm"], row["imep"], row["bmep"], row["kw"], row["nm"], row["peak_bar"], row["p_ivc"], row["z"]))
    for k in ("in", "ex"):
        v = r["valvetrain"][k]
        if v.get("fail"): print(k, "FAIL"); continue
        print(k, "m_eff %.1f g k %.0f N/mm f_open %.0f N  spring mass %.1f g  surge %.0f Hz (%.1f x cam)  float %s  seat v %.2f" % (v["m_eff"], v["k"], v["f_open"], v["spring"]["mass"], v["spring"]["outer"]["surge_hz"], v["surge_ratio_15k"], v["float_onset_rpm"], v["seat_velocity_15k"]))
        print("   outer", {a: round(b, 2) for a, b in v["spring"]["outer"].items()})
        print("   inner", {a: round(b, 2) for a, b in v["spring"]["inner"].items()})
    print("balance", {k: (round(v, 1) if isinstance(v, float) else v) for k, v in r["balance"].items() if not isinstance(v, dict)})
    print("chain", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r["chain"].items() if k != "tangents"})
    print("cooling", {k: round(v, 1) for k, v in r["cooling"].items()})
    print("loads", {k: round(v) for k, v in r["loads"].items()})
