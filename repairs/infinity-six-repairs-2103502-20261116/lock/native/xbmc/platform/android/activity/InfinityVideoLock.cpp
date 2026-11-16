#include "InfinityVideoLock.h"
#include "InfinityVideoLockGate.h"

#include "FileItem.h"
#include "ServiceBroker.h"
#include "application/Application.h"
#include "application/ApplicationPlayer.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIDialog.h"
#include "guilib/GUIWindowManager.h"
#include "guilib/WindowIDs.h"
#include "input/actions/Action.h"
#include "input/actions/ActionIDs.h"
#include "messaging/ApplicationMessenger.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "settings/Settings.h"
#include "settings/SettingsComponent.h"
#include "utils/StringUtils.h"
#include "utils/log.h"

#include <androidjni/Context.h>
#include <androidjni/jutils-details.hpp>
#include <algorithm>
#include <deque>
#include <memory>
#include <mutex>

namespace InfinityVideoLock
{
namespace
{
using namespace KODI::MESSAGING;
constexpr int LOCK_WINDOW = WINDOW_HOME + 1199;
constexpr const char* BRIDGE = "com.projectinfinity.kodi.InfinityVideoLockBridge";
enum Operation { READY = 1, REVOKE = 2, UNLOCK = 3, VALIDATE = 4, OWNER_GONE = 5,
                 ENTRY_FAILED = 6 };
struct Event
{
  std::uint32_t session;
  int operation;
  std::uint64_t epoch;
  std::uint64_t request;
};

Gate gate;
// All metadata below belongs exclusively to Kodi's process thread. JNI only
// reads/CASes gate, or adds bounded value events to the separate queue.
std::uint32_t sessionCounter{0};
std::uint32_t session{0};
std::weak_ptr<CFileItem> itemOwner;
std::uint64_t readyEpoch{0};
std::uint64_t pendingRequest{0};
bool ready{false};
bool everReady{false};
bool restoredOSD{false};
std::mutex queueMutex;
std::deque<Event> queue;
std::weak_ptr<CApplicationMessenger> messengerOwner;
std::uint32_t pendingOwnerGoneToken{0}; // Protected by queueMutex, including the retirement CAS.

std::shared_ptr<CApplicationMessenger> CapturedMessenger()
{
  std::lock_guard<std::mutex> lock(queueMutex);
  return messengerOwner.lock();
}

bool ProcessThread()
{
  const auto messenger = CapturedMessenger();
  return messenger && messenger->IsProcessThread();
}

bool ConsumeOwnerGone(std::uint32_t token)
{
  std::lock_guard<std::mutex> lock(queueMutex);
  if (!token || pendingOwnerGoneToken != token) return false;
  pendingOwnerGoneToken = 0;
  return true;
}

void CloseOwnedWindow(int id);

bool InfinitySkin()
{
  const auto settings = CServiceBroker::GetSettingsComponent();
  return settings && settings->GetSettings() &&
         settings->GetSettings()->GetString("lookandfeel.skin") == "skin.infinity.diggz";
}

void ClearMetadata()
{
  session = 0;
  itemOwner.reset();
  readyEpoch = pendingRequest = 0;
  ready = everReady = restoredOSD = false;
}

bool Active()
{
  if (!session || Gate::Session(gate.Value()) != session)
  {
    if (ConsumeOwnerGone(session))
    {
      CloseOwnedWindow(LOCK_WINDOW);
      if (restoredOSD) CloseOwnedWindow(WINDOW_DIALOG_VIDEO_OSD);
    }
    // A successful atomic Java commit already restored OSD; do not hide it.
    ClearMetadata();
    return false;
  }
  return true;
}

int Theme()
{
  const auto gui = CServiceBroker::GetGUI();
  const auto home = gui ? gui->GetWindowManager().GetWindow(WINDOW_HOME) : nullptr;
  if (!home) return -1;
  const auto value = home->GetProperty("Infinity.Theme").asString();
  return value == "light" ? 1 : value == "dark" ? 0 : -1;
}

template<typename... Args>
bool Java(const char* method, const char* signature, Args... args)
{
  using namespace jni;
  JNIEnv* env = xbmc_jnienv();
  if (!env) return false;
  try
  {
    auto clazz = CJNIContext::getClassLoader().loadClass(BRIDGE);
    if (env->ExceptionCheck()) { env->ExceptionClear(); return false; }
    call_static_method<void>(env, clazz, method, signature, args...);
    if (env->ExceptionCheck()) { env->ExceptionClear(); return false; }
    return true;
  }
  catch (...) { if (env->ExceptionCheck()) env->ExceptionClear(); return false; }
}

void CloseOwnedWindow(int id)
{
  const auto gui = CServiceBroker::GetGUI();
  if (!gui) return;
  if (auto window = gui->GetWindowManager().GetWindow(id))
    if (window->IsDialogRunning()) window->Close(true, 0, false, false);
}

bool ShowOSD()
{
  const auto gui = CServiceBroker::GetGUI();
  if (!gui) return false;
  auto dialog = gui->GetWindowManager().GetWindow<CGUIDialog>(WINDOW_DIALOG_VIDEO_OSD);
  if (!dialog) return false;
  dialog->Open(false); // No nested render loop and no Activity transition.
  return dialog->IsDialogRunning();
}

void Retire(bool notifyJava)
{
  const auto previous = session;
  gate.Retire(previous);
  ConsumeOwnerGone(previous);
  CloseOwnedWindow(LOCK_WINDOW);
  // Only hide an OSD opened by a canceled unlock, never an unrelated player UI.
  if (restoredOSD) CloseOwnedWindow(WINDOW_DIALOG_VIDEO_OSD);
  ClearMetadata();
  if (notifyJava && previous)
    Java("retired", "(J)V", static_cast<jlong>(previous));
}

enum class Context { CURRENT, UNKNOWN, RETIRED };
Context Current()
{
  if (!Active()) return Context::RETIRED;
  if (!InfinitySkin()) { Retire(true); return Context::RETIRED; }
  auto current = g_application.CurrentFileItemPtr();
  const bool sameOwner = current && !itemOwner.expired() &&
                        !itemOwner.owner_before(current) && !current.owner_before(itemOwner);
  // Exact502 assigns a fresh shared_ptr on every PLAYBACK_STARTED; ResetCurrentItem
  // clears the old item's path on confirmed stop. This includes same-title replay.
  if (!sameOwner || current->GetPath().empty())
  {
    Retire(true);
    return Context::RETIRED;
  }
  if (g_application.IsStopping() || InfinityAndroidCheckpoint::IsActive() ||
      !CServiceBroker::GetGUI()) return Context::UNKNOWN;
  const auto player = g_application.GetComponent<CApplicationPlayer>();
  return player && player->IsPlayingVideo() ? Context::CURRENT : Context::UNKNOWN;
}

void Handle(const Event& event)
{
  if (!ProcessThread() || !session || session != event.session) return;
  if (event.operation == OWNER_GONE) { Retire(false); return; }
  if (!Active()) return;
  const auto context = Current();
  if (context == Context::RETIRED) return;
  if (event.operation == VALIDATE)
  {
    Java("validated", "(JI)V", static_cast<jlong>(session), static_cast<jint>(Theme()));
    return;
  }
  if (event.operation == ENTRY_FAILED && !everReady)
  {
    // This is a failed lock activation, never a timeout exemption for an established lock.
    const auto failedSession = session;
    Retire(false);
    if (context == Context::CURRENT) ShowOSD();
    Java("retired", "(J)V", static_cast<jlong>(failedSession));
    CLog::Log(LOGWARNING, "Infinity video lock: Android input window unavailable; lock not activated");
    return;
  }
  if (event.operation == REVOKE)
  {
    if (event.epoch != readyEpoch) return;
    gate.Advance(session, false);
    ready = false;
    pendingRequest = 0;
    if (restoredOSD) CloseOwnedWindow(WINDOW_DIALOG_VIDEO_OSD);
    restoredOSD = false;
    return;
  }
  if (event.operation == READY)
  {
    if (!event.epoch || event.epoch <= readyEpoch || context != Context::CURRENT) return;
    if (!gate.Advance(session, false)) return;
    readyEpoch = event.epoch;
    ready = everReady = true;
    pendingRequest = 0;
    if (restoredOSD) CloseOwnedWindow(WINDOW_DIALOG_VIDEO_OSD);
    restoredOSD = false;
    CloseOwnedWindow(LOCK_WINDOW); // Only after Java's focused input window owns touches.
    return;
  }
  if (event.operation != UNLOCK) return;
  // A stale/duplicate request must not clear another request's ownership or grant.
  if (pendingRequest && event.epoch == readyEpoch && event.request == pendingRequest) return;
  if (!ready || event.epoch != readyEpoch || !event.request || pendingRequest ||
      context != Context::CURRENT)
  {
    Java("restored", "(JJJJ)V", static_cast<jlong>(session),
         static_cast<jlong>(event.epoch), static_cast<jlong>(event.request), jlong{0});
    return;
  }
  Gate::Word grant = 0;
  if (gate.Advance(session, false))
  {
    pendingRequest = event.request;
    restoredOSD = ShowOSD();
    if (restoredOSD) grant = gate.Advance(session, true);
  }
  if (!grant) pendingRequest = 0;
  if (!Java("restored", "(JJJJ)V", static_cast<jlong>(session),
            static_cast<jlong>(event.epoch), static_cast<jlong>(event.request),
            static_cast<jlong>(grant)))
  {
    gate.Advance(session, false);
    pendingRequest = 0;
    if (restoredOSD) CloseOwnedWindow(WINDOW_DIALOG_VIDEO_OSD);
    restoredOSD = false;
  }
}

void Drain(void*)
{
  std::deque<Event> events;
  {
    std::lock_guard<std::mutex> lock(queueMutex);
    events.swap(queue);
  }
  for (const auto& event : events) Handle(event);
}

// Exact502 TMSG_CALLBACK borrows this object and never deletes it. Queue events
// own only integers; no per-message payload allocation can leak during Cleanup.
ThreadMessageCallback callback{Drain, nullptr};

bool Enqueue(const Event& event)
{
  if (Gate::Session(gate.Value()) != event.session || !event.session ||
      event.operation < READY || event.operation > ENTRY_FAILED ||
      event.operation == OWNER_GONE) return false;
  std::shared_ptr<CApplicationMessenger> messenger;
  {
    std::lock_guard<std::mutex> lock(queueMutex);
    messenger = messengerOwner.lock();
    if (!messenger || Gate::Session(gate.Value()) != event.session) return false;
    if (event.operation == VALIDATE)
    {
      const auto duplicate = std::find_if(queue.begin(), queue.end(), [&](const Event& e) {
        return e.session == event.session && e.operation == VALIDATE;
      });
      if (duplicate != queue.end()) queue.erase(duplicate);
    }
    if (queue.size() >= 32) return false; // Explicit refusal retains the input barrier.
    queue.push_back(event);
  }
  // PostMsg is void: this means queued locally, not executed successfully.
  // Repost on each accepted event so a dropped callback never latches a scheduled flag.
  messenger->PostMsg(TMSG_CALLBACK, 0, 0, &callback);
  return true;
}

jboolean JNICALL Transition(JNIEnv*, jclass, jlong token, jint operation, jlong epoch, jlong request)
{
  if (token <= 0 || token > Gate::MAX_SESSION || epoch < 0 || request < 0) return JNI_FALSE;
  return Enqueue({static_cast<std::uint32_t>(token), operation,
                  static_cast<std::uint64_t>(epoch), static_cast<std::uint64_t>(request)})
             ? JNI_TRUE : JNI_FALSE;
}

jboolean JNICALL Commit(JNIEnv*, jclass, jlong token, jlong grant)
{
  if (token <= 0 || token > Gate::MAX_SESSION) return JNI_FALSE;
  return gate.Commit(static_cast<std::uint32_t>(token), static_cast<Gate::Word>(grant))
             ? JNI_TRUE : JNI_FALSE;
}

jboolean JNICALL OwnerGone(JNIEnv*, jclass, jlong token)
{
  if (token <= 0 || token > Gate::MAX_SESSION) return JNI_FALSE;
  std::shared_ptr<CApplicationMessenger> messenger;
  {
    std::lock_guard<std::mutex> lock(queueMutex);
    // Publish the reason while serialized with Active's zero-gate observation.
    // If COMMIT won instead, do not misclassify its restored OSD as abandoned.
    if (!gate.Retire(static_cast<std::uint32_t>(token))) return JNI_FALSE;
    pendingOwnerGoneToken = static_cast<std::uint32_t>(token);
    queue.clear(); // All queued values belong to this now-retired lock or older tokens.
    queue.push_back({static_cast<std::uint32_t>(token), OWNER_GONE, 0, 0});
    messenger = messengerOwner.lock();
  }
  if (messenger) messenger->PostMsg(TMSG_CALLBACK, 0, 0, &callback);
  // Input retirement does not depend on a message being dispatched during teardown.
  return JNI_TRUE;
}

bool Register()
{
  using namespace jni;
  JNIEnv* env = xbmc_jnienv();
  if (!env) return false;
  try
  {
    auto clazz = CJNIContext::getClassLoader().loadClass(BRIDGE);
    if (env->ExceptionCheck()) { env->ExceptionClear(); return false; }
    JNINativeMethod methods[] = {
        {const_cast<char*>("nativeTransition"), const_cast<char*>("(JIJJ)Z"), reinterpret_cast<void*>(Transition)},
        {const_cast<char*>("nativeCommit"), const_cast<char*>("(JJ)Z"), reinterpret_cast<void*>(Commit)},
        {const_cast<char*>("nativeOwnerGone"), const_cast<char*>("(J)Z"), reinterpret_cast<void*>(OwnerGone)}};
    const bool ok = env->RegisterNatives(clazz.get(), methods, 3) == JNI_OK;
    if (env->ExceptionCheck()) { env->ExceptionClear(); return false; }
    return ok;
  }
  catch (...) { if (env->ExceptionCheck()) env->ExceptionClear(); return false; }
}
} // namespace

int Open(const std::vector<std::string>& params)
{
  // Only this process-thread entry reads the broker's current messenger. JNI uses
  // the captured weak owner and never races the broker's global shared_ptr teardown.
  const auto currentMessenger = CServiceBroker::GetAppMessenger();
  if (!currentMessenger || !currentMessenger->IsProcessThread()) return 1;
  {
    std::lock_guard<std::mutex> lock(queueMutex);
    const auto previous = messengerOwner.lock();
    if (previous && previous != currentMessenger) return 1;
    if (!previous && session)
    {
      // The prior engine owner is gone. Do not act on same-numbered windows in
      // this new GUI lifetime while retiring its private stale metadata.
      gate.Retire(session);
      ClearMetadata();
      pendingOwnerGoneToken = 0;
      queue.clear();
    }
    messengerOwner = currentMessenger;
  }
  const auto fail = [&]() {
    if (currentMessenger->IsProcessThread() && !gate.Value())
    {
      CloseOwnedWindow(LOCK_WINDOW);
      const auto player = g_application.GetComponent<CApplicationPlayer>();
      if (player && player->IsPlayingVideo() && !g_application.IsStopping() &&
          !InfinityAndroidCheckpoint::IsActive()) ShowOSD();
    }
    CLog::Log(LOGWARNING, "Infinity video lock: activation refused; no unlock was authorized");
    return 1;
  };
  if (!params.empty() || !ProcessThread() || g_application.IsStopping() ||
      InfinityAndroidCheckpoint::IsActive() || !InfinitySkin()) return fail();
  const auto player = g_application.GetComponent<CApplicationPlayer>();
  const auto item = g_application.CurrentFileItemPtr();
  if (!player || !player->IsPlayingVideo() || !item || item->GetPath().empty()) return fail();
  if (Active())
  {
    const auto context = Current();
    if (context == Context::CURRENT)
      return Java("open", "(JI)V", static_cast<jlong>(session), static_cast<jint>(Theme())) ? 0 : 1;
    if (context == Context::UNKNOWN) return fail();
  }
  if (sessionCounter == Gate::MAX_SESSION || !Register()) return fail();
  const auto next = ++sessionCounter;
  if (!gate.Begin(next)) return 1;
  session = next;
  itemOwner = item;
  if (!Java("open", "(JI)V", static_cast<jlong>(session), static_cast<jint>(Theme())))
  {
    Retire(false);
    ShowOSD();
    return 1;
  }
  return 0;
}

bool BlocksAction(const CAction& action)
{
  const auto token = Gate::Session(gate.Value());
  if (!token) return false;
  const auto owner = CapturedMessenger();
  if (!owner)
  {
    // A destroyed execution owner is positive lifetime evidence. Its old lock
    // cannot block input in a later engine; do not touch the new GUI's windows.
    if (gate.Retire(token)) Java("retired", "(J)V", static_cast<jlong>(token));
    return false;
  }
  if (owner->IsProcessThread())
  {
    if (Current() == Context::RETIRED) return false;
  }
  else Enqueue({token, VALIDATE, 0, 0});
  switch (action.GetID())
  {
    case ACTION_NONE:
    case ACTION_NOOP:
    case ACTION_VOLUME_UP:
    case ACTION_VOLUME_DOWN:
    case ACTION_VOLUME_SET:
    case ACTION_MUTE:
      return false;
    case ACTION_BUILT_IN_FUNCTION:
      // Preserve explicit power/exit commands and their existing save protections.
      // Arbitrary keymap built-ins (seek, window activation, PlayerControl) remain blocked.
      for (const char* command : {"Quit", "Shutdown", "Powerdown", "RestartApp", "Reboot", "Suspend", "Hibernate"})
        if (StringUtils::EqualsNoCase(action.GetName(), command) ||
            StringUtils::EqualsNoCase(action.GetName(), std::string(command) + "()")) return false;
      return true;
    default:
      return true;
  }
}
} // namespace InfinityVideoLock
