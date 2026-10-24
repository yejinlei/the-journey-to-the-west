# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
exec(open('_make_xkb_batch4.py', encoding='utf-8').read().replace("json.dump", "_noop_json_dump"))

def _noop_json_dump(*a, **k): pass
