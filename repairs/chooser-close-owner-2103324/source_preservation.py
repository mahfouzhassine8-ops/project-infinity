"""Keep every Splash Java token outside startXBMC identical to locked 2103323."""
import json
import re
from pathlib import Path

TOKENS=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\w+|[^\s]',re.M)

def tokens(text):
    return [m[0] for m in TOKENS.finditer(text) if not m[0].startswith(('//','/*'))]

def without_start(text):
    matches=list(re.finditer(r'protected void startXBMC\(\)\s*\{',text))
    assert len(matches)==1
    start=text.index('{',matches[0].start());depth=0
    for t in TOKENS.finditer(text,start):
        if t[0]=='{':depth+=1
        elif t[0]=='}':
            depth-=1
            if depth==0:return text[:matches[0].start()]+'SHUTDOWN_DISPATCH'+text[t.end():]
    raise AssertionError('Unclosed method')

def verify(before,after,out):
    assert tokens(without_start(before))==tokens(without_start(after)), 'Splash change outside startXBMC'
    Path(out).write_text(json.dumps({'protected_Splash_java_tokens_identical':True,
        'Splash_changed_methods':['startXBMC'],
        'shutdown_monitor_change':'Require instance lease instead of PID presence; preserve historical receipts and phase semantics',
        'all_Cobra_sources_identical':True,'normal_close_and_native_cleanup_sources_identical':True},indent=2)+'\n')

