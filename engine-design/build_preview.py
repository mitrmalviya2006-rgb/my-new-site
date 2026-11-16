#!/usr/bin/env python3
"""Inject mesh.json and the key results into preview.template.html -> preview.html"""
import json
import os

d = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(d, "results.json")))
mesh = json.load(open(os.path.join(d, "mesh.json")))
import params as P

pk = res["power_peak"]
red = [r for r in res["power"] if r["rpm"] == 15000][0]
tq = res["torque_peak"]
env = res["envelope"]
vt = res["valvetrain"]
stats = dict(cc=P.VD_CC, bore=P.BORE, stroke=P.STROKE, cr=res["ctx"]["cr"], redline=P.RPM_REDLINE, vp=res["piston_speed_15k"],
             vin=P.VALVE_IN["d"], vex=P.VALVE_EX["d"], float_in=vt["in"]["float_onset_rpm"], float_ex=vt["ex"]["float_onset_rpm"],
             hp_peak=pk["hp"], hp_rpm=pk["rpm"], hp_red=red["hp"], nm=tq["nm"], nm_rpm=tq["rpm"], mass=res["mass"]["dry_kg"],
             unique=res["counts"]["unique"], make=res["counts"]["make"],
             size="%d x %d x %d mm" % (env["x"][1] - env["x"][0], env["y"][1] - env["y"][0], env["z"][1] - env["z"][0]))


def fmtv(c):
    v = c["value"]
    u = c["unit"]
    if isinstance(v, (int, float)):
        s = ("%d" % v) if abs(v) >= 1000 or float(v).is_integer() else ("%.2f" % v)
        if abs(v) >= 1000:
            s = "{:,}".format(int(round(v)))
    else:
        s = str(v)
    return (s + " " + u).strip()


def fmtl(c):
    v = c["limit"]
    try:
        s = "{:,}".format(int(round(float(v)))) if abs(float(v)) >= 100 else ("%g" % round(float(v), 2))
    except Exception:
        s = str(v)
    return s


checks = [dict(name=c["name"], value=fmtv(c), limit=fmtl(c), ok=c["ok"]) for c in res["checks"]]
data = dict(meshes=mesh["meshes"], stats=stats, steps={str(k): v for k, v in res["steps"].items()}, checks=checks,
            bom=[dict(id=b["id"], name=b["name"], group=b["group"], source=b["source"], material=b["material"], qty=b["qty"], mass_each_g=b["mass_each_g"]) for b in res["bom"]])
tpl = open(os.path.join(d, "preview.template.html")).read()
open(os.path.join(d, "preview.html"), "w").write(tpl.replace("__DATA__", json.dumps(data, separators=(",", ":"))))
print("preview.html written, %.1f MB" % (os.path.getsize(os.path.join(d, "preview.html")) / 1e6))
