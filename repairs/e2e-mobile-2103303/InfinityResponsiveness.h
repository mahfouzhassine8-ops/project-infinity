/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>

namespace InfinityHealth
{
constexpr size_t FIELD_COUNT = 22;
inline std::array<std::atomic<int64_t>, FIELD_COUNT> values{};
inline std::atomic<uint64_t> sequence{0};
inline std::atomic<int64_t> skinGeneration{0};
inline std::atomic<uint64_t> requestedGeometry{0}, committedGeometry{0};
inline std::atomic<int64_t> requestedAt{0}, committedAt{0}, windowGeneration{0};
inline int64_t UptimeMillis()
{
  return std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
}
inline uint64_t Geometry(int width,int height)
{
  return width>0 && height>0 ? (uint64_t(width)<<32)|uint32_t(height) : 0;
}
inline void RequestGeometry(int width,int height)
{
  requestedGeometry.store(Geometry(width,height)); requestedAt.store(UptimeMillis());
}
inline void CommitGeometry(int width,int height)
{
  committedGeometry.store(Geometry(width,height)); committedAt.store(UptimeMillis());
}
inline void ClearGeometry()
{
  requestedGeometry.store(0);committedGeometry.store(0);++windowGeneration;
  requestedAt.store(0);committedAt.store(0);
}
inline void Publish(const std::array<int64_t,FIELD_COUNT>& snapshot)
{
  sequence.fetch_add(1);
  for(size_t i=0;i<FIELD_COUNT;++i)values[i].store(snapshot[i]);
  sequence.fetch_add(1);
}
inline bool Read(std::array<int64_t,FIELD_COUNT>& out)
{
  for(int attempt=0;attempt<3;++attempt)
  {
    uint64_t before=sequence.load();
    if(before&1)continue;
    for(size_t i=0;i<FIELD_COUNT;++i)out[i]=values[i].load();
    if(sequence.load()==before)return true;
  }
  return false; // Never block a watchdog on the rendering thread.
}
}
