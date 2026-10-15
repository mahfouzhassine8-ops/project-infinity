#!/usr/bin/env python3
"""Compile the actual PVR event job/header with host UI/event boundaries."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source-root', type=Path, required=True)
root = parser.parse_args().source_root.resolve()
with tempfile.TemporaryDirectory(prefix='infinity-pvr-event-contract-') as temporary:
    work = Path(temporary)
    files = {
        'events/EventLog.h': '''#pragma once
#include <memory>
#include <string>
#include <vector>
enum class EventLevel { Information, Error };
struct CNotificationEvent {
  std::string label, message, icon; EventLevel level;
  CNotificationEvent(const std::string& l,const std::string& m,const std::string& i,EventLevel e)
    :label(l),message(m),icon(i),level(e){}
};
struct EventLog {
  std::vector<std::shared_ptr<CNotificationEvent>> events;
  void Add(std::shared_ptr<CNotificationEvent> event){events.push_back(event);}
};
''',
        'events/NotificationEvent.h': '#pragma once\n#include "events/EventLog.h"\n',
        'ServiceBroker.h': '''#pragma once
#include "events/EventLog.h"
struct CServiceBroker {
  inline static EventLog* log=nullptr;
  static EventLog* GetEventLog(){return log;}
};
''',
        'dialogs/GUIDialogKaiToast.h': '''#pragma once
#include <string>
struct CGUIDialogKaiToast {
  enum Type {Error, Info};
  inline static int notifications=0;
  static void QueueNotification(Type,const std::string&,const std::string&,int,bool){++notifications;}
};
''',
        'harness.cpp': '''#include "pvr/PVREventLogJob.h"
#include "ServiceBroker.h"
#include "dialogs/GUIDialogKaiToast.h"
#include <cassert>
#include <iostream>
bool CJob::ShouldCancel(unsigned int,unsigned int)const{return false;}
using Role=CJob::CheckpointResponsibility;
struct Callback : IJobCallback {void OnJobComplete(unsigned int,bool,CJob*)override{}};
struct UnreviewedSubclass : PVR::CPVREventLogJob {bool DoWork()override{return true;}};
struct TypeStringSpoof : CJob {
  const char* GetType()const override{return "pvr-eventlog-job";}
  bool DoWork()override{return true;}
};
int main(){
  PVR::CPVREventLogJob exact; Callback callback;
  assert(exact.GetCheckpointResponsibility(nullptr)==Role::NonPersistent);
  assert(exact.GetCheckpointResponsibility(&callback)==Role::Unknown);
  UnreviewedSubclass derived;
  assert(derived.GetCheckpointResponsibility(nullptr)==Role::Unknown);
  TypeStringSpoof spoof;
  assert(spoof.GetCheckpointResponsibility(nullptr)==Role::Unknown);
  EventLog log;CServiceBroker::log=&log;
  exact.AddEvent(false,EventLevel::Information,"label","message","icon");
  exact.AddEvent(true,EventLevel::Error,"error","detail","icon");
  assert(exact.DoWork());
  assert(log.events.size()==2&&CGUIDialogKaiToast::notifications==1);
  assert(log.events[0]->message=="message"&&log.events[1]->level==EventLevel::Error);
  CServiceBroker::log=nullptr;
  assert(exact.DoWork());
  std::cout<<"PASS actual PVR event job: exact class/null callback only; subclasses and type spoof rejected; memory-only event/toast paths\\n";
}
''',
    }
    for name, content in files.items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    executable = work / 'pvr-event-contract'
    subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-parameter', '-I'+str(work), '-I'+str(root/'xbmc'),
                    str(root/'xbmc/pvr/PVREventLogJob.cpp'), str(work/'harness.cpp'),
                    '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True, timeout=5)
