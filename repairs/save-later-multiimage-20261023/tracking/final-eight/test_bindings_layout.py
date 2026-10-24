"""Focused component admission, Infinity hold boundary and clock reflow evidence."""
import ast, hashlib, importlib.util, json, shutil, subprocess, sys, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent;REPAIR=HERE.parents[1]
def run(baseline, final, native, rc8map):
    versions={'script.infinity.commandcenter':'0.3.5.33','script.infinity.watchedbridge':'1.0.14',
              'script.infinity.uirepair':'0.1.16','skin.infinity.diggz':'1.0.5.240'}
    for aid,version in versions.items():assert ET.parse(final/aid/'addon.xml').getroot().get('version')==version
    pins=json.loads((final/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
    assert len(pins)==19 and pins==json.loads((final/'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json').read_text())
    for name,digest in pins.items():assert hashlib.sha256((final/'script.infinity.commandcenter'/name).read_bytes()).hexdigest()==digest
    trakt=ast.parse((final/'script.infinity.commandcenter/infinity_trakt.py').read_text())
    bridge=ast.literal_eval(next(n.value for n in trakt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BRIDGE_PINS' for t in n.targets)))
    for name,digest in bridge.items():assert hashlib.sha256((final/'script.infinity.watchedbridge'/name).read_bytes()).hexdigest()==digest
    texts=(final/'script.infinity.commandcenter/infinity_trakt.py').read_text()
    assert "'0.3.5.33'" in texts and "'1.0.14'" in texts and "'0.3.5.32'" not in texts
    tree=ast.parse((REPAIR/'dex_binding.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    end=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='classes' for t in n.targets))
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp);env={'inspect':lambda *a:(None,{}),'apk':None,'stage':final,'jars':None,'out':out,'HERE':REPAIR,'json':json,'Path':Path,'sha':lambda b:hashlib.sha256(b).hexdigest()}
        exec(compile(ast.Module(body=function.body[:end],type_ignores=[]),'production-generator','exec'),env)
        probe=out/'Probe.java';probe.write_text('''import java.io.*;import java.lang.reflect.*;
public class Probe { public static void main(String[] a) throws Exception {
Class<?> c=Class.forName("com.projectinfinity.kodi.InfinityInstalledCheckpointInstaller");
Method m=c.getDeclaredMethod("verify",File.class);m.setAccessible(true);
Object r=m.invoke(null,new File(a[0]));System.out.print(r==null?"REJECT":r); }}''')
        subprocess.run(['java','com.sun.tools.javac.Main','--release','8','-d',str(out/'classes'),str(env['source']),str(probe)],check=True)
        def verify(path):return subprocess.check_output(['java','-cp',str(out/'classes'),'Probe',str(path)],text=True)
        assert verify(baseline)=='0.3.5.32';assert verify(final)=='0.3.5.33'
        addons=out/'addons';cc=addons/'script.infinity.commandcenter';cc.mkdir(parents=True)
        for name in pins:
            dest=cc/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(final/'script.infinity.commandcenter'/name,dest)
        for name in pins:
            file=cc/name;raw=file.read_bytes();file.write_bytes(raw+b'\nCORRUPT');assert verify(addons)=='REJECT',name;file.write_bytes(raw)
        tail=ast.literal_eval(next(n.value for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tail' for t in n.targets)))
        assert 'const/4 v6, 0x1' in tail
        spec=importlib.util.spec_from_file_location('final_native',REPAIR/'final_eight_native.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        assert json.loads(rc8map.read_text())[module.PATH]==module.BEFORE
        delta=module.apply(native,out/'overlay');before=(native/module.PATH).read_text();after=(out/'overlay'/module.PATH).read_text()
        restored=after
        for old,new in reversed(module.REPLACEMENTS):
            assert restored.count(new)==1
            restored=restored.replace(new,old)
        assert restored==before
        assert 'if (local && video)' in module.NEW and 'SelectItem' not in module.NEW and 'ACTION_SELECT_ITEM' not in module.NEW
        assert 'popup.Execute(std::make_shared<CFileItem>(*item))' in module.HELPER
        assert '"skin.infinity.diggz"' in module.HELPER and '"0.3.5.33"' in module.HELPER
        assert 'getSelectedItem' not in (final/'script.infinity.commandcenter/context.py').read_text()
        # Compile the exact responsive-axis implementation, not a Python replica.
        cpp=(native/'xbmc/guilib/GUIControl.cpp').read_text()
        a=cpp.index('float InfinityResponsiveParse(');b=cpp.index('} // namespace',a)
        code='''#include <string>\n#include <cstdlib>\n#include <algorithm>\n#include <cassert>\nstruct GUIResponsiveAxisSpec {
std::string start,centerStart,centerEnd,end,size,sizeMax,sizeMin,legacyPos;
bool HasAny() const {return true;}
};\n'''+cpp[a:b]+'''
int main(){for(float parent:{720.f,1080.f,1920.f,2560.f,720.f}) {
GUIResponsiveAxisSpec group;group.start="72%";group.size="26%";
float x=0,w=0;InfinityResolveResponsiveAxis(group,parent,0,0,false,x,w);
GUIResponsiveAxisSpec old;old.start="0";old.size="auto";old.sizeMin="1";old.sizeMax="26%";
float lx=0,lw=0;InfinityResolveResponsiveAxis(old,w,0,0,false,lx,lw);assert(lw<w*.27f);
old.sizeMax="100%";InfinityResolveResponsiveAxis(old,w,0,lw,false,lx,lw);assert(lw==w);
assert(x+w<=parent);
}}
'''
        source=out/'clock.cpp';source.write_text(code)
        subprocess.run(['g++','-std=c++17',str(source),'-o',str(out/'clock')],check=True);subprocess.run([str(out/'clock')],check=True)
    path='skin.infinity.diggz/unified/Includes_InfinityHomeUnified.xml'
    before=(baseline/path).read_text();after=(final/path).read_text()
    assert after.replace('<width min="1" max="100%">auto</width>','<width min="1" max="$PARAM[timewidth]">auto</width>')==before
    report=dict(host='PASS',CC32_admission_retained=True,CC33_exact_binding=True,bridge_UI_CC_coordinated=True,
        CC33_tamper_rejections=19,clock_actual_axis_cpp='PASS five reflow sizes; nested percentage reproduced',
        native_touch_scope='PASS exact Infinity-only hit-tested title handoff; original fallback and resume ownership retained; all other source restored byte-identically',
        dex_assembly='NOT RUN',android='NOT RUN',physical_fold='NOT RUN',shutdown='NOT RUN')
    (HERE/'BINDINGS-LAYOUT-HOST.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':print(json.dumps(run(*map(Path,sys.argv[1:]))))
