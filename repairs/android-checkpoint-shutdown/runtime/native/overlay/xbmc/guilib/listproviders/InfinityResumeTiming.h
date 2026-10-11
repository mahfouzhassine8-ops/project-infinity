/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "utils/log.h"
#include <atomic>
#include <chrono>
#include <string>
#include <cstdint>
#include <map>
#include <mutex>
#include <utility>
#if defined(TARGET_ANDROID)
#include <unistd.h>
#endif

// Observations only. The unchanged provider URL remains the cache/job identity;
// the correlation option is added only to the local Command Center request.
namespace InfinityResumeTiming
{
inline std::atomic<unsigned long long> serial{0};
inline double ClockMs()
{
  return std::chrono::duration<double, std::milli>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
}
inline long Pid()
{
#if defined(TARGET_ANDROID)
  return ::getpid();
#else
  return 0;
#endif
}
inline bool ValidRequest(const std::string& value)
{
  if (value.size() < 2 || value.size() > 31 || (value[0] != 'n' && value[0] != 'p')) return false;
  for (std::size_t i = 1; i < value.size(); ++i)
    if (value[i] < '0' || value[i] > '9') return false;
  return true;
}
struct Card
{
  double started{ClockMs()};
  std::string media{"all"};
  int64_t revision{0};
  int window{0}, control{0};
  bool layout{false}, pending{false}, artReady{false}, fallback{false};
  bool layoutPresented{false}, cardPresented{false};
  bool artLogged{false};
};
inline std::mutex cardMutex;
inline std::map<std::string, Card> cards;
inline Card& BoundedCard(const std::string& request)
{
  if (cards.find(request) == cards.end() && cards.size() >= 128) cards.erase(cards.begin());
  return cards[request];
}
inline void TraceCard(const char* stage, const std::string& request, const Card& card)
{
  const double now = ClockMs();
  try { CLog::Log(LOGINFO, "INFINITY_RESUME_TIMING {{\"schema\":1,\"pid\":{},\"stage\":\"{}\",\"request\":\"{}\",\"media\":\"{}\",\"monotonic_ms\":{},\"elapsed_ms\":{},\"revision\":{},\"window\":{},\"control\":{},\"art_ready\":{},\"art_fallback\":{}}}",
      Pid(), stage, request, card.media, now, now - card.started, card.revision,
      card.window, card.control, card.artReady ? 1 : 0, card.fallback ? 1 : 0); }
  catch (...) { /* Display observations are never persistence authority. */ }
}
inline void Layout(const std::string& request, int64_t revision, int window, int control)
{
  if (!ValidRequest(request)) return;
  try {
    std::lock_guard<std::mutex> lock(cardMutex);
    Card& card = BoundedCard(request);
    card.revision = revision > 0 ? revision : 0; card.window = window; card.control = control;
    if (!card.layout) { card.layout = true; TraceCard("card_layout_ready", request, card); }
  } catch (...) { /* Best effort only. */ }
}
struct ActiveCard
{
  std::string request, poster, thumb;
  bool artReady{false}, fallback{false};
};
inline thread_local ActiveCard activeCard;
class CardScope
{
public:
  CardScope(const std::string& request, std::string poster, std::string thumb)
    : m_previous(std::move(activeCard))
  { activeCard = {ValidRequest(request) ? request : "", std::move(poster), std::move(thumb)}; }
  ~CardScope() { activeCard = std::move(m_previous); }
private:
  ActiveCard m_previous;
};
inline void Texture(const std::string& requested, bool ready, bool fallback)
{
  if (!ready || activeCard.request.empty()) return;
  const bool match = (!activeCard.poster.empty() && requested == activeCard.poster) ||
                     (!activeCard.thumb.empty() && requested == activeCard.thumb) ||
                     (activeCard.poster.empty() && activeCard.thumb.empty() && requested.empty() && fallback);
  if (!match) return;
  activeCard.artReady = true; activeCard.fallback = fallback;
  try {
    std::lock_guard<std::mutex> lock(cardMutex);
    Card& card = BoundedCard(activeCard.request);
    if (!card.artLogged) {
      card.artLogged = true;
      Card observed = card; observed.artReady = true; observed.fallback = fallback;
      TraceCard("card_art_ready", activeCard.request, observed);
    }
  } catch (...) { /* Best effort only. */ }
}
inline void Rendered(const std::string& request)
{
  if (!ValidRequest(request)) return;
  try { std::lock_guard<std::mutex> lock(cardMutex);
    Card& card = BoundedCard(request);
    if (!card.pending) { card.artReady = false; card.fallback = false; }
    if (activeCard.request == request && activeCard.artReady) {
      card.artReady = true; card.fallback = activeCard.fallback;
    }
    card.pending = true;
  }
  catch (...) { /* Best effort only. */ }
}
inline void Presented(bool rendered)
{
  try {
    std::lock_guard<std::mutex> lock(cardMutex);
    for (auto& row : cards) {
      Card& card = row.second;
      if (!card.pending) continue;
      card.pending = false;
      if (!rendered || !card.layout) continue;
      if (!card.layoutPresented) {
        card.layoutPresented = true; TraceCard("first_layout_presented", row.first, card);
      }
      if (card.artReady && !card.cardPresented) {
        card.cardPresented = true; TraceCard("first_card_presented", row.first, card);
      }
    }
  } catch (...) { /* Presentation/authorization behavior remains unchanged. */ }
}
class Observation
{
public:
  explicit Observation(const std::string& url)
    : m_started(ClockMs())
  {
    const std::string prefix = "plugin://script.infinity.commandcenter/";
    if (url.compare(0, prefix.size(), prefix) != 0) return;
    m_request = "n" + std::to_string(++serial);
    m_media = url.find("media=tv") != std::string::npos ? "tv" :
              (url.find("media=movie") != std::string::npos ? "movie" : "all");
    try { std::lock_guard<std::mutex> lock(cardMutex);
      Card& card = BoundedCard(m_request); card.started = m_started; card.media = m_media; }
    catch (...) { /* Best effort only. */ }
  }
  std::string RequestUrl(const std::string& url) const
  {
    return m_request.empty() ? url : url + (url.find('?') == std::string::npos ? "?" : "&") +
        "infinity_trace=" + m_request;
  }
  void Mark(const char* stage, size_t items = 0, size_t queued = 0, size_t active = 0, int64_t revision = 0) const
  {
    if (m_request.empty()) return;
    try { std::lock_guard<std::mutex> lock(cardMutex);
      Card& card = BoundedCard(m_request);
      if (revision > 0) card.revision = revision;
      else revision = card.revision;
    } catch (...) { /* Best effort only. */ }
    const double now = ClockMs();
#if defined(TARGET_ANDROID)
    const long pid = ::getpid();
#else
    const long pid = 0;
#endif
    try { CLog::Log(LOGINFO, "INFINITY_RESUME_TIMING {{\"schema\":1,\"pid\":{},\"stage\":\"{}\",\"request\":\"{}\",\"media\":\"{}\",\"monotonic_ms\":{},\"elapsed_ms\":{},\"items\":{},\"queued\":{},\"active\":{},\"revision\":{}}}",
              pid, stage, m_request, m_media, now, now - m_started, items, queued, active, revision); }
    catch (...) { /* Observations never alter directory completion. */ }
  }
private:
  std::string m_request;
  std::string m_media;
  double m_started;
};
} // namespace InfinityResumeTiming
