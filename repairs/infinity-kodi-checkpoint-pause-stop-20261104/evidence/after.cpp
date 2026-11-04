#define TMSG_MASK_MESSAGE                 0xFFFF0000 // only keep the high bits to route messages
#define TMSG_MASK_APPLICATION             (1<<30) //Don't use bit 31 as it'll fail to build, using unsigned variable to hold the message.
#define TMSG_MASK_PLAYLISTPLAYER          (1<<29)
#define TMSG_MASK_GUIINFOMANAGER          (1<<28)
#define TMSG_MASK_WINDOWMANAGER           (1<<27)
#define TMSG_MASK_PERIPHERALS             (1<<26)
#define TMSG_PLAYLISTPLAYER_PLAY          TMSG_MASK_PLAYLISTPLAYER + 0
#define TMSG_PLAYLISTPLAYER_NEXT          TMSG_MASK_PLAYLISTPLAYER + 1
#define TMSG_PLAYLISTPLAYER_PREV          TMSG_MASK_PLAYLISTPLAYER + 2
#define TMSG_PLAYLISTPLAYER_ADD           TMSG_MASK_PLAYLISTPLAYER + 3
#define TMSG_PLAYLISTPLAYER_CLEAR         TMSG_MASK_PLAYLISTPLAYER + 4
#define TMSG_PLAYLISTPLAYER_SHUFFLE       TMSG_MASK_PLAYLISTPLAYER + 5
#define TMSG_PLAYLISTPLAYER_GET_ITEMS     TMSG_MASK_PLAYLISTPLAYER + 6
#define TMSG_PLAYLISTPLAYER_PLAY_ITEM_ID  TMSG_MASK_PLAYLISTPLAYER + 7
#define TMSG_PLAYLISTPLAYER_INSERT        TMSG_MASK_PLAYLISTPLAYER + 8
#define TMSG_PLAYLISTPLAYER_REMOVE        TMSG_MASK_PLAYLISTPLAYER + 9
#define TMSG_PLAYLISTPLAYER_SWAP          TMSG_MASK_PLAYLISTPLAYER + 10
#define TMSG_PLAYLISTPLAYER_REPEAT        TMSG_MASK_PLAYLISTPLAYER + 11
#define TMSG_MEDIA_PLAY                   TMSG_MASK_PLAYLISTPLAYER + 12
#define TMSG_MEDIA_STOP                   TMSG_MASK_PLAYLISTPLAYER + 13
#define TMSG_MEDIA_PAUSE                  TMSG_MASK_PLAYLISTPLAYER + 14
#define TMSG_MEDIA_RESTART                TMSG_MASK_PLAYLISTPLAYER + 15
#define TMSG_MEDIA_UNPAUSE                TMSG_MASK_PLAYLISTPLAYER + 16
#define TMSG_MEDIA_PAUSE_IF_PLAYING       TMSG_MASK_PLAYLISTPLAYER + 17
#define TMSG_MEDIA_SEEK_TIME              TMSG_MASK_PLAYLISTPLAYER + 18
#define TMSG_SHUTDOWN                     TMSG_MASK_APPLICATION + 0
#define TMSG_POWERDOWN                    TMSG_MASK_APPLICATION + 1
#define TMSG_QUIT                         TMSG_MASK_APPLICATION + 2
#define TMSG_HIBERNATE                    TMSG_MASK_APPLICATION + 3
#define TMSG_SUSPEND                      TMSG_MASK_APPLICATION + 4
#define TMSG_RESTART                      TMSG_MASK_APPLICATION + 5
#define TMSG_RESET                        TMSG_MASK_APPLICATION + 6
#define TMSG_RESTARTAPP                   TMSG_MASK_APPLICATION + 7
#define TMSG_ACTIVATESCREENSAVER          TMSG_MASK_APPLICATION + 8
#define TMSG_NETWORKMESSAGE               TMSG_MASK_APPLICATION + 9
#define TMSG_RESETSCREENSAVER TMSG_MASK_APPLICATION + 10
#define TMSG_VOLUME_SHOW                  TMSG_MASK_APPLICATION + 11
#define TMSG_DISPLAY_SETUP                TMSG_MASK_APPLICATION + 12
#define TMSG_DISPLAY_DESTROY              TMSG_MASK_APPLICATION + 13
#define TMSG_SETVIDEORESOLUTION           TMSG_MASK_APPLICATION + 14
#define TMSG_SWITCHTOFULLSCREEN           TMSG_MASK_APPLICATION + 15
#define TMSG_MINIMIZE                     TMSG_MASK_APPLICATION + 16
#define TMSG_TOGGLEFULLSCREEN             TMSG_MASK_APPLICATION + 17
#define TMSG_SETLANGUAGE                  TMSG_MASK_APPLICATION + 18
#define TMSG_RENDERER_FLUSH               TMSG_MASK_APPLICATION + 19
#define TMSG_INHIBITIDLESHUTDOWN          TMSG_MASK_APPLICATION + 20
#define TMSG_START_ANDROID_ACTIVITY       TMSG_MASK_APPLICATION + 21
#define TMSG_EXECUTE_SCRIPT               TMSG_MASK_APPLICATION + 22
#define TMSG_EXECUTE_BUILT_IN             TMSG_MASK_APPLICATION + 23
#define TMSG_EXECUTE_OS                   TMSG_MASK_APPLICATION + 24
#define TMSG_PICTURE_SHOW                 TMSG_MASK_APPLICATION + 25
#define TMSG_PICTURE_SLIDESHOW            TMSG_MASK_APPLICATION + 26
#define TMSG_LOADPROFILE                  TMSG_MASK_APPLICATION + 27
#define TMSG_VIDEORESIZE                  TMSG_MASK_APPLICATION + 28
#define TMSG_INHIBITSCREENSAVER           TMSG_MASK_APPLICATION + 29
#define TMSG_SYSTEM_POWERDOWN             TMSG_MASK_APPLICATION + 30
#define TMSG_RENDERER_PREINIT             TMSG_MASK_APPLICATION + 31
#define TMSG_RENDERER_UNINIT              TMSG_MASK_APPLICATION + 32
#define TMSG_EVENT                        TMSG_MASK_APPLICATION + 33
#define TMSG_MOVETOSCREEN                 TMSG_MASK_APPLICATION + 34
#define TMSG_UPDATE_PLAYER_ITEM TMSG_MASK_APPLICATION + 35
#define TMSG_SET_VOLUME                   TMSG_MASK_APPLICATION + 36
#define TMSG_SET_MUTE                     TMSG_MASK_APPLICATION + 37
#define TMSG_RESUMEAPP                    TMSG_MASK_APPLICATION + 38
#define TMSG_GUI_INFOLABEL                TMSG_MASK_GUIINFOMANAGER + 0
#define TMSG_GUI_INFOBOOL                 TMSG_MASK_GUIINFOMANAGER + 1
#define TMSG_UPDATE_CURRENT_ITEM          TMSG_MASK_GUIINFOMANAGER + 2
#define TMSG_CECTOGGLESTATE               TMSG_MASK_PERIPHERALS + 1
#define TMSG_CECACTIVATESOURCE            TMSG_MASK_PERIPHERALS + 2
#define TMSG_CECSTANDBY                   TMSG_MASK_PERIPHERALS + 3
#define TMSG_GUI_DIALOG_OPEN              TMSG_MASK_WINDOWMANAGER + 1
#define TMSG_GUI_ACTIVATE_WINDOW          TMSG_MASK_WINDOWMANAGER + 2
#define TMSG_GUI_PYTHON_DIALOG            TMSG_MASK_WINDOWMANAGER + 3
#define TMSG_GUI_WINDOW_CLOSE             TMSG_MASK_WINDOWMANAGER + 4
#define TMSG_GUI_ACTION                   TMSG_MASK_WINDOWMANAGER + 5
#define TMSG_GUI_ADDON_DIALOG             TMSG_MASK_WINDOWMANAGER + 6
#define TMSG_GUI_MESSAGE                  TMSG_MASK_WINDOWMANAGER + 7
#define TMSG_GUI_DIALOG_YESNO             TMSG_MASK_WINDOWMANAGER + 8
#define TMSG_GUI_DIALOG_OK                TMSG_MASK_WINDOWMANAGER + 9
#define TMSG_GUI_PREVIOUS_WINDOW          TMSG_MASK_WINDOWMANAGER + 10
#define TMSG_CALLBACK                     800
#define WINDOW_INVALID                     9999 // do not change. value is used to avoid include in headers.
#define PLAYBACK_STATE_STOPPED  0x0000
#define PLAYBACK_STATE_PLAYING  0x0001
#define PLAYBACK_STATE_VIDEO    0x0100
#define PLAYBACK_STATE_AUDIO    0x0200
#define PLAYBACK_STATE_CANNOT_PAUSE 0x0400
constexpr const int ACTION_PAUSE = 12;
constexpr const int ACTION_STOP = 13;
constexpr const int ACTION_PLAYER_PLAY = 79;
constexpr const int ACTION_MOVE_LEFT = 1;
// Host-only Android/window/player peers; production sender/queue/guards are appended unchanged.
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <future>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>
#include <type_traits>
#include <vector>
using namespace std::chrono_literals;
using CCriticalSection=std::recursive_mutex;
struct Barrier {
 std::mutex mutex;std::condition_variable cv;bool enabled=false,arrived=false,released=false;
 void pause(){std::unique_lock<std::mutex> l(mutex);if(!enabled)return;arrived=true;cv.notify_all();cv.wait(l,[&]{return released;});}
 void reached(){std::unique_lock<std::mutex> l(mutex);assert(cv.wait_for(l,3s,[&]{return arrived;}));}
 void release(){std::lock_guard<std::mutex> l(mutex);released=true;cv.notify_all();}
} payloadBarrier,displayBarrier;
std::atomic<int> waiting{0},liveMessages{0},liveActions{0};
std::mutex waitingMutex;std::condition_variable waitingCv;
struct CEvent {
 std::mutex mutex;std::condition_variable cv;bool signalled=false;
 explicit CEvent(bool){}
 void Wait(){std::unique_lock<std::mutex> lock(mutex);{std::lock_guard<std::mutex> q(waitingMutex);++waiting;}waitingCv.notify_all();cv.wait(lock,[&]{return signalled;});--waiting;}
 void Set(){std::lock_guard<std::mutex> lock(mutex);signalled=true;cv.notify_all();}
};
struct CThread {static std::thread::id GetCurrentThreadId(){return std::this_thread::get_id();}};
struct CSingleExit {
 CCriticalSection* mutex=nullptr;
 explicit CSingleExit(int){}
 explicit CSingleExit(CCriticalSection& m):mutex(&m){mutex->unlock();}
 ~CSingleExit(){if(mutex)mutex->lock();}
};
struct CAction {
 int m_id;
 explicit CAction(int id):m_id(id){++liveActions;}
 ~CAction(){payloadBarrier.pause();--liveActions;}
 int GetID()const{return m_id;}
};
namespace InfinityShutdownTrace {template<class...T>void Event(T&&...) {}}
constexpr int LOGERROR=1,LOGWARNING=2,LOGDEBUG=3;
struct CLog {template<class...T>static void LogF(int,const char*,T&&...){} template<class...T>static void Log(int,const char*,T&&...) {}};
struct ThreadMessage {
 uint32_t dwMessage;int param1=-1,param2=-1;int64_t param3=0;void* lpVoid=nullptr;
 std::string strParam;std::vector<std::string> params;
 std::shared_ptr<CEvent> waitEvent;std::shared_ptr<int> result;
 explicit ThreadMessage(uint32_t id,int p1=-1,int p2=-1,void* p=nullptr):dwMessage(id),param1(p1),param2(p2),lpVoid(p){++liveMessages;}
 ThreadMessage(ThreadMessage&& o):dwMessage(o.dwMessage),param1(o.param1),param2(o.param2),param3(o.param3),lpVoid(o.lpVoid),strParam(std::move(o.strParam)),params(std::move(o.params)),waitEvent(std::move(o.waitEvent)),result(std::move(o.result)){++liveMessages;}
 ~ThreadMessage(){--liveMessages;}
 void SetResult(int value){if(result)*result=value;}
};
struct ThreadMessageCallback {void (*callback)(void*);void* userptr;};
struct IMessageTarget {virtual void OnApplicationMessage(ThreadMessage*)=0;virtual ~IMessageTarget()=default;};
class CApplicationMessenger {
public:
 std::queue<ThreadMessage*> m_vecMessages,m_vecWindowMessages;
 std::map<int,IMessageTarget*> m_mapTargets;
 CCriticalSection m_critSection;
 std::thread::id m_guiThreadId=std::this_thread::get_id(),m_processThreadId=m_guiThreadId;
 std::atomic<bool> m_bStop{false};
 int SendMsg(ThreadMessage&&,bool);
 int SendMsg(uint32_t id,int p1,int p2,void* p){return SendMsg(ThreadMessage(id,p1,p2,p),true);}
 void PostMsg(uint32_t id){SendMsg(ThreadMessage(id),false);}
 void Cleanup();void ProcessMessages();void ProcessWindowMessages();void ProcessMessage(ThreadMessage*);
 void ProcessCheckpointDisplayMessages();bool IsProcessThread()const;
 void Stop(){m_bStop=true;}
};
namespace InfinityAndroidCheckpoint {
struct Owner {uint64_t generation=7;bool dirty=true,complete=false;};
struct State {
 std::mutex mutex;std::atomic<bool> active{true};bool sealed=true,startupInProgress=false,writeAdmissionStarted=true;
 std::string phase="CHECKPOINT_FAILED";int activeWrites=0;
 std::map<std::string,Owner> owners{{"pending-settings",{}},{"unknown-watched-owner",{}}};
 bool checkpointSaved=false,terminationAuthorized=false;int failures=1;
};
inline State state;inline State& Get(){return state;}
inline thread_local unsigned permissionDepth=0,acceptedPlaybackDepth=0,startupWriteDepth=0;
bool IsActive(){return Get().active.load();}
bool AllowNativeWrite(const char*);
class CheckpointWriteGuard {bool m_admitted=false;public:explicit CheckpointWriteGuard(const char*);~CheckpointWriteGuard();explicit operator bool()const{return m_admitted;}};
}
int checkpointPumps=0,normalFrames=0,playerCommands=0,windowActions=0,otherCallbacks=0,guardReceivers=0;
bool enqueueDisplayDuringHandler=false;
std::vector<uint32_t> displayObserved,otherObserved;
std::vector<int> controlObserved;
class CApplication:public IMessageTarget {
public:bool IsInitialized()const{return false;}void Process();bool OnAction(const CAction&);void OnApplicationMessage(ThreadMessage*)override;
};
inline CApplication g_application;
struct CGUIWindow {void OnAction(const CAction&){++windowActions;}};
class CGUIWindowManager:public IMessageTarget {
public:
 CGUIWindow fakeWindow;
 CGUIWindow* GetWindow(int){return &fakeWindow;}
 void OnApplicationMessage(ThreadMessage*)override;
 void SwitchToFullScreen(bool){}
};
struct CGUIComponent {CGUIWindowManager windows;CGUIWindowManager& GetWindowManager(){return windows;}};
struct CApplicationPlayer {bool playing=true,video=true,paused=false;bool IsPlaying()const{return playing;}bool HasVideo()const{return video;}bool IsPaused()const{return paused;}};
struct CApplicationPowerHandling {void ResetShutdownTimers(){}};
struct Components {
 std::shared_ptr<CApplicationPlayer> player=std::make_shared<CApplicationPlayer>();
 std::shared_ptr<CApplicationPowerHandling> power=std::make_shared<CApplicationPowerHandling>();
 template<class T>std::shared_ptr<T> GetComponent()const{if constexpr(std::is_same_v<T,CApplicationPlayer>)return player;else return power;}
};
struct CSettings {static constexpr int SETTING_POWERMANAGEMENT_SHUTDOWNTIME=1;int GetInt(int)const{return 0;}};
struct SettingsComponent {CSettings settings;CSettings* GetSettings(){return &settings;}};
struct ScreenSaver {bool IsInhibited()const{return false;}};
struct CWinSystemBase {ScreenSaver saver;int GetGfxContext(){return 0;}ScreenSaver* GetOSScreenSaver(){return &saver;}};
struct CServiceBroker {
 static CApplicationMessenger* messenger;
 static CApplicationMessenger* GetAppMessenger(){return messenger;}
 static CWinSystemBase* GetWinSystem(){static CWinSystemBase w;return &w;}
 static CGUIComponent* GetGUI(){static CGUIComponent gui;return &gui;}
 static Components& GetAppComponents(){static Components c;return c;}
 static SettingsComponent* GetSettingsComponent(){static SettingsComponent c;return &c;}
};
CApplicationMessenger* CServiceBroker::messenger=nullptr;
template<class...T>void android_printf(const char*,T&&...){}
bool infinityIsPictureInPicture(){return false;}
bool isHeadsetPlugged(){return false;}
struct CJNIAudioManager {static constexpr int AUDIOFOCUS_LOSS=-1;};
class CXBMCApp {
public:
 bool m_bResumePlayback=false,m_hasReqVisible=false,m_headsetPlugged=false;
 int m_playback_state=PLAYBACK_STATE_PLAYING|PLAYBACK_STATE_VIDEO;
 CCriticalSection m_applicationsMutex;std::map<int,int> m_applications;
 void KeepScreenOn(bool){}void RequestVisibleBehind(bool){}
 void onResume();void onPause();void onStop();void onAudioFocusChange(int);
};
namespace InfinityAndroidCheckpoint {void Pump(CApplication&){++checkpointPumps;} } // Coordinator body remains a peer; native write guards are exact.

bool IsCheckpointPlaybackControl(const ThreadMessage& message)
{
  // These Android lifecycle/focus requests target CApplication::OnAction,
  // whose existing checkpoint guard refuses execution before any player or
  // persistence work. Never admit a window-targeted or unrelated GUI action.
  if (message.dwMessage != TMSG_GUI_ACTION || message.param1 != WINDOW_INVALID ||
      message.param2 != -1 || message.param3 != 0 || !message.lpVoid || !message.strParam.empty() ||
      !message.params.empty())
    return false;

  const int action = static_cast<const CAction*>(message.lpVoid)->GetID();
  return action == ACTION_PAUSE || action == ACTION_STOP || action == ACTION_PLAYER_PLAY;
}
void CApplicationMessenger::Cleanup()
{
  std::unique_lock<CCriticalSection> lock(m_critSection);

  while (!m_vecMessages.empty())
  {
    ThreadMessage* pMsg = m_vecMessages.front();

    if (pMsg->waitEvent)
      pMsg->waitEvent->Set();

    delete pMsg;
    m_vecMessages.pop();
  }

  while (!m_vecWindowMessages.empty())
  {
    ThreadMessage* pMsg = m_vecWindowMessages.front();

    if (pMsg->waitEvent)
      pMsg->waitEvent->Set();

    delete pMsg;
    m_vecWindowMessages.pop();
  }
}
int CApplicationMessenger::SendMsg(ThreadMessage&& message, bool wait)
{
  std::shared_ptr<CEvent> waitEvent;
  std::shared_ptr<int> result;

  if (wait)
  {
    //Initialize result here as it's not needed for posted messages
    message.result = std::make_shared<int>(-1);
    // check that we're not being called from our application thread, else we'll be waiting
    // forever!
    if (m_guiThreadId != CThread::GetCurrentThreadId())
    {
      message.waitEvent = std::make_shared<CEvent>(true);
      waitEvent = message.waitEvent;
      result = message.result;
    }
    else
    {
      //OutputDebugString("Attempting to wait on a SendMessage() from our application thread will cause lockup!\n");
      //OutputDebugString("Sending immediately\n");
      ProcessMessage(&message);
      return *message.result;
    }
  }


  if (m_bStop)
    return -1;

  ThreadMessage* msg = new ThreadMessage(std::move(message));

  std::unique_lock<CCriticalSection> lock(m_critSection);

#if defined(TARGET_ANDROID)
  // Stop can occur after the fast-path check, before this queue lock. Recheck
  // while serialized with Cleanup: either the request is admitted before the
  // drain and its waiter is signalled there, or it is rejected here. Never
  // leave a late synchronous sender waiting on an already drained queue.
  if (m_bStop)
  {
    InfinityShutdownTrace::Event("milestone", "scripts.late_message_rejected", -1,
                                0, 0, 0, nullptr, "not_dispatched");
    delete msg;
    return -1;
  }
#endif

  if (msg->dwMessage == TMSG_GUI_MESSAGE)
    m_vecWindowMessages.push(msg);
  else
    m_vecMessages.push(msg);
  lock.unlock(); // this releases the lock on the vec of messages and
      //   allows the ProcessMessage to execute and therefore
      //   delete the message itself. Therefore any access
      //   of the message itself after this point constitutes
      //   a race condition (yarc - "yet another race condition")
      //
  if (waitEvent) // ... it just so happens we have a spare reference to the
                 //  waitEvent ... just for such contingencies :)
  {
    // ensure the thread doesn't hold the graphics lock
    CWinSystemBase* winSystem = CServiceBroker::GetWinSystem();
    //! @todo This won't really help as winSystem can die every single
    // moment on shutdown. A shared ptr would be a more valid solution
    // depending on the design dependencies.
    if (winSystem)
    {
      CSingleExit exit(winSystem->GetGfxContext());
      waitEvent->Wait();
    }
    return *result;
  }

  return -1;
}
void CApplicationMessenger::ProcessMessages()
{
  // process threadmessages
  std::unique_lock<CCriticalSection> lock(m_critSection);
  while (!m_vecMessages.empty())
  {
    ThreadMessage* pMsg = m_vecMessages.front();
    //first remove the message from the queue, else the message could be processed more then once
    m_vecMessages.pop();

    //Leave here as the message might make another
    //thread call processmessages or sendmessage

    std::shared_ptr<CEvent> waitEvent = pMsg->waitEvent;
    lock.unlock(); // <- see the large comment in SendMessage ^

    ProcessMessage(pMsg);

    if (waitEvent)
      waitEvent->Set();
    delete pMsg;

    lock.lock();
  }
}
void CApplicationMessenger::ProcessWindowMessages()
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  //message type is window, process window messages
  while (!m_vecWindowMessages.empty())
  {
    ThreadMessage* pMsg = m_vecWindowMessages.front();
    //first remove the message from the queue, else the message could be processed more then once
    m_vecWindowMessages.pop();

    // leave here in case we make more thread messages from this one

    std::shared_ptr<CEvent> waitEvent = pMsg->waitEvent;
    lock.unlock(); // <- see the large comment in SendMessage ^

    ProcessMessage(pMsg);
    if (waitEvent)
      waitEvent->Set();
    delete pMsg;

    lock.lock();
  }
}
void CApplicationMessenger::ProcessMessage(ThreadMessage *pMsg)
{
  //special case for this that we handle ourselves
  if (pMsg->dwMessage == TMSG_CALLBACK)
  {
    ThreadMessageCallback *callback = static_cast<ThreadMessageCallback*>(pMsg->lpVoid);
    callback->callback(callback->userptr);
    return;
  }

  std::unique_lock<CCriticalSection> lock(m_critSection);
  int mask = pMsg->dwMessage & TMSG_MASK_MESSAGE;

  const auto it = m_mapTargets.find(mask);
  if (it != m_mapTargets.end())
  {
    CSingleExit exit(m_critSection);
    it->second->OnApplicationMessage(pMsg);
  }
  else
    CLog::LogF(LOGERROR, "receiver {} is not defined", mask);
}
bool CApplicationMessenger::IsProcessThread() const
{
  return m_processThreadId == CThread::GetCurrentThreadId();
}
void CApplicationMessenger::ProcessCheckpointDisplayMessages()
{
  // Only Kodi's process thread may run these receivers. Playback controls
  // reach the unchanged OnAction rejection guard; ordinary messages/writes
  // remain closed, including after a failed checkpoint.
  if (!IsProcessThread() || !InfinityAndroidCheckpoint::IsActive())
    return;

  std::unique_lock<CCriticalSection> lock(m_critSection);
  // Bound one pass to the initially queued population. New lifecycle events
  // remain owned by the same queue and can run on a later application frame.
  std::size_t remaining = m_vecMessages.size();
  while (remaining > 0 && !m_bStop)
  {
    --remaining;
    ThreadMessage* selected = nullptr;
    std::queue<ThreadMessage*> retained;
    while (!m_vecMessages.empty())
    {
      ThreadMessage* message = m_vecMessages.front();
      m_vecMessages.pop();
      if (!selected && (message->dwMessage == TMSG_DISPLAY_SETUP ||
                        message->dwMessage == TMSG_DISPLAY_DESTROY ||
                        IsCheckpointPlaybackControl(*message)))
        selected = message;
      else
        retained.push(message);
    }
    m_vecMessages.swap(retained);
    if (!selected)
      return;

    // Retain the real receiver, payload lifetime and acknowledgment order.
    // Wake the sender only after the display handler or existing playback
    // rejection guard has returned. This grants no persistence receipt.
    const std::shared_ptr<CEvent> waitEvent = selected->waitEvent;
    lock.unlock();
    ProcessMessage(selected);
    if (waitEvent)
      waitEvent->Set();
    delete selected;
    lock.lock();
  }
}
void CXBMCApp::onResume()
{
  android_printf("%s: ", __PRETTY_FUNCTION__);

  if (g_application.IsInitialized() &&
      CServiceBroker::GetWinSystem()->GetOSScreenSaver()->IsInhibited())
    KeepScreenOn(true);

  // Reset shutdown timer on wake up
  if (g_application.IsInitialized() &&
      CServiceBroker::GetSettingsComponent()->GetSettings()->GetInt(
          CSettings::SETTING_POWERMANAGEMENT_SHUTDOWNTIME))
  {
    auto& components = CServiceBroker::GetAppComponents();
    const auto appPower = components.GetComponent<CApplicationPowerHandling>();
    appPower->ResetShutdownTimers();
  }

  const auto messenger = CServiceBroker::GetAppMessenger();
  if (messenger)
    messenger->PostMsg(TMSG_RESUMEAPP);

  m_headsetPlugged = isHeadsetPlugged();

  // Clear the applications cache. We could have installed/deinstalled apps
  {
    std::unique_lock<CCriticalSection> lock(m_applicationsMutex);
    m_applications.clear();
  }

  const auto& components = CServiceBroker::GetAppComponents();
  const auto appPlayer = components.GetComponent<CApplicationPlayer>();
  if (m_bResumePlayback && appPlayer->IsPlaying())
  {
    if (appPlayer->HasVideo())
    {
      if (appPlayer->IsPaused())
        CServiceBroker::GetAppMessenger()->SendMsg(
            TMSG_GUI_ACTION, WINDOW_INVALID, -1,
            static_cast<void*>(new CAction(ACTION_PLAYER_PLAY)));
    }
  }

  // Re-request Visible Behind
  if ((m_playback_state & PLAYBACK_STATE_PLAYING) && (m_playback_state & PLAYBACK_STATE_VIDEO))
    RequestVisibleBehind(true);
}
void CXBMCApp::onPause()
{
  android_printf("%s: ", __PRETTY_FUNCTION__);
  m_bResumePlayback = false;
  if (infinityIsPictureInPicture())
  {
    const auto messenger = CServiceBroker::GetAppMessenger();
    if (messenger)
      messenger->PostMsg(TMSG_SWITCHTOFULLSCREEN);
  }

  const auto& components = CServiceBroker::GetAppComponents();
  const auto appPlayer = components.GetComponent<CApplicationPlayer>();
  if (appPlayer->IsPlaying())
  {
    if (appPlayer->HasVideo())
    {
      if (!appPlayer->IsPaused() && !m_hasReqVisible && !infinityIsPictureInPicture())
      {
        CServiceBroker::GetAppMessenger()->SendMsg(TMSG_GUI_ACTION, WINDOW_INVALID, -1,
                                                   static_cast<void*>(new CAction(ACTION_PAUSE)));
        m_bResumePlayback = true;
      }
    }
  }

  if (m_hasReqVisible)
  {
    CGUIComponent* gui = CServiceBroker::GetGUI();
    if (gui)
    {
      gui->GetWindowManager().SwitchToFullScreen(true);
    }
  }

  KeepScreenOn(false);
  m_hasReqVisible = false;
}
void CXBMCApp::onStop()
{
  android_printf("%s: ", __PRETTY_FUNCTION__);

  if ((m_playback_state & PLAYBACK_STATE_PLAYING) && !m_hasReqVisible)
  {
    if (m_playback_state & PLAYBACK_STATE_CANNOT_PAUSE)
      CServiceBroker::GetAppMessenger()->SendMsg(TMSG_GUI_ACTION, WINDOW_INVALID, -1,
                                                 static_cast<void*>(new CAction(ACTION_STOP)));
    else if (m_playback_state & PLAYBACK_STATE_VIDEO)
      CServiceBroker::GetAppMessenger()->SendMsg(TMSG_GUI_ACTION, WINDOW_INVALID, -1,
                                                 static_cast<void*>(new CAction(ACTION_PAUSE)));
  }
}
void CXBMCApp::onAudioFocusChange(int focusChange)
{
  android_printf("Audio Focus changed: %d", focusChange);
  if (focusChange == CJNIAudioManager::AUDIOFOCUS_LOSS)
  {
    if ((m_playback_state & PLAYBACK_STATE_PLAYING))
    {
      if (m_playback_state & PLAYBACK_STATE_CANNOT_PAUSE)
        CServiceBroker::GetAppMessenger()->SendMsg(TMSG_GUI_ACTION, WINDOW_INVALID, -1,
                                                   static_cast<void*>(new CAction(ACTION_STOP)));
      else
        CServiceBroker::GetAppMessenger()->SendMsg(TMSG_GUI_ACTION, WINDOW_INVALID, -1,
                                                   static_cast<void*>(new CAction(ACTION_PAUSE)));
    }
  }
}
namespace InfinityAndroidCheckpoint {
bool AllowNativeWrite(const char*)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  return !s.active.load() || (!s.sealed && s.phase != "CHECKPOINT_FAILED") ||
    (permissionDepth != 0 && s.phase == "PERSISTING");
}
}
namespace InfinityAndroidCheckpoint {
CheckpointWriteGuard::CheckpointWriteGuard(const char* name)
{
  auto& s = Get();
  std::lock_guard<std::mutex> lock(s.mutex);
  const std::string owner = name ? name : "unknown";
  const bool newCommand = owner == "playback-command" || owner == "pvr-start" || owner == "optional-cache-work";
  const bool newJob = owner == "jobs" || owner == "directory-work" || newCommand;
  const bool acceptedStartup = s.startupInProgress && !s.writeAdmissionStarted &&
      !s.sealed && s.phase == "CHECKPOINT_REQUESTED" &&
      (owner == "jobs" || owner == "directory-work");
  m_admitted = acceptedStartup || !s.active.load() ||
    (!newJob && !s.sealed && s.phase != "CHECKPOINT_FAILED") ||
    (owner == "jobs" && acceptedPlaybackDepth != 0 && !s.sealed && s.phase == "QUIESCE") ||
    (!newCommand && permissionDepth != 0 && s.phase == "PERSISTING");
  if (m_admitted)
  {
    ++s.activeWrites;
    auto& tracked = s.owners[owner];
    ++tracked.generation;
    tracked.dirty = true;
    tracked.complete = false;
  }
}
}
namespace InfinityAndroidCheckpoint {
CheckpointWriteGuard::~CheckpointWriteGuard()
{
  if (m_admitted)
  {
    auto& s = Get();
    std::lock_guard<std::mutex> lock(s.mutex);
    --s.activeWrites;
  }
}
}
bool CApplication::OnAction(const CAction &action)
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive())
    return true;
#endif
  // Normal playback stands in for real player work in this HOST peer only.
  (void)action;
  ++playerCommands;
  InfinityAndroidCheckpoint::CheckpointWriteGuard guard("playback-command");
  assert(guard);return true;
}
void CApplication::Process()
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive())
  {
    // Android can synchronously await surface cleanup while a checkpoint is
    // draining or failed. Service only its real display messages, not general
    // queued actions/callbacks or legacy teardown.
    CServiceBroker::GetAppMessenger()->ProcessCheckpointDisplayMessages();
    InfinityAndroidCheckpoint::Pump(*this);
    return;
  }
#endif
  // Normal render/script/frame work is outside this host test.
  ++normalFrames;
  CServiceBroker::GetAppMessenger()->ProcessWindowMessages();
  CServiceBroker::GetAppMessenger()->ProcessMessages();
}
void CApplication::OnApplicationMessage(ThreadMessage* pMsg)
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive() &&
      pMsg->dwMessage != TMSG_DISPLAY_SETUP && pMsg->dwMessage != TMSG_DISPLAY_DESTROY)
    return; // Keep ordinary actions and legacy Stop/Cleanup outside the checkpoint.
#endif
  if(pMsg->dwMessage==TMSG_DISPLAY_SETUP||pMsg->dwMessage==TMSG_DISPLAY_DESTROY){
    displayBarrier.pause();displayObserved.push_back(pMsg->dwMessage);
    if(enqueueDisplayDuringHandler){enqueueDisplayDuringHandler=false;CServiceBroker::GetAppMessenger()->PostMsg(TMSG_DISPLAY_DESTROY);}
    pMsg->SetResult(42);
  }else otherObserved.push_back(pMsg->dwMessage);
}
void CGUIWindowManager::OnApplicationMessage(ThreadMessage* pMsg){
  if(pMsg->dwMessage==TMSG_GUI_ACTION){++guardReceivers;if(pMsg->lpVoid)controlObserved.push_back(static_cast<CAction*>(pMsg->lpVoid)->GetID());}
  switch(pMsg->dwMessage){
  case TMSG_GUI_ACTION:
  {
    if (pMsg->lpVoid)
    {
      CAction *action = static_cast<CAction *>(pMsg->lpVoid);
      if (pMsg->param1 == WINDOW_INVALID)
        g_application.OnAction(*action);
      else
      {
        CGUIWindow *pWindow = GetWindow(pMsg->param1);
        if (pWindow)
          pWindow->OnAction(*action);
        else
          CLog::Log(LOGWARNING, "Failed to get window with ID {} to send an action to",
                    pMsg->param1);
      }
      delete action;
    }
  }
  break;


  default:otherObserved.push_back(pMsg->dwMessage);break;
  }
}
// Harness-only assertions. Deadlines bound failed tests; no timeout enters the candidate.
void awaitWaiting(int n=1){
 std::unique_lock<std::mutex> l(waitingMutex);
 assert(waitingCv.wait_for(l,3s,[&]{return waiting.load()==n;}));
}
template<class T>T completed(std::future<T>& f){
 assert(f.wait_for(3s)==std::future_status::ready);return f.get();
}
std::future<int> control(CApplicationMessenger& m,int id){
 return std::async(std::launch::async,[&m,id]{
  return m.SendMsg(TMSG_GUI_ACTION,WINDOW_INVALID,-1,new CAction(id));
 });
}
std::future<int> display(CApplicationMessenger& m,uint32_t id){
 return std::async(std::launch::async,[&m,id]{return m.SendMsg(ThreadMessage(id),true);});
}
template<class F>void callback(CApplicationMessenger&,F fn){
 auto f=std::async(std::launch::async,[fn]{fn();return 0;});
 awaitWaiting();g_application.Process();assert(completed(f)==0);
}
std::string persistenceState(){
 auto& s=InfinityAndroidCheckpoint::Get();std::lock_guard<std::mutex> l(s.mutex);
 std::string result=s.phase+":"+std::to_string(s.active.load())+":"+std::to_string(s.sealed)+":"+
  std::to_string(s.activeWrites)+":"+std::to_string(s.failures)+":"+
  std::to_string(s.checkpointSaved)+":"+std::to_string(s.terminationAuthorized);
 for(const auto& entry:s.owners)result+="|"+entry.first+":"+std::to_string(entry.second.generation)+":"+
  std::to_string(entry.second.dirty)+":"+std::to_string(entry.second.complete);
 return result;
}
std::vector<ThreadMessage*> queued(std::queue<ThreadMessage*> q){
 std::vector<ThreadMessage*> result;while(!q.empty()){result.push_back(q.front());q.pop();}return result;
}
// Baseline/negative-case rescue only: native Cleanup signals waiters but does not own
// CAction payload disposal. Free these synthetic actions before Cleanup and disclose it.
// This rescue is never an after-candidate completion assertion.
void rescue(CApplicationMessenger& m){
 {std::lock_guard<CCriticalSection> l(m.m_critSection);
  for(auto* message:queued(m.m_vecMessages))
   if(message->dwMessage==TMSG_GUI_ACTION&&message->lpVoid){delete static_cast<CAction*>(message->lpVoid);message->lpVoid=nullptr;}
 }
 m.Cleanup();
}
void unrelated(void*){++otherCallbacks;}
int main(int argc,char**argv){
 assert(argc==3);const bool before=std::string(argv[1])=="before";const std::string test=argv[2];
 CApplicationMessenger m;CServiceBroker::messenger=&m;
 m.m_mapTargets[TMSG_MASK_APPLICATION]=&g_application;
 m.m_mapTargets[TMSG_MASK_WINDOWMANAGER]=&CServiceBroker::GetGUI()->GetWindowManager();
 auto& s=InfinityAndroidCheckpoint::Get();
 const auto originalState=persistenceState();
 bool compareOriginal=true;
 if(test=="pause-starvation"||test=="stop-starvation"||test=="resume-starvation"){
  const int id=test=="pause-starvation"?ACTION_PAUSE:(test=="stop-starvation"?ACTION_STOP:ACTION_PLAYER_PLAY);
  auto f=control(m,id);awaitWaiting();
  for(int i=0;i<4;++i)g_application.Process();
  if(before){
   assert(f.wait_for(0ms)==std::future_status::timeout);
   assert(waiting==1&&m.m_vecMessages.size()==1&&guardReceivers==0);
   assert(playerCommands==0&&checkpointPumps==4&&persistenceState()==originalState);
   std::cout<<"FAIL_BEFORE_WITNESS "<<test<<" still_waiting=1 checkpoint_frames=4 receiver_calls=0\n";
   rescue(m);assert(completed(f)==-1);
  }else{
   assert(completed(f)==-1&&guardReceivers==1&&playerCommands==0);
   assert(m.m_vecMessages.empty()&&liveActions==0&&checkpointPumps==4);
  }
 }else if(test=="audio-focus-pause-and-stop"){
  CXBMCApp app;
  callback(m,[&]{app.onAudioFocusChange(CJNIAudioManager::AUDIOFOCUS_LOSS);});
  app.m_playback_state|=PLAYBACK_STATE_CANNOT_PAUSE;
  callback(m,[&]{app.onAudioFocusChange(CJNIAudioManager::AUDIOFOCUS_LOSS);});
  app.onAudioFocusChange(1); // Native no-op for this unrelated focus value.
  assert((controlObserved==std::vector<int>{ACTION_PAUSE,ACTION_STOP}));
  assert(playerCommands==0&&liveActions==0);
 }else if(test=="android-pause-stop-resume"){
  CXBMCApp app;
  callback(m,[&]{app.onPause();});assert(app.m_bResumePlayback);
  app.m_playback_state|=PLAYBACK_STATE_CANNOT_PAUSE;
  callback(m,[&]{app.onStop();});
  CServiceBroker::GetAppComponents().player->paused=true;
  callback(m,[&]{app.onResume();});
  assert((controlObserved==std::vector<int>{ACTION_PAUSE,ACTION_STOP,ACTION_PLAYER_PLAY}));
  // onResume's ordinary async message remains closed, without blocking Android.
  assert(m.m_vecMessages.size()==1&&m.m_vecMessages.front()->dwMessage==TMSG_RESUMEAPP);
  assert(playerCommands==0&&otherObserved.empty());m.Cleanup();
 }else if(test=="failed-checkpoint-repeated-interruptions"){
  std::vector<std::future<int>> futures;
  for(int i=0;i<48;++i)futures.push_back(std::async(std::launch::async,[i]{
   CXBMCApp app;
   if(i%3==0)app.onPause();
   else if(i%3==1){app.m_playback_state|=PLAYBACK_STATE_CANNOT_PAUSE;app.onStop();}
   else app.onAudioFocusChange(CJNIAudioManager::AUDIOFOCUS_LOSS);
   return 0;
  }));
  awaitWaiting(48);g_application.Process();
  for(auto& f:futures)assert(completed(f)==0);
  assert(guardReceivers==48&&playerCommands==0&&liveActions==0&&m.m_vecMessages.empty());
 }else if(test=="ack-after-real-rejection-handler"){
  payloadBarrier.enabled=true;
  auto f=control(m,ACTION_STOP);awaitWaiting();
  std::thread observer([&]{
   payloadBarrier.reached();
   assert(f.wait_for(0ms)==std::future_status::timeout&&waiting==1);
   assert(guardReceivers==1&&playerCommands==0);
   payloadBarrier.release();
  });
  g_application.Process();observer.join();assert(completed(f)==-1&&liveActions==0);
 }else if(test=="display-ack-and-order"){
  displayBarrier.enabled=true;
  auto d=display(m,TMSG_DISPLAY_DESTROY);awaitWaiting();
  std::thread observer([&]{displayBarrier.reached();assert(d.wait_for(0ms)==std::future_status::timeout);displayBarrier.release();});
  g_application.Process();observer.join();assert(completed(d)==42);
  displayBarrier.enabled=false;
  m.PostMsg(TMSG_DISPLAY_SETUP);
  auto p=control(m,ACTION_PAUSE);awaitWaiting();
  m.PostMsg(TMSG_DISPLAY_DESTROY);m.PostMsg(TMSG_DISPLAY_SETUP);
  g_application.Process();assert(completed(p)==-1);
  assert((displayObserved==std::vector<uint32_t>{TMSG_DISPLAY_DESTROY,TMSG_DISPLAY_SETUP,TMSG_DISPLAY_DESTROY,TMSG_DISPLAY_SETUP}));
  assert(playerCommands==0);
 }else if(test=="unrelated-messages-and-FIFO"){
  std::vector<ThreadMessage*> retained;
  auto post=[&](ThreadMessage&& message){m.SendMsg(std::move(message),false);retained.push_back(m.m_vecMessages.back());};
  ThreadMessageCallback cb{unrelated,nullptr};
  post(ThreadMessage(TMSG_CALLBACK,-1,-1,&cb));
  post(ThreadMessage(TMSG_GUI_ACTION,WINDOW_INVALID-1,-1,new CAction(ACTION_PAUSE)));
  post(ThreadMessage(TMSG_GUI_ACTION,WINDOW_INVALID,0,new CAction(ACTION_STOP)));
  ThreadMessage extra(TMSG_GUI_ACTION,WINDOW_INVALID,-1,new CAction(ACTION_STOP));extra.param3=1;post(std::move(extra));
  post(ThreadMessage(TMSG_GUI_ACTION,WINDOW_INVALID,-1,nullptr));
  post(ThreadMessage(TMSG_GUI_ACTION,WINDOW_INVALID,-1,new CAction(ACTION_MOVE_LEFT)));
  auto safe=control(m,ACTION_STOP);awaitWaiting();m.PostMsg(TMSG_DISPLAY_DESTROY);
  ThreadMessage text(TMSG_GUI_ACTION,WINDOW_INVALID,-1,new CAction(ACTION_PAUSE));text.strParam="synthetic";post(std::move(text));
  ThreadMessage params(TMSG_GUI_ACTION,WINDOW_INVALID,-1,new CAction(ACTION_PLAYER_PLAY));params.params={"synthetic"};post(std::move(params));
  post(ThreadMessage(TMSG_SHUTDOWN));post(ThreadMessage(TMSG_QUIT));
  m.SendMsg(ThreadMessage(TMSG_GUI_MESSAGE),false);auto windows=queued(m.m_vecWindowMessages);
  g_application.Process();assert(completed(safe)==-1);
  assert(queued(m.m_vecMessages)==retained&&queued(m.m_vecWindowMessages)==windows);
  assert(guardReceivers==1&&windowActions==0&&playerCommands==0&&otherCallbacks==0&&otherObserved.empty());
  rescue(m);
 }else if(test=="wrong-thread"){
  auto f=control(m,ACTION_PAUSE);awaitWaiting();
  auto wrong=std::async(std::launch::async,[&]{m.ProcessCheckpointDisplayMessages();});wrong.get();
  assert(guardReceivers==0&&f.wait_for(0ms)==std::future_status::timeout);
  g_application.Process();assert(completed(f)==-1&&guardReceivers==1&&playerCommands==0);
 }else if(test=="noncheckpoint-normal"){
  compareOriginal=false;s.active=false;
  for(int id:{ACTION_PAUSE,ACTION_STOP,ACTION_PLAYER_PLAY}){
   auto f=control(m,id);awaitWaiting();m.ProcessCheckpointDisplayMessages();
   assert(f.wait_for(0ms)==std::future_status::timeout);
   g_application.Process();assert(completed(f)==-1);
  }
  // Same-thread native direct-dispatch path remains intact too.
  assert(m.SendMsg(TMSG_GUI_ACTION,WINDOW_INVALID,-1,new CAction(ACTION_PAUSE))==-1);
  assert(playerCommands==4&&guardReceivers==4&&normalFrames==3&&checkpointPumps==0);
 }else if(test=="bounded-reentrant-display"){
  enqueueDisplayDuringHandler=true;m.PostMsg(TMSG_DISPLAY_SETUP);g_application.Process();
  assert(displayObserved.size()==1&&m.m_vecMessages.size()==1&&checkpointPumps==1);
  g_application.Process();assert(displayObserved.size()==2&&m.m_vecMessages.empty()&&checkpointPumps==2);
 }else if(test=="checkpoint-transition-after-enqueue"){
  s.active=false;auto f=control(m,ACTION_STOP);awaitWaiting();s.active=true;
  g_application.Process();assert(completed(f)==-1&&guardReceivers==1&&playerCommands==0);
 }else if(test=="sealed-durability-and-shutdown-fences"){
  compareOriginal=false;
  for(const auto& phase:{"QUIESCE","PERSISTING","CHECKPOINT_FAILED","SAFE_TO_TERMINATE"}){
   for(bool sealed:{false,true}){
    s.phase=phase;s.sealed=sealed;const auto snapshot=persistenceState();
    for(int id:{ACTION_PAUSE,ACTION_STOP,ACTION_PLAYER_PLAY}){
     auto f=control(m,id);awaitWaiting();g_application.Process();assert(completed(f)==-1);
    }
    {InfinityAndroidCheckpoint::CheckpointWriteGuard blocked("playback-command");assert(!blocked);}
    assert(persistenceState()==snapshot&&playerCommands==0);
    if(s.phase=="CHECKPOINT_FAILED"){
     InfinityAndroidCheckpoint::permissionDepth=1; // Even a stale coordinator scope must not admit failed writes.
     {InfinityAndroidCheckpoint::CheckpointWriteGuard failed("pending-settings");assert(!failed);}
     assert(!InfinityAndroidCheckpoint::AllowNativeWrite("pending-settings"));
     InfinityAndroidCheckpoint::permissionDepth=0;assert(persistenceState()==snapshot);
    }
   }
  }
  s.phase="PERSISTING";s.sealed=true;InfinityAndroidCheckpoint::permissionDepth=1;
  {InfinityAndroidCheckpoint::CheckpointWriteGuard writer("pending-settings");assert(writer&&s.activeWrites==1);}
  assert(s.activeWrites==0&&s.owners.at("pending-settings").generation==8);
  assert(s.owners.at("pending-settings").dirty&&!s.owners.at("pending-settings").complete);
  assert(s.owners.at("unknown-watched-owner").generation==7&&s.owners.at("unknown-watched-owner").dirty);
  assert(!s.checkpointSaved&&!s.terminationAuthorized&&s.failures==1);
  {InfinityAndroidCheckpoint::CheckpointWriteGuard command("playback-command");assert(!command);}
  InfinityAndroidCheckpoint::permissionDepth=0;
 }else if(test=="stopped-queue-cleanup"){
  auto f=control(m,ACTION_STOP);awaitWaiting();m.Stop();g_application.Process();
  assert(f.wait_for(0ms)==std::future_status::timeout&&guardReceivers==0&&playerCommands==0);
  rescue(m);assert(completed(f)==-1);
  assert(m.SendMsg(ThreadMessage(TMSG_DISPLAY_SETUP),false)==-1&&m.m_vecMessages.empty());
 }else assert(false);
 if(compareOriginal)assert(persistenceState()==originalState);
 assert(m.m_vecMessages.empty()&&m.m_vecWindowMessages.empty());
 assert(liveMessages==0&&liveActions==0&&waiting==0);
 if(!before)std::cout<<"PASS "<<test<<" checkpoint_receiver_calls="<<guardReceivers<<" player_commands="<<playerCommands<<" (host peers; no Android acceptance)\n";
}
