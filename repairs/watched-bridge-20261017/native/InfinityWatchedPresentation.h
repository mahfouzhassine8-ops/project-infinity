// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "InfinityWatchedIndex.h"
#include "FileItem.h"
#include "URL.h"
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
  const CURL route(item.GetPath());
  const std::string provider = route.GetProtocol() == "plugin" ? route.GetHostName() : "";
  const bool nativeLibrary = route.GetProtocol() == "videodb" && tag->m_iDbId > 0;
  return LookupItem(std::move(query), provider, nativeLibrary);
}
} // namespace InfinityWatched
