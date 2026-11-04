#!/usr/bin/env python3
"""One bounded source-bound HOST measurement; never builds an APK or runs Kodi."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, statistics, subprocess, sys, time

HERE=Path(__file__).resolve().parent
NATIVE=Path('/tmp/kodi451-restored-native')
PROOF=Path('/tmp/kodi451-restored-proof')
OLD=Path('/workspace/project-infinity/repairs/android-checkpoint-shutdown/native/test_runtime_file_saves.py')
DEFAULT_OUT=Path('/tmp/infinity-settings-measurement-20261104')

def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=DEFAULT_OUT)
    ap.add_argument('--generate-only',action='store_true')
    ap.add_argument('--execute-prepared',action='store_true')
    args=ap.parse_args()
    out=args.out;out.mkdir(parents=True,exist_ok=True)
    if (out/'PASS-STARTED.json').exists(): raise RuntimeError('One pass already started; retain evidence, do not rerun')
    assert (HERE/'SELECTED-PASS.json').is_file()
    baseline=json.loads((PROOF/'BASELINE-NATIVE-SOURCE-MAP.json').read_text())
    candidate=json.loads((PROOF/'CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    bound={}
    def read(name):
        raw=(NATIVE/name).read_bytes();h=sha(raw)
        assert h==baseline[name]==candidate[name],name
        bound[name]={'sha256':h,'same_in451_and452':True}
        return raw.decode()
    spec=importlib.util.spec_from_file_location('existing_file_save_fixture',OLD)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    function=old.function
    addon=read('xbmc/addons/Addon.cpp')
    start=addon.rfind('namespace\n{',0,addon.index('struct CheckpointAddonTree'))
    end=addon.index('bool InfinityAndroidCheckpoint::CheckpointAudioPolicyFile()',start)
    registry=addon[start:end]
    assert 'CheckpointLoadedAddonSettings' not in registry
    serializer_header=read('xbmc/settings/SettingsValueXmlSerializer.h')
    serializer_decl=serializer_header[serializer_header.index('class CSettingsValueXmlSerializer :'):]
    serializer_decl=serializer_decl.replace('private:','public:\n  std::string SerializeValuesOriginal(const CSettingsManager*) const;\nprivate:',1)
    serializer_source=read('xbmc/settings/SettingsValueXmlSerializer.cpp')
    serializer=serializer_source[serializer_source.index('static constexpr char SETTINGS_XML_ROOT[]'):]
    assert serializer.count('CSettingsValueXmlSerializer::SerializeValues(')==1
    serializer=serializer.replace('CSettingsValueXmlSerializer::SerializeValues(', 'CSettingsValueXmlSerializer::SerializeValuesOriginal(',1)
    wrapper=r'''
std::string CSettingsValueXmlSerializer::SerializeValues(const CSettingsManager* manager)const {
  const auto started=Observation::enabled?Observation::Clock::now():Observation::Clock::time_point{};
  auto result=SerializeValuesOriginal(manager);
  ++Observation::serializations; // common measurement peer, on and off
  Observation::serializedBytes+=result.size();
  Observation::maxSerialized=std::max<uint64_t>(Observation::maxSerialized,result.size());
  if(Observation::enabled) Observation::serializationNs+=Observation::elapsed(started);
  return result; // move/NRVO; no second serialization, logs or values retained
}
'''
    defs=read('xbmc/settings/lib/SettingDefinitions.h')
    defines='\n'.join(re.search(r'^#define '+name+r'\s+[^\n]+',defs,re.M).group(0) for name in ('SETTING_XML_ROOT_VERSION','SETTING_XML_ELM_SETTING','SETTING_XML_ATTR_ID','SETTING_XML_ELM_DEFAULT'))
    manager=function(read('xbmc/settings/lib/SettingsManager.cpp'),'bool CSettingsManager::Save(')
    base=function(read('xbmc/settings/SettingsBase.cpp'),'bool CSettingsBase::SaveValuesToXml(')
    save=function(read('xbmc/addons/settings/AddonSettings.cpp'),'bool CAddonSettings::Save(CXBMCTinyXML& doc) const')
    source=(HERE/'peers.cpp.in').read_text()+'\n'+defines+'\n'+serializer_decl+'\n'+serializer+wrapper+manager+'\n'+base+'\nnamespace ADDON {\n'+save+'\n}\n'+registry+(HERE/'measure.cpp.in').read_text()
    unit=out/'measurement.cpp';unit.write_text(source)
    for signature, original in [('bool CSettingsManager::Save(',manager),('bool CSettingsBase::SaveValuesToXml(',base),('bool CAddonSettings::Save(CXBMCTinyXML& doc) const',save),('void TrackLoadedAddonTree(',function(addon,'void TrackLoadedAddonTree(')),('bool ConfirmAddonSave(',function(addon,'bool ConfirmAddonSave('))]:
        assert function(source,signature)==original,signature
    (out/'SOURCE-BINDING.json').write_text(json.dumps({
      'files':bound,'existing_test_extractor':{'file':str(OLD),'sha256':sha(OLD.read_bytes())},
      'generated_cpp_sha256':sha(source.encode()),
      'unchanged_bodies':['owner registry helpers','CSettingsManager::Save','CSettingsBase::SaveValuesToXml','CAddonSettings::Save'],
      'serializer_adaptor':'Only public entry renamed Original plus wrapper; original body unchanged; no extra serialization.',
      'peers':['Synthetic CSettingsManager tree/locks/hooks and CAddonSettings owner construction','ASCII pinned TinyXML Parse, without Kodi charset detection','Normal file-save success supplied; no disk/durability claim'],
      'excluded':['actual Kodi/Android','Scudo allocator','native settings load/deserialization','actual data/settings values','derived owner serialization overrides','shutdown coordinator','provider execution'],
    },indent=2)+'\n')
    tiny=out/'deps/tinyxml-2.6.2_2'
    make=read('tools/depends/target/tinyxml/Makefile')
    expected=re.search(r'^SHA512=(\w+)',make,re.M).group(1)
    assert hashlib.sha512((out/'deps/tinyxml-2.6.2_2.tar.gz').read_bytes()).hexdigest()==expected
    command=['g++','-std=c++17','-O2','-pthread','-DTIXML_USE_STL','-DTARGET_ANDROID','-Wall','-Wextra',
             '-I',str(tiny/'include'),str(unit)]+[str(tiny/'src'/n) for n in ('tinyxml.cpp','tinyxmlparser.cpp','tinyxmlerror.cpp','tinystr.cpp')]+['-o',str(out/'measurement')]
    if args.execute_prepared:
        prepared=json.loads((out/'PREPARED.json').read_text())
        assert sha(unit.read_bytes())==prepared['cpp_sha256']
        assert sha((out/'measurement').read_bytes())==prepared['binary_sha256']
        assert command==json.loads((out/'COMPILE-COMMAND.json').read_text())
    else:
        built=subprocess.run(command,capture_output=True,text=True,timeout=60)
        (out/'COMPILE.txt').write_text(built.stdout+built.stderr)
        (out/'COMPILE-COMMAND.json').write_text(json.dumps(command,indent=2)+'\n')
        if built.returncode: raise RuntimeError('Host compile failed; see COMPILE.txt. Measurement not started.')
        (out/'PREPARED.json').write_text(json.dumps({'cpp_sha256':sha(unit.read_bytes()),'binary_sha256':sha((out/'measurement').read_bytes())},indent=2)+'\n')
    if args.generate_only:
        print('Source binding and host compile completed; no measurement started.');return
    # No broad suite: one finite manifest, fresh process per cell, counterbalanced on/off ordering.
    plan=[]
    for scenario in ('clean_fresh','dirty_reused','dirty_fresh','transient_large'):
        for pair in range(3):
            for observer in (('off','on') if pair%2==0 else ('on','off')):
                plan.append({'scenario':scenario,'pair':pair,'observer':observer})
    stamp={'source_checkpoint':json.loads((HERE/'SELECTED-PASS.json').read_text())['source_checkpoint'],'pid':os.getpid(),'planned_cells':plan}
    (out/'PASS-STARTED.json').write_text(json.dumps(stamp,indent=2)+'\n')
    deadline=time.monotonic()+120
    rows=[]
    cpu=min(os.sched_getaffinity(0))
    def pin_cpu(): os.sched_setaffinity(0,{cpu})
    for cell in plan:
        remaining=deadline-time.monotonic()
        if remaining<=0: raise RuntimeError('Bounded pass elapsed; no automatic retry')
        run=subprocess.run([str(out/'measurement'),cell['scenario'],cell['observer']],capture_output=True,text=True,timeout=min(30,remaining),preexec_fn=pin_cpu)
        name=f"{cell['scenario']}-{cell['pair']}-{cell['observer']}"
        (out/(name+'.stderr.txt')).write_text(run.stderr)
        if run.returncode:
            (out/(name+'.failed.txt')).write_text(run.stdout)
            raise RuntimeError('Measurement cell failed; no automatic retry: '+name)
        row=json.loads(run.stdout)
        row.update(pair=cell['pair'],cpu_affinity=cpu)
        # Structured numeric results only; synthetic identity intentionally literal.
        assert row['addon']=='diagnostic.synthetic.settings'
        assert 'synthetic-settings-owner-only/settings.xml' not in run.stdout
        assert row['observer_dropped']==0 and row['observer_fixed_bytes']<=64*1024
        (out/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
        rows.append(row)
    summaries=[]
    for scenario in ('clean_fresh','dirty_reused','dirty_fresh','transient_large'):
        cells=[r for r in rows if r['scenario']==scenario]
        pair_ratios=[];alloc_delta=[]
        for pair in range(3):
            off=next(r for r in cells if r['pair']==pair and r['observer']=='off')
            on=next(r for r in cells if r['pair']==pair and r['observer']=='on')
            assert off['serializations']==on['serializations']
            assert off['serialized_bytes_total']==on['serialized_bytes_total']
            for field in ('registry','dirty','live_registry','pending','destroyed','baseline_size','pending_size','fixture_value_capacity','cpp_live_requested_bytes'):
                assert off['final'][field]==on['final'][field],(scenario,pair,field)
            delta=on['final']['cpp_allocations']-off['final']['cpp_allocations'];alloc_delta.append(delta)
            assert delta==0,'Observer added heap allocations'
            pair_ratios.append(100*(on['loop_ns']/off['loop_ns']-1))
        measured=[r for r in cells if r['observer']=='on']
        first=measured[0]
        summaries.append({
           'scenario':scenario,'iterations':first['iterations'],'serializations':first['serializations'],
           'serialized_bytes_total':first['serialized_bytes_total'],'max_serialized_bytes':first['max_serialized_bytes'],
           'serializations_per_second_host_median':statistics.median(r['serializations']/(r['serialization_ns']/1e9) for r in measured),
           'median_serialization_ms':statistics.median(r['serialization_ns']/1e6 for r in measured),
           'observer_loop_overhead_percent_pairs':pair_ratios,'observer_loop_overhead_percent_median':statistics.median(pair_ratios),
           'observer_extra_heap_allocations':alloc_delta,'unchanged_functional_results':True,
           'representative_snapshots':first['snapshots'],'representative_final':first['final'],
           'rss_kib_final_range':[min(r['final']['rss_kib'] for r in measured),max(r['final']['rss_kib'] for r in measured)],
           'cpp_requested_peak_range':[min(r['final']['cpp_peak_requested_bytes'] for r in measured),max(r['final']['cpp_peak_requested_bytes'] for r in measured)]
        })
    summary={'status':'COMPLETED_ONE_BOUNDED_HOST_PASS','cells':len(rows),'summaries':summaries,
             'observer_fixed_bytes':rows[0]['observer_fixed_bytes'],'device_instrumentation_deployed':False,
             'host_allocator':'glibc/libstdc++; global new requested-byte accounting common to both arms; header overhead affects host RSS',
             'owner_tree_measurement':'Synthetic settings-manager tree; exact registry retention and real pinned TinyXML pipeline',
             'limits':'Does not attribute historical add-on or reproduce Scudo/OOM, actual Kodi callbacks, disk persistence, or Android peak. Live requested C++ bytes are not total process/native RSS.',
             'no_production_changes':True,'no_apk_native_engine_build':True,'no_shutdown_test':True}
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'status':summary['status'],'cells':len(rows),'observer_fixed_bytes':summary['observer_fixed_bytes'],
      'scenarios':[{'scenario':s['scenario'],'live_owners':s['representative_final']['live_registry'],'retained_baseline_bytes':s['representative_final']['baseline_size'],'cpp_peak':s['representative_final']['cpp_peak_requested_bytes'],'overhead_percent_median':round(s['observer_loop_overhead_percent_median'],2)} for s in summaries]},indent=2))
if __name__=='__main__':main()
