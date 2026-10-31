"""Classify every inventoried signed action; coverage is not runtime acceptance."""
import argparse
import hashlib
from collections import Counter
import json
from pathlib import Path
import re

OWNED = frozenset(('search-provider','search-all','movies','movie-navigator','tv','tv-navigator',
                   'custom-lists','library','continue','resume','commands'))

def classify(record):
    action=record['action'];lower=action.lower()
    if any(x in lower for x in ('shutdown','checkpoint','powerdown','quit','reboot','restartapp')):
        return 'PROTECTED_UNCHANGED', 'No new observation or behavioral test'
    if 'plugin://script.infinity.commandcenter' in action:
        route=re.search(r'(?:[?&]|&amp;)action=([a-z-]+)',action)
        if route and route.group(1) in OWNED:
            return 'FIRST_PARTY_PREPARATION', 'Existing plugin context: return/exception; endOfDirectory publication is not proof of painted viewport'
    if 'script.infinity.commandcenter' in action and ('search' in lower):
        return 'SEARCH_PREPARATION_OR_NATIVE_MODAL', 'Inventory preparation has explicit start/end; original provider-selection and native modal contracts retained'
    if record['event']=='content':
        return 'NATIVE_OR_ADDON_DIRECTORY', 'Kodi busy lifetime only where exposed; no inferred readiness from item count or timeout'
    if record['event'] in ('onback','onunload'):
        return 'NATIVE_NAVIGATION_CLEANUP', 'Original action unchanged; foreground ownership invalidated on context change'
    if action.startswith(('ActivateWindow(','RunScript(','RunAddon(','RunPlugin(','PlayMedia(')):
        return 'DISPATCH_WITH_NATIVE_FALLBACK', 'Original dispatch once; builtin return is not content readiness; real busy retained only while observed'
    return 'ORIGINAL_UI_OR_DYNAMIC_ACTION', 'No unsupported completion signal invented; preserve original UI action and required native dialogs'

def main(inventory,plan,out):
    source=json.loads(inventory.read_text());staged=json.loads(plan.read_text())
    # Inventory schema is checked explicitly rather than silently dropping rows.
    windows=source['xml'];counts=Counter();rows=[];contracts={}
    for window in windows:
        entries=[]
        for index,record in enumerate(window['actions']):
            category,contract=classify(record);counts[category]+=1;contracts[category]=contract
            entries.append(dict(inventory_action_index=index,coverage=category))
        rows.append(dict(member=window['member'],actions=entries,
                         staged_frame_controls=staged['registered_windows'].get(window['member'],[]),
                         limitation='Static include reachability is not proof a frame is currently visible'))
    result=dict(inventory_sha256=hashlib.sha256(inventory.read_bytes()).hexdigest(),baseline=staged['baseline_component'],categories=dict(counts),contracts=contracts,windows=rows,
                classification_count=sum(counts.values()),runtime='Only isolated Linux fixture tested; no universal Android acceptance')
    out.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    main(**vars(p.parse_args()))
