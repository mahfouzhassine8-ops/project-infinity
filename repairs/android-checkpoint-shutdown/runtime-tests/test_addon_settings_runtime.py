#!/usr/bin/env python3
"""Exercise production add-on settings helpers with live and missing owners."""
import argparse
from pathlib import Path
import subprocess
import tempfile

PEERS = r'''
#include <algorithm>
#include <cassert>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#define TARGET_ANDROID
namespace InfinityAndroidCheckpoint {
 int failures=0;
 void RecordFailure(const char*,const char*){++failures;}
}
struct CVariant { int value; explicit CVariant(int v):value(v){} };
enum class SettingType { Integer, List };
struct Setting { virtual ~Setting()=default; virtual SettingType GetType()const=0; };
struct CSettingInt:Setting {
 using Value=int; int value=42;
 static SettingType Type(){return SettingType::Integer;}
 SettingType GetType()const override{return Type();}
 int GetValue()const{return value;} bool SetValue(int v){value=v;return true;}
};
struct CSettingList:Setting {
 SettingType GetType()const override{return SettingType::List;}
 SettingType GetElementType()const{return SettingType::Integer;}
};
struct CSettingsBase {
 bool loaded=true, list=false; int reads=0,writes=0;
 std::shared_ptr<CSettingInt> integer=std::make_shared<CSettingInt>();
 virtual ~CSettingsBase()=default;
 virtual bool IsLoaded()const{return loaded;}
 std::shared_ptr<Setting> GetSetting(const std::string& key){
  ++reads;if(key=="missing")return {};
  if(list)return std::make_shared<CSettingList>();
  return integer;
 }
 std::vector<CVariant> GetList(const std::string&){return {CVariant(42)};}
 bool SetList(const std::string&,const std::vector<CVariant>& v){++writes;return v.size()==1&&v[0].value==7;}
};
'''
CASES = r'''
int main(){
 std::shared_ptr<CSettingsBase> settings;
 int value=99;std::vector<int> values={99};
 const auto transform=[](CVariant v){return v.value;};
 assert(!GetSettingValue<CSettingInt>(settings,"key",value)&&value==99);
 assert(!SetSettingValue<CSettingInt>(settings,"key",7));
 assert(!GetSettingValueList<CSettingInt>(settings,"key",transform,values)&&values==std::vector<int>{99});
 assert(!SetSettingValueList<CSettingInt>(settings,"key",{7}));
 assert(InfinityAndroidCheckpoint::failures==2);
 settings=std::make_shared<CSettingsBase>();settings->loaded=false;
 assert(!GetSettingValue<CSettingInt>(settings,"key",value));assert(settings->reads==0);
 settings->loaded=true;
 assert(!GetSettingValue<CSettingInt>(settings,"",value));assert(settings->reads==0);
 assert(!GetSettingValue<CSettingInt>(settings,"missing",value)&&value==99);
 assert(GetSettingValue<CSettingInt>(settings,"key",value)&&value==42);
 assert(SetSettingValue<CSettingInt>(settings,"key",7)&&settings->integer->value==7);
 assert(!GetSettingValueList<CSettingInt>(settings,"key",transform,values));
 settings->list=true;
 assert(!GetSettingValue<CSettingInt>(settings,"key",value));
 values.clear();assert(GetSettingValueList<CSettingInt>(settings,"key",transform,values)&&values==std::vector<int>{42});
 assert(SetSettingValueList<CSettingInt>(settings,"key",{7})&&settings->writes==1);
 assert(InfinityAndroidCheckpoint::failures==2);
}
'''

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',type=Path,required=True)
    args=parser.parse_args()
    source=(args.runtime/'xbmc/interfaces/legacy/Settings.cpp').read_text()
    helpers=source[source.index('template<class TSetting>'):source.index('Settings::Settings(')]
    with tempfile.TemporaryDirectory(prefix='addon-settings-') as folder:
        root=Path(folder);cpp=root/'test.cpp';binary=root/'test'
        cpp.write_text(PEERS+helpers+CASES)
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
                        '-fsanitize=undefined','-fno-sanitize-recover=all',str(cpp),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
    print('PASS: production settings reads/writes/lists reject missing owners and preserve valid behavior')

if __name__=='__main__':
    main()
