"""Exact signed445 Main preimages. No teardown, shutdown, native or skin edits."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods
MAIN='Lcom/projectinfinity/kodi/Main;'
POLICY='Lcom/projectinfinity/kodi/InfinityExternalVideoIntents;'

def patch_main(raw):
 before=methods(raw)
 sig='public onCreate(Landroid/os/Bundle;)V';old=before[sig]
 # Only the existing cold URI copy changes; original 5000ms, queue and URI clearing remain.
 begin=old.index('    new-instance v3, Landroid/content/Intent;\n',old.index('    .line 252'))
 end=old.index('    const/16 v4, 0x1388',begin)
 fragment=old[begin:end]
 assert 'invoke-virtual {p0}, '+MAIN+'->getIntent()Landroid/content/Intent;' in fragment
 # Unsupported routes still require the baseline cold copy, even when policy is a no-op.
 # accept returns original on unsupported routes; take a copy first exactly as baseline.
 new='''    new-instance v3, Landroid/content/Intent;
    invoke-virtual {p0}, '''+MAIN+'''->getIntent()Landroid/content/Intent;
    move-result-object v4
    invoke-direct {v3, v4}, Landroid/content/Intent;-><init>(Landroid/content/Intent;)V
    invoke-static {p0, v3}, '''+POLICY+'''->accept('''+MAIN+'''Landroid/content/Intent;)Landroid/content/Intent;
    move-result-object v3

'''
 raw=raw.replace(old,old[:begin]+new+old[end:])
 sig='protected onNewIntent(Landroid/content/Intent;)V';old=before[sig]
 needle='    .line 349\n    :cond_2\n'
 assert old.count(needle)==1
 new=old.replace(needle,needle+'    invoke-static {p0, p1}, '+POLICY+'->accept('+MAIN+'Landroid/content/Intent;)Landroid/content/Intent;\n    move-result-object p1\n\n')
 native='invoke-virtual {p0, p1}, '+MAIN+'->_onNewIntent(Landroid/content/Intent;)V'
 assert new.count(native)==1
 new=new.replace(native,'invoke-static {p0, p1}, '+POLICY+'->dispatch('+MAIN+'Landroid/content/Intent;)V')
 return raw.replace(old,new)

def patch_delayed(raw):
 old='invoke-virtual {v0, v1}, '+MAIN+'->_onNewIntent(Landroid/content/Intent;)V'
 assert raw.count(old)==1
 return raw.replace(old,'invoke-static {v0, v1}, '+POLICY+'->dispatch('+MAIN+'Landroid/content/Intent;)V')
