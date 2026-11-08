#pragma once

// UI result correlation only. This state never grants persistence admission,
// finishes a writer, certifies durability or changes a provider's result.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <mutex>
#include <optional>
#include <string>
#include <vector>
#include <utility>

namespace InfinitySavedNavigation
{
struct Ticket
{
  std::string token, key, originalPath, path, reason, bucket;
  std::vector<std::string> attempted;
  double resume{0.0};
  bool folder{false}, cancelled{false}, failed{false}, recovering{false}, succeeded{false};
  std::chrono::steady_clock::time_point created;
};

// Watchlist provenance is transient and independent of recovery Ticket state.
struct WatchIdentity
{
  std::string kind, tmdb, tvdb, imdb;
  int season{-1}, episode{-1};
  bool operator==(const WatchIdentity& other) const
  {
    return kind == other.kind && tmdb == other.tmdb && tvdb == other.tvdb &&
        imdb == other.imdb && season == other.season && episode == other.episode;
  }
};
inline bool WatchMatches(const WatchIdentity& expected, const WatchIdentity& actual)
{
  if (expected.kind != actual.kind || expected.season != actual.season ||
      expected.episode != actual.episode) return false;
  bool common = false;
  for (auto pair : {std::make_pair(expected.tmdb, actual.tmdb),
                    std::make_pair(expected.tvdb, actual.tvdb), std::make_pair(expected.imdb, actual.imdb)})
  {
    if (pair.first.empty()) continue;
    if (pair.first != pair.second) return false;
    common = true;
  }
  return common;
}
struct WatchOrigin
{
  std::string token, key, profile, selection, route, provider, selectedToken, launchToken, resolverToken;
  double resume{0};
  int64_t resumeRevision{0};
  WatchIdentity identity;
  uint64_t generation{0};
  int64_t epoch{0};
  std::chrono::steady_clock::time_point created{std::chrono::steady_clock::now()};
};
struct WatchInvocation { int id; WatchOrigin origin; };
struct WatchActive { WatchOrigin origin; std::string path; WatchIdentity identity; };

class Correlation
{
public:
  void Begin(Ticket ticket)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    ticket.created = std::chrono::steady_clock::now();
    m_current = std::move(ticket);
  }
  std::optional<Ticket> Read()
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    Expire();
    return m_current;
  }
  bool Next(const std::string& token, const std::string& path, const std::string& provider)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    Expire();
    if (!m_current || m_current->token != token || !m_current->failed ||
        m_current->attempted.size() >= 8 || path == m_current->path)
      return false;
    for (const auto& previous : m_current->attempted)
      if (previous == provider) return false;
    m_current->path = path;
    m_current->attempted.push_back(provider);
    m_current->cancelled = false;
    m_current->failed = false;
    m_current->reason.clear();
    m_current->recovering = true;
    return true;
  }
  void Cancelled(const std::string& token)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_current && m_current->token == token) m_current->cancelled = true;
  }
  std::optional<Ticket> Finish(const std::string& token, const std::string& path,
                               bool success, const char* reason)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    Expire();
    if (!m_current || m_current->token != token || m_current->path != path || m_current->failed)
      return {};
    if (success || m_current->cancelled)
    {
      auto finished = m_current;
      m_current.reset();
      if (success && !finished->cancelled && finished->recovering)
      {
        finished->succeeded = true;
        return finished;
      }
      return {};
    }
    m_current->failed = true;
    m_current->reason = reason;
    return m_current;
  }
  void Clear(const std::string& token)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_current && m_current->token == token) m_current.reset();
  }
  uint64_t WatchBegin(WatchOrigin origin)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchReset();
    origin.generation = m_watchGeneration;
    origin.created = std::chrono::steady_clock::now();
    m_watch = std::move(origin);
    return m_watchGeneration;
  }
  void WatchFail(const std::string& path, const std::string& resolverToken = "")
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_watch && m_watch->route == path && !m_watchConsumed &&
        (resolverToken.empty() || resolverToken == m_watchResolverToken)) WatchReset();
  }
  void WatchInvalidate()
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchReset();
  }
  std::optional<WatchOrigin> WatchCurrent(const std::string& route, const std::string& profile)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    if (m_watch && m_watch->profile != profile) { WatchReset(); return {}; }
    if (!m_watch || m_watch->route != route) return {};
    return m_watch;
  }
  bool WatchSeal(uint64_t generation, WatchOrigin child)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    if (!m_watch || generation != m_watchGeneration || m_watchSeals.size() >= 256) return false;
    child.generation = generation;
    child.created = m_watch->created;
    m_watchSeals.push_back(std::move(child));
    return true;
  }
  std::optional<WatchOrigin> WatchSelect(const std::string& token, const std::string& route,
                                       const std::string& profile)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    for (const auto& child : m_watchSeals)
    {
      if (child.token != token || child.route != route || child.profile != profile ||
          child.generation != m_watchGeneration) continue;
      auto selected = child;
      WatchReset();
      selected.generation = m_watchGeneration;
      m_watch = selected;
      return selected;
    }
    return {};
  }
  // A direct wrapper receipt authorizes precisely one fresh first-party handoff.
  std::optional<WatchOrigin> WatchLaunch(const std::string& selectedToken, WatchOrigin origin)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    if (!selectedToken.empty() && (!m_watch || m_watch->selectedToken != selectedToken ||
        m_watch->key != origin.key || m_watch->profile != origin.profile ||
        m_watch->selection != origin.selection || m_watch->route != origin.route)) return {};
    const auto now = std::chrono::steady_clock::now();
    m_watchLaunches.erase(std::remove_if(m_watchLaunches.begin(), m_watchLaunches.end(),
        [now](const auto& value) { return now - value.second > std::chrono::minutes(5); }), m_watchLaunches.end());
    if (origin.launchToken.empty() || m_watchLaunches.size() >= 128) return {};
    for (const auto& value : m_watchLaunches) if (value.first == origin.launchToken) return {};
    m_watchLaunches.emplace_back(origin.launchToken, now);
    WatchReset();
    origin.generation = m_watchGeneration;
    origin.created = now;
    m_watch = std::move(origin);
    return m_watch;
  }
  // A route lookup is observation only. Actual item proof is required to mint a permit.
  std::optional<WatchOrigin> WatchItemPermit(const std::string& itemToken,
      const std::string& route, const std::string& profile)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    if (!m_watch || itemToken.empty() || m_watch->token != itemToken ||
        m_watch->route != route || m_watch->profile != profile || m_watchConsumed) return {};
    return m_watch;
  }
  std::optional<WatchOrigin> WatchClaimResolver(const WatchOrigin& permit,
                                              const std::string& resolverToken)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    if (!m_watch || m_watchConsumed || !m_watchResolverToken.empty() || resolverToken.empty() ||
        permit.generation != m_watchGeneration || permit.token != m_watch->token ||
        permit.route != m_watch->route || permit.profile != m_watch->profile) return {};
    m_watchResolverToken = resolverToken;
    auto claimed = permit;
    claimed.resolverToken = resolverToken;
    return claimed;
  }
  // Called under manager serialization, never calls out or holds this lock over Execute.
  void WatchDispatch(int id, const std::optional<WatchOrigin>& observed)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    m_watchInvokers.erase(std::remove_if(m_watchInvokers.begin(), m_watchInvokers.end(),
        [id](const WatchInvocation& value) { return value.id == id; }), m_watchInvokers.end());
    if (observed && m_watch && !m_watchConsumed && observed->generation == m_watchGeneration &&
        observed->token == m_watch->token && !observed->resolverToken.empty() &&
        observed->resolverToken == m_watchResolverToken && m_watchInvokers.size() < 32)
      m_watchInvokers.push_back({id, *observed});
  }
  std::optional<WatchOrigin> WatchConsume(int id, const std::string& provider,
      const std::string& profile, const WatchIdentity& identity, const std::string& path, const std::string& resolverToken = "")
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    for (auto it = m_watchInvokers.begin(); it != m_watchInvokers.end(); ++it)
    {
      if (it->id != id) continue;
      if (!resolverToken.empty() && it->origin.resolverToken != resolverToken) return {};
      const auto origin = it->origin;
      m_watchInvokers.erase(it); // A mismatching actual handoff cannot be retried.
      if (!m_watch || m_watchConsumed || origin.generation != m_watchGeneration || origin.provider != provider ||
          origin.profile != profile || (!resolverToken.empty() && origin.resolverToken != resolverToken) ||
          !WatchMatches(origin.identity, identity)) return {};
      m_watchConsumed = true;
      m_watchInvokers.clear();
      m_watchActive = WatchActive{origin, path, identity};
      return origin;
    }
    return {};
  }
  std::optional<WatchOrigin> WatchReceipt(const std::string& token, const std::string& profile,
      const WatchIdentity& identity, const std::string& path)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    WatchExpire();
    if (m_watch && m_watch->profile != profile) { WatchReset(); return {}; }
    if (!m_watchActive || !m_watch || m_watchActive->origin.token != token ||
        m_watchActive->origin.generation != m_watchGeneration ||
        m_watchActive->origin.profile != profile || m_watchActive->path != path ||
        !WatchMatches(m_watchActive->identity, identity)) return {};
    return m_watchActive->origin;
  }
private:
  void WatchReset()
  {
    ++m_watchGeneration;
    m_watch.reset(); m_watchSeals.clear(); m_watchInvokers.clear(); m_watchActive.reset(); m_watchConsumed = false; m_watchResolverToken.clear();
  }
  void WatchExpire()
  {
    if (m_watch && std::chrono::steady_clock::now() - m_watch->created > std::chrono::minutes(5))
      WatchReset();
  }
  void Expire()
  {
    if (m_current && std::chrono::steady_clock::now() - m_current->created > std::chrono::minutes(5))
      m_current.reset();
  }
  std::mutex m_mutex;
  std::optional<Ticket> m_current;
  uint64_t m_watchGeneration{0};
  bool m_watchConsumed{false};
  std::string m_watchResolverToken;
  std::vector<std::pair<std::string, std::chrono::steady_clock::time_point>> m_watchLaunches;
  std::optional<WatchOrigin> m_watch;
  std::vector<WatchOrigin> m_watchSeals;
  std::vector<WatchInvocation> m_watchInvokers;
  std::optional<WatchActive> m_watchActive;
};
} // namespace InfinitySavedNavigation
