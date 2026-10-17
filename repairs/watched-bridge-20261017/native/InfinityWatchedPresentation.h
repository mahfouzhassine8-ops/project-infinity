// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "InfinityWatchedIndex.h"
#include "FileItem.h"
#include "utils/StringUtils.h"
#include "video/VideoInfoTag.h"

namespace InfinityWatched
{
inline std::string ItemState(const CFileItem& item)
{
  if (!item.HasVideoInfoTag())
    return {};
  const auto* tag = item.GetVideoInfoTag();
  Identity query;
  query.kind = tag->m_type;
  if (query.kind == "movie")
    query.scope = "movie";
  else if (query.kind == "episode")
  {
    query.scope = "episode";
    query.season = tag->m_iSeason;
    query.episode = tag->m_iEpisode;
  }
  else
    return {}; // Never infer a title, show folder, season or absolute mapping.
  for (const std::string name : {"tmdb", "tvdb", "imdb"})
  {
    std::string value = tag->GetUniqueID(name);
    StringUtils::Trim(value);
    if (ValidID(name, value))
      query.ids[name] = std::move(value);
  }
  const auto episodeState = Lookup(query);
  if (query.kind != "episode")
    return episodeState;
  Identity showQuery = query;
  showQuery.scope = "show_episode";
  showQuery.ids.clear();
  // Only explicitly namespaced series identifiers can enter series scope.
  // Generic episode IDs are never silently reinterpreted as a show's IDs.
  for (const std::string name : {"tmdb", "tvdb", "imdb"})
  {
    std::string value = tag->GetUniqueID(name + "show");
    StringUtils::Trim(value);
    if (ValidID(name, value))
      showQuery.ids[name] = std::move(value);
  }
  const auto showState = Lookup(showQuery);
  if (!episodeState.empty() && !showState.empty() && episodeState != showState)
    return {};
  return !episodeState.empty() ? episodeState : showState;
}
} // namespace InfinityWatched
