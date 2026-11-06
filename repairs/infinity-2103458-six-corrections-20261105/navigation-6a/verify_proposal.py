"""Bounded compiled-source-fragment proof; NOT an Android or full-engine test."""
import ast
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import proposal as p


def main():
    result = {'kind': 'UNAPPLIED proposal / compiled native fragments and Python mocks',
              'checks': [], 'Android': 'NOT RUN', 'Fold': 'NOT RUN', 'ARM64_engine': 'NOT RUN'}
    def check(name, value):
        result['checks'].append({'name': name, 'pass': bool(value)})
        assert value, name

    sources = p.candidate()
    source_map = json.loads(p.NATIVE_MAP.read_text())
    inspected = ['xbmc/windows/GUIMediaWindow.cpp', 'xbmc/interfaces/builtins/GUIBuiltins.cpp',
                 'xbmc/interfaces/json-rpc/GUIOperations.cpp', 'xbmc/guilib/GUIWindowManager.cpp',
                 'xbmc/addons/Skin.h', p.NAV]
    result['source_bindings'] = {}
    for path in inspected:
        digest = p.sha((p.NATIVE / path).read_bytes())
        check('source map: ' + path, digest == source_map[path])
        result['source_bindings'][path] = digest
    media = (p.NATIVE / inspected[0]).read_text()
    start = media.index('      if (m_vecItems->GetPath() == "?")', media.index('case GUI_MSG_WINDOW_INIT:'))
    end = media.index('      if (message.GetParam2() == PLUGIN_REFRESH_DELAY)', start)
    init = media[start:end]  # Exact existing initialization/history decision code.
    start = media.index('  const std::string startFolder = GetStartFolder(dir);', media.index('bool CGUIMediaWindow::IsSameStartFolder'))
    same = media[start:media.index('\n}', start)]
    native = sources[p.NAV][1].decode()
    check('native proposal removes cleanly', native.replace('#include "addons/Skin.h"\n', '').replace(p.HOOK, '') == sources[p.NAV][0].decode())
    builtin = (p.NATIVE / inspected[1]).read_text()
    rpc = (p.NATIVE / inspected[2]).read_text()
    wm = (p.NATIVE / inspected[3]).read_text()
    check('original builtin descendant guard remains', '->IsSameStartFolder(params[0])' in builtin and '|| !bIsSameStartFolder)' in builtin)
    check('RPC posts parameters without builtin folder suppression', 'PostMsg(TMSG_GUI_ACTIVATE_WINDOW' in rpc and 'IsSameStartFolder' not in rpc)
    check('native activation restrictions retained', 'if (!force && HasModalDialog(true))' in wm and 'msg.SetStringParams(params)' in wm)

    harness = r'''
#include <algorithm>
#include <iostream>
#include <memory>
#include <string>
#include <vector>
constexpr int WINDOW_INVALID=-1;
struct Msg { std::vector<std::string> p; int previous;
 std::string GetStringParam(unsigned i=0) const {return i<p.size()?p[i]:"";}
 unsigned GetNumStringParams() const {return p.size();}
 int GetParam1() const{return previous;} int GetParam2() const{return 10025;}
};
struct Skin {std::string id; std::string ID() const{return id;}};
std::shared_ptr<Skin> g_SkinInfo;
namespace StringUtils {bool EqualsNoCase(std::string a,std::string b){
 std::transform(a.begin(),a.end(),a.begin(),::tolower);
 std::transform(b.begin(),b.end(),b.begin(),::tolower);return a==b;}}
namespace URIUtils {std::string trim(std::string a){while(!a.empty()&&a.back()=='/')a.pop_back();return a;}
 bool PathEquals(const std::string&a,const std::string&b,bool=true){return trim(a)==trim(b);}
 bool PathHasParent(const std::string&a,const std::string&b){return a.rfind(b,0)==0;}
 bool IsRemote(const std::string&){return false;}}
struct Items {std::string path;int cache=0;std::string GetPath()const{return path;}
 void SetPath(const std::string&p){path=p;}void RemoveDiscCache(int){cache++;}};
struct Window {std::shared_ptr<Items> m_vecItems=std::make_shared<Items>(); std::string m_startDirectory;
 int historyCalls=0;std::string attempted;int loads=0;
 int GetID(){return 10025;}bool WaitForNetwork(){return true;}
 std::string GetRootPath(){return "";}std::string GetStartFolder(const std::string&d){return d;}
 void SetHistoryForPath(const std::string&){historyCalls++;}
 bool IsSameStartFolder(const std::string&dir){ SAME }
 void Init(Msg&message,bool proposed,bool fail){
   if(proposed){
 HOOK
   }
   INIT
   // Stand-in for directory loading only: record the requested directory;
   // an injected failure falls back to root, rather than claiming success.
   attempted=m_vecItems->GetPath();loads++;
   bool same=URIUtils::PathEquals(m_vecItems->GetPath(),m_startDirectory,true);
   if(fail)m_vecItems->SetPath("");
   if(same){m_startDirectory=m_vecItems->GetPath();SetHistoryForPath(m_startDirectory);}
 }
};
int main(int argc,char**argv){if(argc<8)return 2;
 std::string mode=argv[1]; Window w;w.m_vecItems->path=argv[2];w.m_startDirectory=argv[3];
 if(std::string(argv[4])!="NULL")g_SkinInfo=std::make_shared<Skin>(Skin{argv[4]});
 Msg msg;msg.previous=std::stoi(argv[5]);for(int i=7;i<argc;i++)msg.p.emplace_back(argv[i]);
 bool skipped=mode=="before"&&msg.previous==10025&&w.IsSameStartFolder(msg.GetStringParam());
 if(!skipped)w.Init(msg,mode=="after",std::string(argv[6])=="fail");
 std::cout<<w.m_vecItems->path<<'\t'<<w.m_startDirectory<<'\t'<<w.attempted<<'\t'<<w.loads<<'\t'<<w.historyCalls<<'\t'<<skipped<<'\n';
}
'''.replace(' SAME ', same).replace(' HOOK\n', p.HOOK).replace('   INIT', init)
    movies, tv = p.TARGETS.values()
    skin = 'skin.infinity.diggz'
    flag = 'infinity-library-direct'
    with tempfile.TemporaryDirectory(prefix='infinity-navigation-proof-') as directory:
        d = Path(directory)
        cpp = d / 'fragments.cpp'
        cpp.write_text(harness)
        binary = d / 'proof'
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-DTARGET_ANDROID', str(cpp), '-o', str(binary)], check=True, capture_output=True)
        result['compiled_fragment_sha256'] = p.sha(cpp.read_bytes())
        check('native fragments compile with warnings as errors', True)
        def run(mode, current, root, target, previous=10000, selected_skin=skin, params=None, failure=False):
            args = [str(binary), mode, current, root, selected_skin, str(previous), 'fail' if failure else 'ok']
            args += params if params is not None else [target, 'return', flag]
            return subprocess.check_output(args, text=True).rstrip('\n').split('\t')
        for target in (movies, tv):
            child = target + '12/'
            before = run('before', child, target, target)
            after = run('after', child, target, target)
            check('before retained-child reproduction: ' + target, before[0] == child)
            check('proposed explicit root from Home: ' + target, after[0] == target and after[1] == target and after[3] == '1')
            before = run('before', child, target, target, previous=10025)
            after = run('after', child, target, target, previous=10025)
            check('before builtin suppression: ' + target, before[5] == '1' and before[0] == child)
            check('proposed RPC entry from child: ' + target, after[0] == target and after[1] == target and after[3] == '1')
            for initial in ('', '?', target, 'plugin://fixture-provider/category/'):
                after = run('after', initial, '', target)
                check('first/cross-directory entry: ' + target + initial, after[0] == target and after[1] == target)
            after = run('after', child, target, target, failure=True)
            check('failed target attempted once; no forced success: ' + target, after[0] == '' and after[2] == target and after[3] == '1')
        negatives = [
            ('ordinary return', skin, [movies, 'return']),
            ('wrong flag', skin, [movies, 'return', 'other']),
            ('additional parameter', skin, [movies, 'return', flag, 'extra']),
            ('no loaded skin', 'NULL', [movies, 'return', flag]),
            ('other skin', 'skin.estuary', [movies, 'return', flag]),
            ('non-return mode', skin, [movies, 'replace', flag]),
            ('unsupported path', skin, ['sources://video/', 'return', flag]),
        ]
        for name, selected_skin, params in negatives:
            before = run('before', movies+'12/', movies, movies, selected_skin=selected_skin, params=params)
            after = run('after', movies+'12/', movies, movies, selected_skin=selected_skin, params=params)
            check('unchanged negative: ' + name, before == after)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(binary)], check=True, capture_output=True)
        check('non-Android unaffected', run('before', movies+'12/', movies, movies) == run('after', movies+'12/', movies, movies))

    old = {}; new = {}
    exec(compile(sources[p.HELPER][0], p.HELPER, 'exec'), old)
    exec(compile(sources[p.HELPER][1], 'UNAPPLIED-helper', 'exec'), new)
    class Kodi:
        def __init__(self, reply): self.reply=reply; self.calls=[]
        def executeJSONRPC(self, raw): self.calls.append(json.loads(raw)); return json.dumps(self.reply)
    class GUI:
        def __init__(self): self.messages=[]
        def Dialog(self): return self
        def ok(self, *args): self.messages.append(args)
    for action, path in p.TARGETS.items():
        kodi=Kodi({'result':'OK'}); gui=GUI()
        check('helper dispatch: '+action, new['run'](action,kodi,gui) is True and kodi.calls == [
            {'jsonrpc':'2.0','id':1,'method':'GUI.ActivateWindow','params':{'window':'videos','parameters':[path,'return',flag]}}])
        kodi=Kodi({'error':{'code':-32100}}); gui=GUI()
        check('RPC rejection remains visible: '+action, new['run'](action,kodi,gui) is False and len(gui.messages)==1)
    for path in ('files', '/storage/self/primary/Download/', 'plugin://fixture-provider/'):
        a=Kodi({'result':'OK'});b=Kodi({'result':'OK'})
        check('ordinary helper activation unchanged: '+path, old['activate'](a,GUI(),path)==new['activate'](b,GUI(),path) and a.calls==b.calls)
    kodi=Kodi({'result':'OK'})
    check('flag unavailable to arbitrary paths', new['activate'](kodi,GUI(),'plugin://fixture-provider/',True) is False and not kodi.calls)
    trees=[ast.parse(sources[p.HELPER][i]) for i in (0,1)]
    funcs=[{n.name:ast.dump(n) for n in t.body if isinstance(n,ast.FunctionDef)} for t in trees]
    check('all unrelated helper functions unchanged', all(funcs[0][n]==funcs[1][n] for n in funcs[0] if n not in ('activate','run')))
    check('run old actions unchanged', ast.dump(ast.Module(body=trees[0].body[-2].body, type_ignores=[])) == ast.dump(ast.Module(body=trees[1].body[-2].body[1:], type_ignores=[])))
    drawer = sources[p.DRAWER][1].decode()
    for action,path in p.TARGETS.items():
        drawer=drawer.replace('RunScript(script.infinity.commandcenter,library-navigation,%s)'%action, 'ActivateWindow(Videos,%s,return)'%path)
    check('drawer reverse-byte preservation', drawer.encode()==sources[p.DRAWER][0])
    xml=ET.fromstring(sources[p.DRAWER][1])
    for cid,action in [('1198104','library-movies'),('1198111','library-tv')]:
        check('intended visible control only: '+cid, 'RunScript(script.infinity.commandcenter,library-navigation,%s)'%action in [n.text for n in xml.find('.//control[@id="%s"]'%cid).findall('onclick')])
    # The generator and proof must not have applied any runtime edit.
    for path,(before,_) in sources.items():
        actual=(p.NATIVE/path if path==p.NAV else p.ROOT/path).read_bytes()
        check('production source unchanged: '+path, actual==before)
    result['pass_count']=len(result['checks'])
    result['limitations']=[
        'Native directory loading, locks, permissions, window manager and Back input were not executed; their original source is preserved.',
        'Harness reproduces the source conditions, not the user device incident.',
        'RPC OK means admitted request, not completed navigation.',
        'No full ARM64 compile, engine link, APK, Android or physical acceptance result.'
    ]
    (p.HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pass_count':result['pass_count'],'kind':result['kind'],'Android':result['Android']}))


if __name__=='__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        evidence = {'exit_code': error.returncode, 'stdout': (error.stdout or b'').decode(),
                    'stderr': (error.stderr or b'').decode(), 'kind': 'host fragment compilation failure'}
        with (p.HERE/'RETAINED-FAILURES.jsonl').open('a') as output:
            output.write(json.dumps(evidence)+'\n')
        print(json.dumps(evidence,indent=2))
        raise
