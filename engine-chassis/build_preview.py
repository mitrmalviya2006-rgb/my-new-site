#!/usr/bin/env python3
"""Inject preview_data.json (written by frame.py) into preview.template.html -> preview.html"""
import json, os
d = os.path.dirname(os.path.abspath(__file__))
data = open(os.path.join(d, "preview_data.json")).read()
tpl = open(os.path.join(d, "preview.template.html")).read()
open(os.path.join(d, "preview.html"), "w").write(tpl.replace("__DATA__", data))
print("preview.html written")
