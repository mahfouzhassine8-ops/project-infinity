#include "InfinityAudioPolicy.h"
#include <cassert>
#include <iostream>
using namespace INFINITY_AUDIO;
int main()
{
  static_assert(API_VERSION == 1);
  static_assert(ResolvePacked(DEFAULT_POLICY, MOVIE) == MOVIE);
  static_assert(ResolvePacked(DEFAULT_POLICY, MUSIC) == MUSIC);
  static_assert(ResolvePacked(DEFAULT_POLICY, SONIFICATION) == SONIFICATION);
  static_assert(ResolvePacked(DEFAULT_POLICY, UNKNOWN) == MUSIC);
  static_assert(SelectStreamRole(MUSIC, MOVIE) == MOVIE);
  static_assert(SelectStreamRole(MOVIE, MUSIC) == MOVIE);
  static_assert(SelectStreamRole(SONIFICATION, UNKNOWN) == MUSIC);
  const uint32_t legacy = MUSIC | (MUSIC << 4) | (MUSIC << 8);
  for (int r = 0; r < 5; ++r) assert(ResolvePacked(legacy, r) == MUSIC);
  // Malformed packed values can never reach Android as unknown/invalid content.
  for (uint32_t config = 0; config < 4096; ++config)
    for (int role = 0; role < 5; ++role)
      assert(ValidContent(ResolvePacked(config, role)));
  // Equal PCM formats still require a new sink on role transitions.
  int sink = ResolvePacked(DEFAULT_POLICY, MUSIC);
  const int video = ResolvePacked(DEFAULT_POLICY, MOVIE);
  assert(video != sink); sink = video;
  assert(ResolvePacked(DEFAULT_POLICY, MOVIE) == sink); // seek/resume/fold: same policy
  assert(ResolvePacked(DEFAULT_POLICY, MUSIC) != sink);
  std::cout << "PASS: policy defaults, bounds, legacy mapping, mixed streams, role transitions\n";
}
