/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
#include "guilib/GUIKeyboard.h"
#include <jni.h>
#include <atomic>
#include <memory>
#include <mutex>

struct InfinityKeyboardState;
class CAndroidKeyboard final : public CGUIKeyboard
{
public:
  explicit CAndroidKeyboard(CGUIKeyboard* owner, bool search) : m_owner(owner), m_search(search) {}
  bool ShowAndGetInput(char_callback_t callback, const std::string& initial, std::string& result,
                       const std::string& heading, bool hidden) override;
  void Cancel() override;
  bool SetTextToKeyboard(const std::string& text, bool closeKeyboard = false) override;
  static void RegisterNatives(JNIEnv* env);
  static bool UseAndroidIME();
private:
  static void Changed(JNIEnv*, jclass, jlong, jstring, jboolean, jboolean);
  std::shared_ptr<InfinityKeyboardState> State();
  std::mutex m_ownerMutex;
  std::atomic_bool m_cancelled{false};
  std::shared_ptr<InfinityKeyboardState> m_state;
  CGUIKeyboard* const m_owner;
  const bool m_search;
};
