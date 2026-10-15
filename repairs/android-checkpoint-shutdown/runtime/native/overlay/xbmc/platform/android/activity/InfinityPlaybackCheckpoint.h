#pragma once

// Explicit playback persistence checkpoint. This never closes or destroys a
// player: the decoder thread parks with its state and clock still available.
#include "FileItem.h"
#include "cores/VideoSettings.h"
#include "video/Bookmark.h"

#include <memory>
#include <mutex>
#include <string>
#include <utility>

class CApplicationPlayer;
class CApplicationPlayerCallback;

namespace InfinityPlaybackCheckpoint
{
enum class PollResult { Pending, Complete, Failed };

struct Snapshot
{
  CFileItem item;
  CBookmark bookmark;
  CVideoSettings videoSettings;
  bool hasPlayback{false};
};

struct Request
{
  explicit Request(std::string value) : session(std::move(value)) {}
  const std::string session;
  std::mutex mutex;
  bool frozen{false};
  std::string failure;
  Snapshot snapshot;
};

// Called only by the application-thread checkpoint pump. Pending never means
// success. Coordinator must impose its transaction deadline and retain fences.
PollResult Poll(CApplicationPlayer& player, CApplicationPlayerCallback& callback,
                const std::string& session, std::string& failure);
} // namespace InfinityPlaybackCheckpoint
