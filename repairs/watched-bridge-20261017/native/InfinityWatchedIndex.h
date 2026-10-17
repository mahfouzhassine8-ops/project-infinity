// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

// The render-side lookup owns plain immutable metadata only. It never enters
// Python, a GUI/window lock, a directory provider, a database or the filesystem.
#include <algorithm>
#include <atomic>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

namespace InfinityWatched
{
struct Identity
{
  std::string kind;
  std::string scope;
  std::map<std::string, std::string> ids;
  int season{-1};
  int episode{-1};
};

struct Record
{
  Identity identity;
  bool watched{false};
};

inline bool ValidID(const std::string& name, const std::string& value)
{
  const auto digits = [](const std::string& text) {
    return !text.empty() && text.find_first_not_of("0123456789") == std::string::npos;
  };
  if (name == "tmdb" || name == "tvdb")
    return value.size() <= 20 && digits(value) && value.front() != '0';
  if (name == "imdb")
    return value.size() >= 7 && value.size() <= 14 && value.compare(0, 2, "tt") == 0 && digits(value.substr(2));
  return false;
}

inline bool Valid(const Identity& identity)
{
  if (identity.ids.empty() || identity.ids.size() > 3)
    return false;
  for (const auto& [name, value] : identity.ids)
    if (!ValidID(name, value))
      return false;
  if (identity.kind == "movie")
    return identity.scope == "movie" && identity.season == -1 && identity.episode == -1;
  return identity.kind == "episode" &&
         (identity.scope == "episode" || identity.scope == "show_episode") &&
         identity.season >= 0 && identity.season <= 100000 &&
         identity.episode >= 0 && identity.episode <= 100000;
}

inline std::vector<std::string> Aliases(const Identity& identity)
{
  std::vector<std::string> aliases;
  const auto suffix = identity.kind == "episode" ?
      ":" + std::to_string(identity.season) + ":" + std::to_string(identity.episode) : "";
  for (const auto& [name, value] : identity.ids)
    aliases.push_back(identity.scope + ":" + name + ":" + value + suffix);
  return aliases;
}

inline bool Same(const Identity& left, const Identity& right)
{
  if (left.kind != right.kind || left.scope != right.scope ||
      left.season != right.season || left.episode != right.episode)
    return false;
  bool common = false;
  for (const auto& [name, value] : left.ids)
  {
    const auto found = right.ids.find(name);
    if (found != right.ids.end())
    {
      common = true;
      if (found->second != value)
        return false;
    }
  }
  return common;
}

class Index
{
public:
  explicit Index(std::vector<Record> records) : m_records(std::move(records))
  {
    for (size_t index = 0; index < m_records.size(); ++index)
      for (const auto& alias : Aliases(m_records[index].identity))
        m_aliases[alias].insert(index);
  }

  std::string Lookup(const Identity& query) const
  {
    if (!Valid(query))
      return {};
    std::set<size_t> candidates;
    for (const auto& alias : Aliases(query))
    {
      const auto found = m_aliases.find(alias);
      if (found != m_aliases.end())
        candidates.insert(found->second.begin(), found->second.end());
    }
    if (candidates.empty())
      return {};
    const bool state = m_records[*candidates.begin()].watched;
    for (size_t left : candidates)
    {
      if (!Same(m_records[left].identity, query) || m_records[left].watched != state)
        return {};
      for (size_t right : candidates)
        if (!Same(m_records[left].identity, m_records[right].identity))
          return {}; // Shared aliases with contradictory metadata are unknown.
    }
    return state ? "true" : "false";
  }

private:
  const std::vector<Record> m_records;
  std::unordered_map<std::string, std::set<size_t>> m_aliases;
};

inline std::shared_ptr<const Index>& Published()
{
  static std::shared_ptr<const Index> value;
  return value;
}

inline bool Publish(std::vector<Record> records)
{
  if (records.size() > 1200 ||
      std::any_of(records.begin(), records.end(), [](const Record& row) { return !Valid(row.identity); }))
    return false;
  std::shared_ptr<const Index> replacement = std::make_shared<Index>(std::move(records));
  std::atomic_store_explicit(&Published(), std::move(replacement), std::memory_order_release);
  return true;
}

inline void Clear()
{
  std::atomic_store_explicit(&Published(), std::shared_ptr<const Index>{}, std::memory_order_release);
}

inline std::string Lookup(const Identity& identity)
{
  const auto view = std::atomic_load_explicit(&Published(), std::memory_order_acquire);
  return view ? view->Lookup(identity) : std::string{};
}
} // namespace InfinityWatched
