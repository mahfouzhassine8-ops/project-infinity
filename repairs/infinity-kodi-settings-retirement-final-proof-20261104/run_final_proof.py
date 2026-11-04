#!/usr/bin/env python3
"""Bounded isolated implementation pass; a native coverage gap blocks promotion."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import re
import subprocess

HERE=Path(__file__).resolve().parent
NATIVE=Path('/tmp/kodi451-restored-native')
OUT=Path('/tmp/infinity-settings-retirement-final-results-20261104')
EXTRACTOR=Path('/workspace/project-infinity/repairs/android-checkpoint-shutdown/native/test_runtime_file_saves.py')

def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    plan=json.loads((HERE/'SELECTED-TESTS.json').read_text())
    OUT.mkdir(exist_ok=True)
    if (OUT/'STARTED.json').exists(): raise RuntimeError('Bounded pass already started; no automatic rerun')
    expected=json.loads(Path('/tmp/kodi451-restored-proof/CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    baseline=json.loads(Path('/tmp/kodi451-restored-proof/BASELINE-NATIVE-SOURCE-MAP.json').read_text())
    binding={}
    def read(name):
        raw=(NATIVE/name).read_bytes();h=sha(raw);assert h==expected[name]
        binding[name]={'sha256':h,'identical_in451_and452':h==baseline[name]}
        return raw.decode()
    spec=importlib.util.spec_from_file_location('extractor',EXTRACTOR)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    function=old.function
    setting=read('xbmc/settings/lib/Setting.cpp')
    setting_header=read('xbmc/settings/lib/Setting.h')
    manager=read('xbmc/settings/lib/SettingsManager.cpp')
    settings=read('xbmc/addons/settings/AddonSettings.cpp')
    addon=read('xbmc/addons/Addon.cpp')
    read('xbmc/settings/SettingsValueXmlSerializer.cpp')
    definitions=[
        function(setting,'bool CSettingString::SetValue('),
        function(setting,'void CSettingString::SetDefault('),
        function(manager,'bool CSettingsManager::AddSetting(const std::shared_ptr<CSetting>& setting,'),
    ]
    start=settings.index('template<class TSetting>\nSettingPtr InitializeFromOldSettingWithoutDefinition(')
    add=function(settings,'template<class TSetting>\nSettingPtr AddSettingWithoutDefinition(')
    end=settings.index(add)+len(add)
    definitions.append(settings[start:end])
    add_string=function(settings,'std::shared_ptr<CSetting> CAddonSettings::AddSetting(const std::string& settingId,\n                                                     const std::string& value)')
    update=function(addon,'void CAddon::UpdateSetting(')
    inline_from_string=re.search(r'bool FromString\(const std::string &value\) override \{ return SetValue\(value\); \}',setting_header).group(0)
    peers=(HERE/'coverage_peers.cpp.in').read_text().replace('bool FromString(const std::string&)override;',inline_from_string)
    cpp=peers+'\n'+'\n'.join(definitions)+'\nnamespace ADDON {\n'+add_string+'\n'+update+'\n}\n'+(HERE/'coverage_case.cpp.in').read_text()
    (OUT/'native_coverage.cpp').write_text(cpp)
    for signature,original in [('bool CSettingString::SetValue(',definitions[0]),('void CSettingString::SetDefault(',definitions[1]),('void CAddon::UpdateSetting(',update)]:
        assert function(cpp,signature)==original
    (OUT/'SOURCE-BINDING.json').write_text(json.dumps({
        'files':binding,'extractor_sha256':sha(EXTRACTOR.read_bytes()),'coverage_cpp_sha256':sha(cpp.encode()),
        'native_unchanged_bodies':['CAddon::UpdateSetting','CAddonSettings::AddSetting(string)',
          'AddSettingWithoutDefinition','InitializeFromOldSettingWithoutDefinition generic/string',
          'CSettingsManager::AddSetting(group)','CSettingString::SetDefault','CSettingString::SetValue','CSettingString::FromString'],
        'coverage_peers':['Already initialized/loaded synthetic owner','Containers and section registration','Accepted simple-value validation','Value-change notification counter; no real providers or profiles'],
        'prototype':'Independent C++ protocol implementation; no native integration claim',
        'prototype_sha256':{p.name:sha(p.read_bytes()) for p in (HERE/'contract.hpp',HERE/'contract_tests.cpp')},
        'production_changes':0,
    },indent=2)+'\n')
    commands={
        'contract':['g++','-std=c++17','-O2','-pthread','-Wall','-Wextra','-I',str(HERE),str(HERE/'contract_tests.cpp'),'-o',str(OUT/'contract')],
        'native_coverage':['g++','-std=c++17','-O2','-pthread','-DTARGET_ANDROID','-Wall','-Wextra',str(OUT/'native_coverage.cpp'),'-o',str(OUT/'native_coverage')],
    }
    for name,command in commands.items():
        result=subprocess.run(command,capture_output=True,text=True,timeout=60)
        (OUT/(name+'-COMPILE.txt')).write_text(result.stdout+result.stderr)
        if result.returncode: raise RuntimeError('Host compile failed before cases: '+name)
    (OUT/'COMPILE-COMMANDS.json').write_text(json.dumps(commands,indent=2)+'\n')
    (OUT/'STARTED.json').write_text(json.dumps({'selected':plan['prototype_cases']+plan['source_bound_cases'],'binaries':{n:sha((OUT/n).read_bytes()) for n in commands}},indent=2)+'\n')
    results=[]
    for case in plan['prototype_cases']:
        run=subprocess.run([str(OUT/'contract'),case],capture_output=True,text=True,timeout=20)
        (OUT/(case+'.stderr.txt')).write_text(run.stderr)
        if run.returncode: raise RuntimeError('Selected prototype case failed; no rerun: '+case)
        row=json.loads(run.stdout);assert row['case']==case and row['expected_result_observed']
        results.append(row)
    coverage=subprocess.run([str(OUT/'native_coverage')],capture_output=True,text=True,timeout=20)
    (OUT/'native_coverage.stderr.txt').write_text(coverage.stderr)
    if coverage.returncode: raise RuntimeError('Source-bound coverage case failed; no rerun')
    witness=json.loads(coverage.stdout)
    assert witness['case']==plan['source_bound_cases'][0]
    assert witness['expected_result_observed'] and not witness['production_coverage_certificate']
    results.append(witness)
    final={'decision':'EARLY_RETIREMENT_BLOCKED','cases':len(results),'prototype_cases':len(plan['prototype_cases']),
      'source_bound_coverage_witnesses':1,'results':results,
      'contract_limits':'Only the encapsulated synthetic API has complete mutation coverage. Native integration, ownership callbacks and write-lease placement remain unproven.',
      'concrete_blocker':'Actual loaded-owner UpdateSetting(undefined key) changes registered serialized settings without the ordinary OnSettingChanged notification; callback-only revision tracking misses it.',
      'production_patch_delivered':False,'native_sources_changed':0,'APKs_built_signed_locked':0,
      'stop_rule':'Gate reached; retain existing safe checkpoint behavior. No expansion into shared-settings rewrite or unrelated systems.'}
    (OUT/'RESULTS.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps({k:final[k] for k in ('decision','cases','prototype_cases','source_bound_coverage_witnesses','production_patch_delivered')},indent=2))

if __name__=='__main__':main()
