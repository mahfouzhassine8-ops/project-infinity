#!/usr/bin/env python3
"""Review exact producer/path authorization and real staging/namespace synchronization."""
import argparse,subprocess,tempfile
from pathlib import Path
CODE=r'''
#include "platform/android/activity/InfinityScriptPersistence.h"
#include <cassert>
#include <filesystem>
#include <fstream>
using namespace InfinityScriptPersistence;
int main(int argc,char**argv){assert(argc==3);std::string root=argv[1],mode=argv[2];
const std::string weather="service.infinity.chooser.weather.snapshot:weather_snapshot.py";
Admit(1,weather);Admit(2,"unreviewed:service.py");Observed(1);Observed(2);
std::string exact="/data/user/0/com.projectinfinity.kodi/files/infinity-chooser-weather/snapshot.json.pending";
Touch(1,exact);assert(Get().paths.at(exact).optional);Touch(2,exact);assert(!Get().paths.at(exact).optional);
for(const auto& path:std::vector<std::string>{"/data/user/x/com.projectinfinity.kodi/files/infinity-chooser-weather/snapshot.json.pending","/data/user/0/com.projectinfinity.kodi/files/infinity-chooser-weather/snapshot.json","/tmp/snapshot.json.pending"}){Touch(1,path);assert(!Get().paths.at(path).optional);}
std::string reviewed="/data/data/com.projectinfinity.kodi/files/infinity-chooser-weather/snapshot.json.pending";Touch(1,reviewed);assert(Get().paths.at(reviewed).optional);auto contract=Get().paths.at(reviewed);
std::string staging=root+"/snapshot.json.pending";if(mode=="present")std::ofstream(staging)<<"weather labels";
if(mode=="symlink")assert(::symlink("/dev/null",staging.c_str())==0);
if(mode=="required")contract.optional=false;
if(mode=="missing-parent")staging=root+"/missing/snapshot.json.pending";
// Transfer the reviewed namespace attributes to a host fixture; run the actual sync worker.
CommitWorker({{staging,contract}});assert(Get().commitFinished);
assert(Get().committed==(mode=="absent"||mode=="present"));
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args()
 with tempfile.TemporaryDirectory(prefix='weather-contract-') as t:
  t=Path(t);(t/'test.cpp').write_text(CODE);subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-I'+str(a.runtime/'xbmc'),str(t/'test.cpp'),'-o',str(t/'test')],check=True)
  for mode in ['absent','present','symlink','required','missing-parent']:
   f=t/mode;f.mkdir();subprocess.run([str(t/'test'),str(f),mode],check=True)
 print('PASS: reviewed weather staging absence; actual files synced; wrong writer, required file loss, symlink and missing parent rejected')
if __name__=='__main__':main()
