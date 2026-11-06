"""Actual XML -> actual Python dispatcher -> actual helper; Kodi RPC boundary only."""
import ast,importlib.util,json,re,sys,types
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[3];CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter';SKIN=ROOT/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz'
s=importlib.util.spec_from_file_location('library_navigation',CC/'library_navigation.py');helper=importlib.util.module_from_spec(s);s.loader.exec_module(helper);sys.modules['library_navigation']=helper
fn=next(n for n in ast.parse((CC/'default.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='direct_command');calls=[];env={'xbmc':types.SimpleNamespace(executeJSONRPC=lambda raw:(calls.append(json.loads(raw)) or '{"result":"OK"}')),'xbmcgui':types.SimpleNamespace(Dialog=lambda:None)};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_default_dispatch','exec'),env)
root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot();cases=[]
for cid,action,route in [('1198104','library-movies','movies'),('1198111','library-tv','tv')]:
 control=root.find('.//control[@id="'+cid+'"]');script=next(n.text for n in control.findall('onclick') if (n.text or '').startswith('RunScript(script.infinity.commandcenter,library-navigation,'));m=re.fullmatch(r'RunScript\(script.infinity.commandcenter,(library-navigation),(library-(?:movies|tv))\)',script);assert m and m[2]==action
 assert env['direct_command'](['actual_default.py',*m.groups()]);assert calls[-1]=={'jsonrpc':'2.0','id':1,'method':'GUI.ActivateWindow','params':{'window':'videos','parameters':['plugin://script.infinity.commandcenter/?action='+route,'return','infinity-library-direct']}};cases.append(cid)
report={'status':'PASS_ACTUAL_DRAWER_DISPATCH_CHAIN','controls':cases,'segments':'real XML -> real direct_command AST -> imported real helper -> checked native RPC message','not_executed':'native window, bootstrap/JNI, actual plugin directory/Android','Android':'NOT_RUN'};Path(__file__).with_name('DRAWER-DISPATCH-RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
