/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "InfinityAudioPolicy.h"

#include "filesystem/File.h"
#include "utils/JSONVariantParser.h"
#include "utils/Variant.h"
#include "utils/log.h"

#include <atomic>
#include <mutex>
#include <string>

namespace INFINITY_AUDIO
{
namespace
{
std::atomic<uint32_t> s_policy{DEFAULT_POLICY};
std::atomic<uint32_t> s_revision{0};
std::atomic<int> s_track{UNKNOWN};
std::mutex s_loadMutex;
constexpr const char* CONFIG = "special://profile/infinity-audio-policy.json";

int ReadContent(const CVariant& value, int fallback)
{
  if (!value.isString()) return fallback;
  const std::string name = value.asString();
  if (name == "movie") return MOVIE;
  if (name == "music") return MUSIC;
  if (name == "speech") return SPEECH;
  if (name == "sonification") return SONIFICATION;
  return fallback;
}
}

void Reload()
{
  // Called on control/event paths only, never inside the AudioTrack write loop.
  std::lock_guard<std::mutex> lock(s_loadMutex);
  uint32_t policy = DEFAULT_POLICY;
  XFILE::CFile file;
  if (file.Open(CONFIG))
  {
    const int64_t length = file.GetLength();
    if (length > 0 && length <= 4096)
    {
      std::string text(static_cast<size_t>(length), '\0');
      CVariant data;
      if (file.Read(&text[0], text.size()) == length &&
          CJSONVariantParser::Parse(text, data) && data.isObject() &&
          data["schema"].isInteger() && data["schema"].asInteger() == API_VERSION)
      {
        const int video = ReadContent(data["video"], MOVIE);
        const int music = ReadContent(data["music"], MUSIC);
        const int ui = ReadContent(data["ui"], SONIFICATION);
        policy = static_cast<uint32_t>(video | (music << 4) | (ui << 8));
      }
      else
        CLog::Log(LOGWARNING, "Infinity AudioPolicy: invalid API-1 configuration; using defaults");
    }
    else
      CLog::Log(LOGWARNING, "Infinity AudioPolicy: configuration exceeds bounds; using defaults");
  }
  if (s_policy.exchange(policy) != policy || s_revision.load() == 0)
  {
    ++s_revision;
    CLog::Log(LOGINFO, "Infinity AudioPolicy API 1: video={} music={} ui={} revision={}",
              Name(ResolvePacked(policy, MOVIE)), Name(ResolvePacked(policy, MUSIC)),
              Name(ResolvePacked(policy, SONIFICATION)), s_revision.load());
  }
}
int Resolve(int role) { return ResolvePacked(s_policy.load(), role); }
uint32_t Revision() { return s_revision.load(); }
void NoteTrack(int content)
{
  s_track.store(content);
  CLog::Log(LOGINFO, "Infinity AudioPolicy API 1 AudioTrack: USAGE_MEDIA CONTENT_TYPE_{}",
            Name(content));
}
int TrackContent() { return s_track.load(); }
} // namespace INFINITY_AUDIO
