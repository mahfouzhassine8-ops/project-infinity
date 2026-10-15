#!/usr/bin/env python3
"""Summarize actual before/after mappings. This is evidence, not a formula oracle."""
from pathlib import Path
import argparse,csv,json
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();r=a.evidence
before=json.loads((r/'baseline-screenshots/display-observed-geometry.json').read_text());after=json.loads((r/'screenshots/display-observed-geometry.json').read_text())
key=lambda x:(x['mode'],tuple(x['source']),tuple(x['viewport']))
b={key(x):x for x in before};assert len(b)==len(before)==len(after)==240
names={12:'Fold Fit',13:'Fold Fill',-1:'Inherit Default',0:'Best Fit',1:'Crop / Fill',2:'16:9',3:'4:3',4:'Wide 1.10x',5:'Wide 1.25x',6:'Wide 1.40x',7:'Short + Wide',8:'Zoom 1.25x',9:'Zoom 1.50x',10:'Zoom 2.00x',11:'Custom Width / Height'}
fields=['mode','label','source','viewport','before_bounds','after_bounds','before_utilization','after_utilization','before_proportional_crop','after_proportional_crop','physical_acceptance']
with (r/'Display-observed-before-after.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
 for x in after:
  old=b[key(x)];writer.writerow(dict(mode=x['mode'],label=names[x['mode']],source='x'.join(map(str,x['source'])),viewport='x'.join(map(str,x['viewport'])),before_bounds=json.dumps(old['bounds']),after_bounds=json.dumps(x['bounds']),before_utilization=old['utilization'],after_utilization=x['utilization'],before_proportional_crop=old['proportional_source_crop'],after_proportional_crop=x['proportional_source_crop'],physical_acceptance='UNVERIFIED'))
lines=['# Recorded Display geometry — exact baseline vs candidate','', 'Measurements are from the real production TextureView inside verified native Android window bounds. Source metadata is controlled; decoded video remains unverified. These observations do not independently establish product acceptance.', '', '| Mode | 1920x1080 source / 800x600 pane: baseline picture | Candidate picture | Utilization before → after | Proportional crop before → after | Physical |','| --- | --- | --- | --- | --- | --- |']
for mode in names:
 x=next(x for x in after if key(x)==(mode,(1920,1080),(800,600)));old=b[key(x)]
 fmt=lambda x: ', '.join(f'{v:.1f}' for v in x['bounds'])
 lines.append(f"| {names[mode]} | [{fmt(old)}] | [{fmt(x)}] | {old['utilization']:.1%} → {x['utilization']:.1%} | {old['proportional_source_crop']:.1%} → {x['proportional_source_crop']:.1%} | UNVERIFIED |")
lines+=['','Bounds are left, top, right, bottom in pane pixels. Negative/outside bounds are clipped by the pane. Utilization is picture intersection area / pane area. Crop is geometric intersection / transformed picture; this cannot detect bars encoded in the source or establish the actual decoder crop.', '', 'Full 240-pair record: Display-observed-before-after.csv. Fixed aspects/Wide/Short/Custom intentionally reshape the picture, so proportional crop alone does not describe distortion. Inherit uses the fixture default; separate transition tests change the actual global control. Custom starts at saved 100% values; reset/isolation are separate tests.']
(r/'DISPLAY-GEOMETRY.md').write_text('\n'.join(lines)+'\n')
print('Recorded 240 actual paired observations; no decoded-video/device pass inferred')
