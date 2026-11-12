/* SPDX-License-Identifier: GPL-2.0-or-later */
// Cast-only conditional handoff. No observer, persistence owner, startup hook,
// shutdown hook, player replacement, or call from the ordinary playback path.
#include "FileItem.h"
#include "ServiceBroker.h"
#include "application/Application.h"
#include "application/ApplicationComponents.h"
#include "application/ApplicationPlayer.h"
#include "messaging/ApplicationMessenger.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "settings/Settings.h"
#include "settings/SettingsComponent.h"
#include "utils/Digest.h"
#include "utils/JSONVariantWriter.h"
#include "utils/Variant.h"
#include "video/VideoInfoTag.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <jni.h>
#include <unistd.h>

namespace
{
using KODI::UTILITY::CDigest;
using Clock = std::chrono::steady_clock;
constexpr size_t Capacity = 8;
constexpr auto QueueDeadline = std::chrono::seconds(3);
enum class Phase { Free, Queued, Running, Done };

struct Slot
{
  MESSAGING::ThreadMessageCallback callback{};
  uint64_t id{0};
  Phase phase{Phase::Free};
  bool cancelled{false};
  bool consumed{false};
  std::string operation;
  std::string token;
  int64_t position{0};
  Clock::time_point deadline{};
  std::string result;
};

struct State
{
  std::mutex mutex;
  uint64_t sequence{0};
  std::array<Slot, Capacity> slots;
  std::string token;
  std::weak_ptr<CFileItem> item;
  std::string file;
  std::string origin;
  Clock::time_point lease{};
};

State& Store()
{
  // Construct only when Cast is explicitly invoked, never during startup.
  static State state;
  return state;
}

bool Token(const std::string& value)
{
  return value.size() == 32 && std::all_of(value.begin(), value.end(), [](char c) {
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
  });
}

std::string Hash(const std::string& value)
{
  return CDigest::Calculate(CDigest::Type::SHA256, value);
}

CVariant Error(const char* reason)
{
  CVariant value(CVariant::VariantTypeObject);
  value["status"] = "error";
  value["reason"] = reason;
  return value;
}

bool Cancelled(Slot& slot)
{
  auto& state = Store();
  std::lock_guard<std::mutex> lock(state.mutex);
  return slot.cancelled || Clock::now() > slot.deadline;
}

CVariant Snapshot(const std::shared_ptr<CFileItem>& item,
                  const std::shared_ptr<CApplicationPlayer>& player,
                  const std::string& token)
{
  CVariant result(CVariant::VariantTypeObject);
  result["status"] = "ok";
  result["schema"] = 1;
  result["token"] = token;
  result["pid"] = static_cast<int>(getpid());
  result["file"] = item->GetDynPath();
  result["file_sha256"] = Hash(item->GetDynPath());
  result["origin_sha256"] = Hash(item->GetProperty("Infinity.Resume.OriginalProvider").asString());
  result["position_ms"] = player->GetTime();
  result["duration_ms"] = player->GetTotalTime();
  result["paused"] = player->IsPaused();
  result["can_pause"] = player->CanPause();
  result["can_seek"] = player->CanSeek();
  result["title"] = item->GetLabel();
  if (item->HasVideoInfoTag())
  {
    const auto* tag = item->GetVideoInfoTag();
    result["kind"] = tag->m_type;
    if (!tag->m_strTitle.empty()) result["title"] = tag->m_strTitle;
    result["season"] = tag->m_iSeason;
    result["episode"] = tag->m_iEpisode;
  }
  return result;
}

CVariant Execute(Slot& slot, const std::string& op, const std::string& token, int64_t position)
{
  // Read the existing admission state; never modify shutdown or reopen a gate.
  if (g_application.IsStopping() || InfinityAndroidCheckpoint::IsActive())
    return Error("closing");
  if (CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") !=
      "skin.infinity.diggz")
    return Error("not_infinity");
  auto player = g_application.GetComponent<CApplicationPlayer>();
  auto current = g_application.CurrentFileItemPtr();
  if (!player || !current || !player->IsPlayingVideo()) return Error("no_video");
  if (current->GetDynPath().size() > 65536) return Error("unsupported_source");

  auto& state = Store();
  if (op == "capture")
  {
    CVariant result = Snapshot(current, player, token);
    if (Cancelled(slot)) return Error("cancelled");
    std::lock_guard<std::mutex> lock(state.mutex);
    if (slot.cancelled || Clock::now() > slot.deadline) return Error("cancelled");
    state.token = token;
    state.item = current;
    state.file = current->GetDynPath();
    state.origin = current->GetProperty("Infinity.Resume.OriginalProvider").asString();
    state.lease = Clock::now() + std::chrono::seconds(60);
    return result;
  }

  std::weak_ptr<CFileItem> bound;
  std::string file, origin;
  {
    std::lock_guard<std::mutex> lock(state.mutex);
    if (state.token != token || Clock::now() > state.lease) return Error("stale_session");
    bound = state.item;
    file = state.file;
    origin = state.origin;
  }
  // GUI playback-start replaces CurrentFileItemPtr, including replay of the
  // same URI. Do not apply an old Cast command to a new playing item.
  if (bound.lock() != current || current->GetDynPath() != file ||
      current->GetProperty("Infinity.Resume.OriginalProvider").asString() != origin)
    return Error("source_changed");
  if (Cancelled(slot)) return Error("cancelled");

  if (op == "pause")
  {
    if (!player->CanPause()) return Error("not_pausable");
    if (!player->IsPaused()) player->Pause();
  }
  else if (op == "resume")
  {
    if (player->IsPaused()) player->Pause();
  }
  else if (op == "seek")
  {
    if (!player->CanSeek() || position < 0 || player->GetTotalTime() <= 0 ||
        position > player->GetTotalTime()) return Error("not_seekable");
    player->SeekTime(position);
  }
  else if (op != "snapshot" && op != "release") return Error("unknown_operation");

  CVariant result = Snapshot(current, player, token);
  {
    std::lock_guard<std::mutex> lock(state.mutex);
    if (state.token == token)
    {
      state.lease = Clock::now() + std::chrono::seconds(60);
      if (op == "release")
      {
        state.token.clear();
        state.item.reset();
        state.file.clear();
        state.origin.clear();
      }
    }
  }
  return result;
}

void Run(void* pointer)
{
  auto& slot = *static_cast<Slot*>(pointer);
  auto& state = Store();
  std::string operation, token;
  int64_t position;
  {
    std::lock_guard<std::mutex> lock(state.mutex);
    if (slot.phase != Phase::Queued) return;
    slot.phase = Phase::Running;
    operation = slot.operation;
    token = slot.token;
    position = slot.position;
  }
  CVariant result;
  try
  {
    result = Cancelled(slot) ? Error("cancelled") : Execute(slot, operation, token, position);
  }
  catch (...)
  {
    result = Error("native_operation_failed");
  }
  const std::string encoded = CJSONVariantWriter::Write(result, false);
  std::lock_guard<std::mutex> lock(state.mutex);
  slot.result = encoded;
  slot.phase = slot.consumed ? Phase::Free : Phase::Done;
}

std::string ASCII(JNIEnv* env, jstring value, size_t limit)
{
  if (!value || env->GetStringUTFLength(value) > static_cast<jsize>(limit)) return {};
  const char* raw = env->GetStringUTFChars(value, nullptr);
  if (!raw) return {};
  std::string result(raw);
  env->ReleaseStringUTFChars(value, raw);
  if (!std::all_of(result.begin(), result.end(), [](unsigned char c) { return c < 128; })) return {};
  return result;
}
} // namespace

extern "C" JNIEXPORT jlong JNICALL
Java_com_projectinfinity_kodi_InfinityCastNative_request(JNIEnv* env, jclass, jstring operation,
                                                        jstring token, jlong position)
{
  const auto op = ASCII(env, operation, 16);
  const auto key = ASCII(env, token, 32);
  if (!Token(key) || (op != "capture" && op != "snapshot" && op != "pause" &&
      op != "resume" && op != "seek" && op != "release") || position < 0) return 0;
  auto messenger = CServiceBroker::GetAppMessenger();
  if (!messenger || g_application.IsStopping()) return 0;
  auto& state = Store();
  Slot* selected = nullptr;
  uint64_t id = 0;
  {
    std::lock_guard<std::mutex> lock(state.mutex);
    for (auto& slot : state.slots)
    {
      if (slot.phase == Phase::Done && Clock::now() > slot.deadline + std::chrono::seconds(10))
        slot.phase = Phase::Free;
      if (slot.phase != Phase::Free) continue;
      slot.id = id = ++state.sequence;
      slot.operation = op;
      slot.token = key;
      slot.position = position;
      slot.cancelled = slot.consumed = false;
      slot.result.clear();
      slot.deadline = Clock::now() + QueueDeadline;
      slot.callback = {Run, &slot};
      slot.phase = Phase::Queued;
      selected = &slot;
      break;
    }
  }
  // Stable, bounded slot storage owns the callback: no per-request detached
  // thread/heap callback and no slot reuse while a queued callback can run.
  if (selected) messenger->PostMsg(TMSG_CALLBACK, 0, 0, &selected->callback);
  return static_cast<jlong>(id);
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_projectinfinity_kodi_InfinityCastNative_poll(JNIEnv* env, jclass, jlong id)
{
  auto& state = Store();
  std::string data;
  {
    std::lock_guard<std::mutex> lock(state.mutex);
    for (auto& slot : state.slots)
    {
      if (slot.id != static_cast<uint64_t>(id) || slot.phase == Phase::Free) continue;
      if (slot.phase != Phase::Done) return nullptr;
      data = slot.result;
      slot.phase = Phase::Free;
      break;
    }
  }
  if (data.empty() || data.size() > 131072) return nullptr;
  auto bytes = env->NewByteArray(static_cast<jsize>(data.size()));
  if (bytes) env->SetByteArrayRegion(bytes, 0, static_cast<jsize>(data.size()),
                                  reinterpret_cast<const jbyte*>(data.data()));
  return bytes;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_projectinfinity_kodi_InfinityCastNative_cancel(JNIEnv*, jclass, jlong id)
{
  auto& state = Store();
  std::lock_guard<std::mutex> lock(state.mutex);
  for (auto& slot : state.slots)
  {
    if (slot.id != static_cast<uint64_t>(id) || slot.phase == Phase::Free) continue;
    const bool beforeCommit = slot.phase == Phase::Queued;
    slot.cancelled = true;
    // A committed/running request retains its actual outcome for the caller.
    // Only a queued request can be discarded as certainly uncommitted.
    if (beforeCommit) slot.consumed = true;
    return beforeCommit ? JNI_TRUE : JNI_FALSE;
  }
  return JNI_FALSE;
}
