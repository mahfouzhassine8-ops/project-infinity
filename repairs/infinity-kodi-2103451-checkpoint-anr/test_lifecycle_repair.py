"""Actual queue/sender bodies and checkpoint branches; GUI/native-window peers stubbed."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TEST = r'''
int main(int argc,char** argv){
 assert(argc==2);const std::string mode=argv[1];
 CApplicationMessenger messenger;CApplication application;
 currentMessenger=&messenger;currentApplication=&application;
 auto send=[&](uint32_t id,bool wait){return messenger.SendMsg(ThreadMessage(id),wait);};
 auto pending=[&]{std::lock_guard<CCriticalSection> lock(messenger.m_critSection);return messenger.m_vecMessages.size();};
 auto awaitSender=[&]{for(int i=0;i<1000 && waiting.load()==0;++i)std::this_thread::sleep_for(1ms);assert(waiting.load()==1);};
 auto finish=[&]{assert(liveMessages==0 && waiting==0);assert(messenger.m_vecMessages.empty() && messenger.m_vecWindowMessages.empty());};
 if(mode=="synchronous-display"){
   auto result=std::async(std::launch::async,[&]{return send(TMSG_DISPLAY_DESTROY,true);});
   awaitSender();application.Process();
   assert(result.wait_for(3s)==std::future_status::ready && result.get()==42);
   assert(observed==std::vector<uint32_t>{TMSG_DISPLAY_DESTROY});
   assert(checkpointPumps==1 && normalProcessReached==0);finish();
 }else if(mode=="ack-after-handler"){
   handlerBarrier.enabled=true;
   auto result=std::async(std::launch::async,[&]{return send(TMSG_DISPLAY_DESTROY,true);});
   awaitSender();
   auto watcher=std::async(std::launch::async,[&]{handlerBarrier.reached();assert(result.wait_for(0ms)==std::future_status::timeout);handlerBarrier.release();});
   application.Process();watcher.get();
   assert(result.wait_for(3s)==std::future_status::ready && result.get()==42);finish();
 }else if(mode=="unrelated-fifo"){
   send(17,false);send(TMSG_GUI_MESSAGE,false);send(TMSG_DISPLAY_SETUP,false);send(18,false);send(TMSG_DISPLAY_DESTROY,false);
   application.Process();
   assert((observed==std::vector<uint32_t>{TMSG_DISPLAY_SETUP,TMSG_DISPLAY_DESTROY}));
   assert(pending()==2 && messenger.m_vecWindowMessages.size()==1);
   assert(messenger.m_vecMessages.front()->dwMessage==17);
   InfinityAndroidCheckpoint::active=false;messenger.ProcessMessages();messenger.ProcessWindowMessages();
   assert((observed==std::vector<uint32_t>{TMSG_DISPLAY_SETUP,TMSG_DISPLAY_DESTROY,17,18,TMSG_GUI_MESSAGE}));finish();
 }else if(mode=="wrong-thread"){
   auto result=std::async(std::launch::async,[&]{return send(TMSG_DISPLAY_DESTROY,true);});
   awaitSender();auto wrong=std::async(std::launch::async,[&]{messenger.ProcessCheckpointDisplayMessages();});wrong.get();
   assert(observed.empty() && pending()==1 && result.wait_for(0ms)==std::future_status::timeout);
   application.Process();assert(result.get()==42);finish();
 }else if(mode=="inactive-normal"){
   InfinityAndroidCheckpoint::active=false;
   auto result=std::async(std::launch::async,[&]{return send(TMSG_DISPLAY_DESTROY,true);});
   awaitSender();messenger.ProcessCheckpointDisplayMessages();
   assert(observed.empty() && pending()==1);
   messenger.ProcessMessages();assert(result.get()==42);
   assert(send(17,true)==42); // existing same-GUI-thread immediate path
   application.Process();assert(normalProcessReached==1 && checkpointPumps==0);finish();
 }else if(mode=="ordered-bounded-burst"){
   send(TMSG_DISPLAY_SETUP,false);send(TMSG_DISPLAY_DESTROY,false);send(TMSG_DISPLAY_SETUP,false);
   enqueueDuringHandler=true;application.Process();
   assert((observed==std::vector<uint32_t>{TMSG_DISPLAY_SETUP,TMSG_DISPLAY_DESTROY,TMSG_DISPLAY_SETUP}));
   assert(pending()==1); // admitted while a real handler was running, retained for next pass
   application.Process();assert(observed.back()==TMSG_DISPLAY_DESTROY && observed.size()==4);finish();
 }else if(mode=="stopped-cleanup"){
   auto result=std::async(std::launch::async,[&]{return send(TMSG_DISPLAY_DESTROY,true);});
   awaitSender();messenger.Stop();application.Process();
   assert(observed.empty() && pending()==1 && result.wait_for(0ms)==std::future_status::timeout);
   messenger.Cleanup(); // unchanged native messenger cleanup owns queued waiters
   assert(result.get()==-1);assert(observed.empty());
   assert(send(TMSG_DISPLAY_SETUP,false)==-1);finish();
 }else assert(false);
 std::cout<<"HOST_PASS "<<mode<<"; native window and EGL are stubbed\n";
}
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if (a.out / 'RESULTS.json').exists():
        raise ValueError('Preserve completed evidence; do not repeat passing checks')
    sys.path.insert(0, str(ROOT / 'repairs/python-exit-2103334'))
    old = load(ROOT / 'repairs/python-exit-2103334/test_messenger.py', 'p0_real_sender_peer')
    candidate = load(HERE / 'stage_lifecycle_repair.py', 'p0_lifecycle_stage')
    inputs = {name: (a.baseline / name).read_bytes() for name in candidate.PINS}
    outputs = {name: (a.source / name).read_bytes() for name in candidate.PINS}
    for name, raw in inputs.items():
        assert hashlib.sha256(raw).hexdigest() == candidate.PINS[name]
        assert candidate.transform(name, raw) == outputs[name]
    cpp = outputs[candidate.CPP].decode()
    base_cpp = inputs[candidate.CPP].decode()
    app = outputs[candidate.APP].decode()
    base_app = inputs[candidate.APP].decode()
    header = outputs[candidate.HEADER].decode()
    preserved = {}
    signatures = ['void CApplicationMessenger::Cleanup()',
                  'int CApplicationMessenger::SendMsg(ThreadMessage&& message, bool wait)',
                  'void CApplicationMessenger::ProcessMessages()',
                  'void CApplicationMessenger::ProcessWindowMessages()',
                  'void CApplicationMessenger::ProcessMessage(',
                  'bool CApplicationMessenger::IsProcessThread() const']
    for signature in signatures:
        before = old.function(base_cpp, signature)
        assert before == old.function(cpp, signature), signature
        preserved[signature] = hashlib.sha256(before.encode()).hexdigest()
    for signature in ['int CApplication::Run()', 'bool CApplication::Stop(',
                      'bool CApplication::Cleanup()', 'void CApplication::FrameMove(',
                      'void CApplication::StopPlaying()', 'bool CApplication::PlayFile(',
                      'bool CApplication::PlayMedia(']:
        before = old.function(base_app, signature)
        assert before == old.function(app, signature), signature
        preserved[signature] = hashlib.sha256(before.encode()).hexdigest()
    assert 'void Stop() { m_bStop = true; }' in header

    prefix = old.PREFIX.replace('STOP_TYPE', 'std::atomic<bool>')
    prefix = '#include <vector>\n' + prefix
    defines = '\n'.join(re.search(r'^#define ' + name + r'\s+[^\n]+', header, re.M).group(0)
                        for name in ['TMSG_MASK_APPLICATION', 'TMSG_DISPLAY_SETUP', 'TMSG_DISPLAY_DESTROY'])
    declarations = r'''
class CApplicationMessenger;
class CApplication;
namespace InfinityAndroidCheckpoint {
inline std::atomic<bool> active{true};
inline bool IsActive(){return active.load();}
void Pump(CApplication&);
}
'''
    # The existing peer defines CServiceBroker before the messenger declaration.
    point = prefix.index('struct CServiceBroker')
    prefix = prefix[:point] + declarations + prefix[point:]
    prefix = prefix.replace('struct CServiceBroker {static CWinSystemBase* GetWinSystem()',
                            'struct CServiceBroker {static CApplicationMessenger* GetAppMessenger();static CWinSystemBase* GetWinSystem()')
    prefix = prefix.replace(' void ProcessMessage(ThreadMessage* m){++dispatched;m->SetResult(42);}',
                            ' void ProcessMessage(ThreadMessage*);\n void ProcessCheckpointDisplayMessages();\n'
                            ' std::thread::id m_processThreadId=std::this_thread::get_id();\n'
                            ' bool IsProcessThread()const;')
    assert 'void ProcessCheckpointDisplayMessages();' in prefix
    peers = r'''
class CApplication {public:void Process();void OnApplicationMessage(ThreadMessage*);};
CApplicationMessenger* currentMessenger=nullptr;
CApplication* currentApplication=nullptr;
CApplicationMessenger* CServiceBroker::GetAppMessenger(){return currentMessenger;}
int checkpointPumps=0,normalProcessReached=0;
bool enqueueDuringHandler=false;
Barrier handlerBarrier;
std::vector<uint32_t> observed;
void InfinityAndroidCheckpoint::Pump(CApplication&){++checkpointPumps;} // failed coordinator boundary
void CApplicationMessenger::ProcessMessage(ThreadMessage* message){++dispatched;currentApplication->OnApplicationMessage(message);}
'''
    process = old.function(app, 'void CApplication::Process()')
    process = process[:process.index('  // dispatch the messages generated')] + '  ++normalProcessReached;\n}\n'
    guard = old.function(app, 'void CApplication::OnApplicationMessage(')
    guard = guard[:guard.index('  uint32_t msg = pMsg->dwMessage;')] + r'''
  // Real display-handler/EGL boundary: assert the messenger's call and ack order,
  // without pretending that a native Android surface was actually destroyed.
  handlerBarrier.pause();
  observed.push_back(pMsg->dwMessage);
  if(enqueueDuringHandler){enqueueDuringHandler=false;
    currentMessenger->SendMsg(ThreadMessage(TMSG_DISPLAY_DESTROY),false);}
  pMsg->SetResult(42);
}
'''
    bodies = '\n'.join(old.function(cpp, sig) for sig in signatures[:4])
    bodies += '\n' + old.function(cpp, 'bool CApplicationMessenger::IsProcessThread() const')
    bodies += '\n' + old.function(cpp, 'void CApplicationMessenger::ProcessCheckpointDisplayMessages()')
    unit = a.out / 'lifecycle.cpp'
    unit.write_text(prefix + defines + '\n' + peers + process + guard + bodies + TEST)
    exe = a.out / 'lifecycle'
    command = ['g++', '-std=c++17', '-pthread', '-Wall', '-Wextra', '-Werror',
               '-DTARGET_ANDROID', str(unit), '-o', str(exe)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    (a.out / 'COMPILE.txt').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode:
        raise RuntimeError('Compile failed; inspect ' + str(a.out / 'COMPILE.txt'))
    results = []
    cases = ['synchronous-display', 'ack-after-handler', 'unrelated-fifo', 'wrong-thread',
             'inactive-normal', 'ordered-bounded-burst', 'stopped-cleanup']
    for case in cases:
        result = subprocess.run([str(exe), case], capture_output=True, text=True, timeout=10)
        row = {'case': case, 'status': 'HOST_PASS' if result.returncode == 0 else 'FAIL',
               'exit_code': result.returncode, 'output': result.stdout + result.stderr}
        results.append(row)
        if result.returncode:
            (a.out / 'FAILED-CASE.json').write_text(json.dumps(row, indent=2) + '\n')
            raise RuntimeError('Host case failed: ' + case)
        print(result.stdout, end='')
    report = {'purpose': 'isolated checkpoint lifecycle repair host verification',
              'compiler': command, 'cases': results, 'unchanged_method_sha256': preserved,
              'source_delta': json.loads((a.source / 'SOURCE-DELTA.json').read_text()),
              'real_sender_wait_and_consumer_threads': True, 'GUI_and_native_window_peers_stubbed': True,
              'android_execution': False, 'physical_fold_acceptance': False,
              'watched_job_persistence_repaired': False, 'apk_built_or_signed': False}
    (a.out / 'RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
