"""Compare every decoded class; allow only eight reviewed method removals.

Source line numbers are debug metadata and shift after deleting definitions.
All executable instructions, registers, literals, call targets and catches remain
checked, using the existing narrow D8 helper/encoding normalization.
"""
import difflib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RULES = json.loads((HERE / 'removals.json').read_text())

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def compare(base, candidate, classpath, out):
    old_guard = load('preserved_dex_normalization', ROOT/'repairs/cobra-clean-restart/bytecode_guard.py')
    bridge = load('preserved_helper_resolution', ROOT/'repairs/chooser-close-owner-2103324/bridge_preservation.py')
    old_guard.selftest()
    maps = []; helper_proofs = []
    activity = 'com/projectinfinity/kodi/InfinityLiveActivity.smali'
    buildconfig = 'com/projectinfinity/kodi/BuildConfig.smali'
    removed = {row['name'] for row in RULES['methods']}
    retired = ['showCobraSportsHub', 'cobraSportsPrepareHeader', 'cobraSportsRenderCurrent',
               'cobraSportsRenderHub', 'cobraSportsAddSection', 'cobraSportsAddSoccerSection',
               'showCobraSportsSoccer', 'cobraSportsAddLeagueSection', 'cobraSportsGameCard',
               'cobraSportsTeamMark', 'showCobraSportsGame', 'cobraSportsAddTeamRow',
               'showCobraSportsLeague', 'COBRA • SPORTS', 'cobra_sports_drawer_header',
               'cobra_sports_soccer_section', 'cobra_sports_soccer_leagues',
               'cobra_sports_soccer_rail', 'cobra-sports-game:', 'cobra-sports-league-game:']
    method = re.compile(r'^\.method [^\n]*? ([^\s(]+)\([^\n]*\n.*?^\.end method\n?', re.M|re.S)
    with tempfile.TemporaryDirectory(prefix='infinity-cleanup-dex-') as directory:
        for label, apk in [('parent', base), ('candidate', candidate)]:
            root = Path(directory)/label; root.mkdir()
            with zipfile.ZipFile(apk) as z:
                for name in z.namelist():
                    if re.fullmatch(r'classes\d*\.dex', name):
                        dex = root/name; dex.write_bytes(z.read(name))
                        subprocess.run(['java','-cp',classpath,'org.jf.baksmali.Main','disassemble',
                                        '--sequential-labels',str(dex),'-o',str(root/'smali')], check=True)
            raw = {p.relative_to(root/'smali').as_posix():p.read_text() for p in (root/'smali').rglob('*.smali')}
            if activity not in raw:
                raise RuntimeError('Expected activity missing')
            if buildconfig in raw:
                raise RuntimeError('Unexpected BuildConfig: exact locked APK has no such class')
            found = {m[1] for m in method.finditer(raw[activity]) if m[1] in removed}
            if found != (removed if label == 'parent' else set()):
                raise RuntimeError('Compiled removal inventory mismatch: '+repr(found))
            if label == 'parent':
                raw[activity] = method.sub(lambda m: '' if m[1] in removed else m[0], raw[activity])
            else:
                matches = [(name,token) for name,text in raw.items() for token in retired
                           if re.search(r'(?<![A-Za-z0-9_])'+re.escape(token)+r'(?![A-Za-z0-9_])', text)]
                if matches: raise RuntimeError('Retired dashboard token returned: '+repr(matches))
            normalized = {n:old_guard.normalize(re.sub(r'(?m)^\s*\.line \d+\s*$', '', t))+'\n' for n,t in raw.items()}
            resolved, bodies, helpers = bridge.resolve(normalized)
            maps.append(resolved)
            helper_proofs.append({'side':label,'classes':len(raw),'helper_bodies':sorted(bodies),'helper_containers':sorted(helpers)})
        old, new = maps
        changed = [n for n in sorted(old.keys()|new.keys()) if old.get(n) != new.get(n)]
        diagnostics = out/'compiler-differences'; diagnostics.mkdir(exist_ok=True)
        for n in changed:
            (diagnostics/(n.replace('/','_')+'.diff')).write_text(''.join(difflib.unified_diff(
                old.get(n,'').splitlines(True),new.get(n,'').splitlines(True),'parent/'+n,'candidate/'+n)))
        report = {'protected_classes_checked':len(old.keys()|new.keys()),'unexpected_differences':changed,
                  'removed_methods':sorted(removed),'retired_dashboard_absent':True,
                  'buildconfig_absent_in_both':True,
                  'source_debug_line_numbers_ignored':True,'helper_proofs':helper_proofs,
                  'decoded_protected_instructions_identical':not changed}
        (out/'DEX-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
        if changed: raise RuntimeError('Unapproved compiled difference: '+repr(changed))
        return report
