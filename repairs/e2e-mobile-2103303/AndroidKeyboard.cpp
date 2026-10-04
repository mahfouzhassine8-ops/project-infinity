/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "AndroidKeyboard.h"
#include "CompileInfo.h"
#include "utils/CharsetConverter.h"
#include <androidjni/jutils-details.hpp>
#include <atomic>
#include <condition_variable>
#include <unordered_map>

using namespace jni;

struct InfinityKeyboardState
{
  std::mutex mutex;
  std::condition_variable ready;
  uint64_t token{0}, revision{0};
  bool finished{false}, accepted{false};
  std::string text;
};

namespace
{
jclass keyboardClass{nullptr};
jmethodID openMethod{nullptr}, closeMethod{nullptr}, replaceMethod{nullptr}, mobileMethod{nullptr};
std::atomic<uint64_t> nextToken{1};
std::mutex registryMutex;
std::unordered_map<uint64_t, std::weak_ptr<InfinityKeyboardState>> editors;
thread_local int inputKind = 0;

jstring ToJava(JNIEnv* env, const std::string& text)
{
  std::u16string value;
  CCharsetConverter::utf8To("UTF-16LE", text, value);
  return env->NewString(reinterpret_cast<const jchar*>(value.data()), value.size());
}
bool JavaFailed(JNIEnv* env)
{
  if (!env->ExceptionCheck()) return false;
  // The UI reports cancellation. Never log text, credentials or exception messages.
  env->ExceptionClear();
  return true;
}
void CloseJava(uint64_t token)
{
  if (!keyboardClass || !closeMethod) return;
  JNIEnv* env = xbmc_jnienv();
  env->CallStaticVoidMethod(keyboardClass, closeMethod, static_cast<jlong>(token));
  JavaFailed(env);
}
}

int CAndroidKeyboard::InputKind() { return inputKind; }
CAndroidKeyboard::InputScope::InputScope(int kind) : previous(inputKind) { inputKind=kind; }
CAndroidKeyboard::InputScope::~InputScope() { inputKind=previous; }

void CAndroidKeyboard::RegisterNatives(JNIEnv* env)
{
  const std::string name = std::string(CCompileInfo::GetClass()) + "/InfinityAndroidKeyboard";
  jclass local = env->FindClass(name.c_str());
  if (JavaFailed(env) || !local) return;
  keyboardClass = static_cast<jclass>(env->NewGlobalRef(local));
  JNINativeMethod methods[] = {{"changed", "(JLjava/lang/String;ZZ)V", reinterpret_cast<void*>(&Changed)}};
  env->RegisterNatives(local, methods, 1);
  openMethod = env->GetStaticMethodID(local,"open","(JLjava/lang/String;Ljava/lang/String;ZZI)V");
  closeMethod = env->GetStaticMethodID(local,"close","(J)V");
  replaceMethod = env->GetStaticMethodID(local,"replace","(JLjava/lang/String;Z)V");
  mobileMethod = env->GetStaticMethodID(local,"isMobile","()Z");
  env->DeleteLocalRef(local);
}

bool CAndroidKeyboard::UseAndroidIME()
{
  // Failure must not expose the Kodi keyboard on a phone.
  if (!keyboardClass || !mobileMethod) return true;
  JNIEnv* env = xbmc_jnienv();
  jboolean mobile = env->CallStaticBooleanMethod(keyboardClass,mobileMethod);
  return JavaFailed(env) || mobile == JNI_TRUE;
}

std::shared_ptr<InfinityKeyboardState> CAndroidKeyboard::State()
{
  std::lock_guard<std::mutex> lock(m_ownerMutex);
  return m_state;
}

void CAndroidKeyboard::Changed(JNIEnv* env,jclass,jlong token,jstring text,jboolean finished,jboolean accepted)
{
  std::shared_ptr<InfinityKeyboardState> state;
  {
    std::lock_guard<std::mutex> lock(registryMutex);
    auto found = editors.find(token);
    if (found == editors.end() || !(state = found->second.lock())) return;
  }
  std::string value;
  if (text)
  {
    const jchar* chars = env->GetStringChars(text,nullptr);
    if (!chars) return;
    const std::u16string utf16(reinterpret_cast<const char16_t*>(chars),env->GetStringLength(text));
    env->ReleaseStringChars(text,chars);
    CCharsetConverter::utf16LEtoUTF8(utf16,value);
  }
  {
    std::lock_guard<std::mutex> lock(state->mutex);
    if (state->finished) return;
    state->text = std::move(value);
    ++state->revision;
    state->finished = finished == JNI_TRUE;
    state->accepted = accepted == JNI_TRUE;
  }
  state->ready.notify_one();
}

bool CAndroidKeyboard::ShowAndGetInput(char_callback_t callback,const std::string& initial,
    std::string& result,const std::string& heading,bool hidden)
{
  if (!keyboardClass || !openMethod) return false;
  auto state = std::make_shared<InfinityKeyboardState>();
  state->token = nextToken.fetch_add(1); state->text = initial;
  { std::lock_guard<std::mutex> lock(m_ownerMutex); m_state = state; }
  { std::lock_guard<std::mutex> lock(registryMutex); editors[state->token] = state; }
  if (m_cancelled.load()) Cancel();
  JNIEnv* env = xbmc_jnienv();
  jstring text = ToJava(env,initial), title = ToJava(env,heading);
  if (text && title && !env->ExceptionCheck())
    env->CallStaticVoidMethod(keyboardClass,openMethod,static_cast<jlong>(state->token),text,title,
                             static_cast<jboolean>(hidden),static_cast<jboolean>(m_search),m_kind);
  const bool failed = JavaFailed(env) || !text || !title;
  if (text) env->DeleteLocalRef(text);
  if (title) env->DeleteLocalRef(title);
  if (failed) Cancel();
  uint64_t seen = 0;
  bool confirmed = false;
  while (true)
  {
    std::unique_lock<std::mutex> lock(state->mutex);
    state->ready.wait(lock,[&]{return state->finished || state->revision != seen;});
    const bool changed = state->revision != seen;
    seen = state->revision;
    const std::string current = state->text;
    const bool done = state->finished;
    confirmed = state->accepted;
    lock.unlock();
    // Never call into Kodi's window manager from Android's IME/main thread.
    if (changed && callback) callback(m_owner,current);
    if (done) { if (confirmed) result=current; break; }
  }
  { std::lock_guard<std::mutex> lock(registryMutex); editors.erase(state->token); }
  CloseJava(state->token);
  { std::lock_guard<std::mutex> lock(m_ownerMutex); m_state.reset(); }
  return confirmed;
}

void CAndroidKeyboard::Cancel()
{
  m_cancelled.store(true);
  auto state=State(); if(!state)return;
  { std::lock_guard<std::mutex> lock(state->mutex); state->finished=true;state->accepted=false; }
  state->ready.notify_one();
  CloseJava(state->token);
}

bool CAndroidKeyboard::SetTextToKeyboard(const std::string& text,bool confirm)
{
  auto state=State();if(!state || !keyboardClass || !replaceMethod)return false;
  JNIEnv* env=xbmc_jnienv();jstring value=ToJava(env,text);
  if(value)env->CallStaticVoidMethod(keyboardClass,replaceMethod,static_cast<jlong>(state->token),
                                    value,static_cast<jboolean>(confirm));
  bool success=!JavaFailed(env) && value;
  if(value)env->DeleteLocalRef(value);
  return success;
}
