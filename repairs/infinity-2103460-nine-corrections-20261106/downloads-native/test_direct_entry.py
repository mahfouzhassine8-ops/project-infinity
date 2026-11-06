from pathlib import Path
import subprocess,json
P=Path(__file__).resolve().parent;cpp=(P/'native/xbmc/video/windows/GUIWindowVideoNav.cpp').read_text();start=cpp.index('      if (g_SkinInfo && g_SkinInfo->ID() == "skin.infinity.diggz" &&',cpp.index('// An explicit Infinity drawer entry'))
end=cpp.index('\n#endif',start);body=cpp[start:end]
source=r'''
#include <cassert>
#include <memory>
#include <string>
#include <vector>
#include <iostream>
struct Skin{std::string id="skin.infinity.diggz";std::string ID(){return id;}};auto g_SkinInfo=std::make_shared<Skin>();
struct Message{std::vector<std::string>p;int GetNumStringParams(){return p.size();}std::string GetStringParam(int i){return p.at(i);}};
struct Items{std::string path="previous-child";void SetPath(const std::string&s){path=s;}};
std::string apply(Message message){Items items;auto*m_vecItems=&items;
BODY
return items.path;}
int main(){
for(auto path:{"plugin://script.infinity.commandcenter/?action=movies","plugin://script.infinity.commandcenter/?action=tv"}){assert(apply({{path,"return","infinity-library-direct"}})==path);}
for(auto path:{"videodb://movies/titles/","videodb://tvshows/titles/"}){assert(apply({{path,"return","infinity-library-direct"}})==path);}
assert(apply({{"plugin://other/","return","infinity-library-direct"}})=="previous-child");
assert(apply({{"plugin://script.infinity.commandcenter/?action=movies","return"}})=="previous-child");
assert(apply({{"plugin://script.infinity.commandcenter/?action=movies","return","other"}})=="previous-child");
g_SkinInfo->id="skin.other";assert(apply({{"plugin://script.infinity.commandcenter/?action=tv","return","infinity-library-direct"}})=="previous-child");
std::cout<<"PASS8 actual conditional cases; Android NOT_RUN\n";}
'''.replace('BODY',body)
out=Path('/dev/shm/infinity-native-direct-entry');out.mkdir(exist_ok=True);(out/'conditional.cpp').write_text(source)
r=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(out/'conditional.cpp'),'-o',str(out/'conditional')],capture_output=True,text=True);assert r.returncode==0,r.stderr
r=subprocess.run([str(out/'conditional')],capture_output=True,text=True);(out/'result.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
(P/'DIRECT-ENTRY-RESULT.json').write_text(json.dumps({'status':'PASS8_ACTUAL_NATIVE_CONDITIONAL_HOST_BOUNDARIES','Android':'NOT_RUN','scope':'two exact Home menus + original native title roots; wrong provider/skin/flag/missing param rejected'},indent=2)+'\n');print(r.stdout)
