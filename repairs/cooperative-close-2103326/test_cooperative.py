#!/usr/bin/env python3
"""Production methods/real locks+clock; Python C API and Android are explicit fakes."""
import argparse,subprocess,tempfile,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'shutdown-2103313'))
import native_patch as patch
spec=importlib.util.spec_from_file_location('host3313',HERE.parent/'shutdown-2103313/test_native.py')
host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
function,no_includes=host.function,host.no_includes
PREFIX,INVOKER_STUB,SERVICE_STUB,TESTS=host.PREFIX,host.INVOKER_STUB,host.SERVICE_STUB,host.TESTS
def run(source):
    changed = {n: (source/n).read_text() for n in patch.ALLOWED}
    assert 'GetInstance().BeginShutdown()' in changed[patch.APP]
    assert 'GetXBPython().BeginShutdown()' in changed[patch.APP]
    header = no_includes(changed[patch.MANAGER_H]).replace('protected:', 'public:').replace('private:', 'public:')
    code = '#include "InfinityShutdownTrace.h"\n' + PREFIX + header + no_includes(changed[patch.MANAGER])
    for sig in ('void XBPython::BeginShutdown()', 'bool XBPython::ShutdownGraceExpired() const',
                'void XBPython::RegisterPythonMonitorCallBack('):
        code += function(changed[patch.PYTHON], sig)
    code += INVOKER_STUB + function(changed[patch.INVOKER], 'bool CPythonInvoker::stop(bool abort)')
    code += SERVICE_STUB
    for sig in ('void CServiceAddonManager::Stop()', 'void CServiceAddonManager::Stop(const std::string& addonId)',
                'void CServiceAddonManager::Stop(const std::map<std::string, int>::value_type& service)'):
        code += 'namespace ADDON {\n' + function(changed[patch.SERVICE],sig) + '}\n'
    code += TESTS
    with tempfile.TemporaryDirectory(prefix='infinity-shutdown-') as tmp:
        cpp=Path(tmp)/'production_shutdown.cpp';cpp.write_text(code)
        binary=Path(tmp)/'shutdown_test'
        subprocess.run(['g++','-std=c++17','-pthread','-Wall','-Wextra','-Werror',
                        '-Wno-unused-parameter','-I'+str(source/'xbmc/platform/android/activity'),str(cpp),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True,timeout=15)


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
 app=(a.source/'xbmc/application/Application.cpp').read_text()
 for signature in ('void CApplication::PrepareAndroidShutdownScripts(int exitCode)','bool CApplication::Stop(int exitCode)'):
  body=function(app,signature)
  assert body.count('GetXBPython().BeginShutdown()')==1
  assert body.index('GetSettings()->Save()')<body.index('GetXBPython().BeginShutdown()')
  assert body.index('g_SkinInfo->SaveSettings()')<body.index('GetXBPython().BeginShutdown()')
  assert body.index('GetInstance().BeginShutdown()')<body.index('AnnounceQuit(exitCode)')
 run(a.source)
