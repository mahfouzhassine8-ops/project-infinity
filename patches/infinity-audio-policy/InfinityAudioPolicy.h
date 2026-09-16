/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <cstdint>

// API 1: native audio classification, not an effects engine or Samsung opt-in.
// The numbers match public Android AudioAttributes content type values.
namespace INFINITY_AUDIO
{
constexpr int API_VERSION = 1;
constexpr int UNKNOWN = 0;
constexpr int SPEECH = 1;
constexpr int MUSIC = 2;
constexpr int MOVIE = 3;
constexpr int SONIFICATION = 4;
constexpr uint32_t DEFAULT_POLICY = MOVIE | (MUSIC << 4) | (SONIFICATION << 8);

constexpr bool ValidContent(int value)
{
  return value >= SPEECH && value <= SONIFICATION;
}
constexpr int NormalizeStreamRole(int value)
{
  return ValidContent(value) ? value : MUSIC;
}
constexpr int SelectStreamRole(int current, int next)
{
  next = NormalizeStreamRole(next);
  if (current == MOVIE || next == MOVIE) return MOVIE;
  if (current == SPEECH || next == SPEECH) return SPEECH;
  if (current == MUSIC || next == MUSIC) return MUSIC;
  return SONIFICATION;
}
constexpr int ResolvePacked(uint32_t policy, int role)
{
  const int shift = role == MOVIE ? 0 : role == SONIFICATION ? 8 : 4;
  const int selected = (policy >> shift) & 15u;
  return ValidContent(selected) ? selected : NormalizeStreamRole(role);
}
constexpr const char* Name(int value)
{
  return value == MOVIE ? "movie" : value == MUSIC ? "music" :
         value == SPEECH ? "speech" : value == SONIFICATION ? "sonification" : "unknown";
}

// Reload only at new-stream/playback boundaries. No timer, polling loop or
// AudioTrack recreation on pause/seek/fold. Policy updates apply on next play.
void Reload();
int Resolve(int role);
uint32_t Revision();
void NoteTrack(int content);
int TrackContent();
} // namespace INFINITY_AUDIO
