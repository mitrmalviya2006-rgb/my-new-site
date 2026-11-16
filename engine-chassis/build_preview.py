#!/usr/bin/env python3
"""Inject preview_data.json (written by frame.py) and the engine's outer-shell meshes into preview.template.html -> preview.html"""
import json
import os

d = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(d, "preview_data.json")))

# outer-shell parts of the engine, in the engine frame (the viewer moves them to data["engine"]["origin"])
SHELL = ["upper_case", "bedplate", "oil_pan", "barrel", "head", "cam_cover", "cover_chain", "cover_gear",
         "pump_cover", "oil_filter", "throttle_body", "spark_coil", "output_flange"]
mesh_path = os.path.join(d, "..", "engine-design", "mesh.json")
if os.path.exists(mesh_path):
    meshes = json.load(open(mesh_path))["meshes"]
    data["engine_meshes"] = [{k: m[k] for k in ("part", "name", "lo", "span", "v", "i", "it")} for m in meshes if m["part"] in SHELL]
else:
    data["engine_meshes"] = []

tpl = open(os.path.join(d, "preview.template.html")).read()
open(os.path.join(d, "preview.html"), "w").write(tpl.replace("__DATA__", json.dumps(data, separators=(",", ":"))))
print("preview.html written, %.2f MB, %d engine meshes" % (os.path.getsize(os.path.join(d, "preview.html")) / 1e6, len(data["engine_meshes"])))
