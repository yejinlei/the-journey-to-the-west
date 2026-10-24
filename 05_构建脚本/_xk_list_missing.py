# -*- coding: utf-8 -*-
import json
from pathlib import Path
data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
missing = [l for l in data['lines']
           if l.get('edition') == 'xinke_pingbi' and not l.get('text_zh')]
print(f'缺 {len(missing)} 行:')
for l in missing:
    print(f'({l["page_no"]}, {l["line_idx"]}, {l["form_type"]}): {l["text"][:80]}')
