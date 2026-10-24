"""CC applied-result regression; actual generated Java verifier, no shutdown."""
import ast, hashlib, json, pathlib, shutil, subprocess, tempfile

HERE=pathlib.Path(__file__).resolve().parent
REPAIR=HERE.parents[1]

def run(components):
    tree=ast.parse((REPAIR/'dex_binding.py').read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    # Execute the production Java-source generator only. DEX assembly/native
    # startup remain separate gates and are never claimed by this host check.
    end=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='classes' for t in n.targets))
    with tempfile.TemporaryDirectory() as temp:
        out=pathlib.Path(temp);stage=pathlib.Path(components)
        env={'inspect':lambda *a:(None,{}),'apk':None,'stage':stage,'jars':None,'out':out,'HERE':REPAIR,'json':json,'Path':pathlib.Path,'sha':lambda b:hashlib.sha256(b).hexdigest()}
        exec(compile(ast.Module(body=function.body[:end],type_ignores=[]),'production-generator','exec'),env)
        addons=out/'addons';cc=addons/'script.infinity.commandcenter';cc.mkdir(parents=True)
        pins=json.loads((stage/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
        assert len(pins)==19
        for name in pins:
            dest=cc/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/'script.infinity.commandcenter'/name,dest)
        probe=out/'Probe.java';probe.write_text('''import java.io.*;import java.lang.reflect.*;
public class Probe { public static void main(String[] a) throws Exception {
Class<?> c=Class.forName("com.projectinfinity.kodi.InfinityInstalledCheckpointInstaller");
Method m=c.getDeclaredMethod("verify",File.class);m.setAccessible(true);
Object r=m.invoke(null,new File(a[0]));System.out.print(r==null?"REJECT":r); }}''')
        subprocess.run(['java','com.sun.tools.javac.Main','--release','8','-d',str(out/'classes'),str(env['source']),str(probe)],check=True)
        def verify():return subprocess.check_output(['java','-cp',str(out/'classes'),'Probe',str(addons)],text=True)
        assert verify()=='0.3.5.32'
        for name in pins:
            file=cc/name;raw=file.read_bytes();file.write_bytes(raw+b'\nCORRUPT')
            assert verify()=='REJECT',name
            file.write_bytes(raw)
        # Production receipt/return uses v6. A non-null verified version enters
        # the dedicated tail; the old tail left v6 false after CC27 mismatch.
        tail=ast.literal_eval(next(n.value for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tail' for t in n.targets)))
        def receipt(block):
            registers={'v2':'old','v7':'0.3.5.32','v6':0}
            for line in block.splitlines():
                words=line.strip().replace(',','').split()
                if words[:1]==['move-object']:registers[words[1]]=registers[words[2]]
                if words[:1]==['const/4']:registers[words[1]]=int(words[2],0)
            return registers['v2'],bool(registers['v6'])
        assert receipt(tail.replace('    const/4 v6, 0x1\n',''))==('0.3.5.32',False)
        assert receipt(tail)==('0.3.5.32',True)
    return dict(host='PASS',valid_CC32='PASS',individual_source_tamper_rejections=len(pins),receipt_register_regression='PASS',dex_assembly='NOT RUN',android='NOT RUN',shutdown='NOT RUN',physical_fold='NOT RUN')
if __name__=='__main__':
    import sys
    result=run(sys.argv[1]);(HERE/'INSTALLER-HOST.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
