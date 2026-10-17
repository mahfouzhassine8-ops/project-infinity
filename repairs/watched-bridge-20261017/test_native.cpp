// SPDX-License-Identifier: GPL-2.0-or-later
#include "native/InfinityWatchedIndex.h"
#include <iostream>
#include <stdexcept>
#include <thread>

using namespace InfinityWatched;

static void require(bool value, const char* label)
{
  if (!value)
    throw std::runtime_error(label);
}

int main()
{
  const Identity movie{"movie", "movie", {{"tmdb", "123"}, {"imdb", "tt00123"}}};
  const Identity otherNamespace{"movie", "movie", {{"tvdb", "123"}}};
  const Identity episode{"episode", "episode", {{"tmdb", "123"}}, 1, 2};
  const Identity show{"episode", "show_episode", {{"tmdb", "123"}}, 1, 2};
  const Identity special{"episode", "episode", {{"tmdb", "123"}}, 0, 0};
  require(Publish({{movie, true}, {episode, true}, {special, true}}), "publish valid records");
  require(Lookup(movie) == "true", "typed movie");
  require(Lookup(Identity{"movie", "movie", {{"imdb", "tt00123"}}}) == "true", "cross-provider namespace alias");
  require(Lookup(otherNamespace).empty(), "equal numeric foreign namespace is unknown");
  require(Lookup(episode) == "true" && Lookup(special) == "true", "season/episode and zero special");
  require(Lookup(show).empty(), "show and episode scopes never conflate");
  Identity absolute = episode; absolute.episode = 102;
  require(Lookup(absolute).empty(), "absolute anime number not guessed");
  Identity conflict = movie; conflict.ids["imdb"] = "tt00999";
  require(Lookup(conflict).empty(), "one equal namespace cannot hide a conflicting namespace");
  require(Publish({{movie, false}}) && Lookup(movie) == "false", "explicit Unwatched");
  require(Publish({{movie, true}, {conflict, true}}), "contradictory records stay representable for rejection");
  require(Lookup(Identity{"movie", "movie", {{"tmdb", "123"}}}).empty(), "ambiguous reduced metadata is withheld");
  require(Publish({{movie, true}, {movie, false}}) && Lookup(movie).empty(), "mixed watched records unknown");
  Identity malformed = movie; malformed.ids["tmdb"] = "00123";
  require(!Publish({{malformed, true}}), "invalid identifiers rejected");
  require(!Publish(std::vector<Record>(1201, {movie, true})), "bounded publication");
  Clear(); require(Lookup(movie).empty(), "profile clear");
  std::atomic<bool> failed{false};
  std::thread writer([&]() {
    for (int pass = 0; pass < 5000; ++pass)
    {
      Publish({{movie, (pass % 2) == 0}});
      if (pass % 3 == 0) Clear();
    }
  });
  std::thread reader([&]() {
    for (int pass = 0; pass < 15000; ++pass)
    {
      const auto value = Lookup(movie);
      if ((!value.empty() && value != "true" && value != "false") || !Lookup(otherNamespace).empty())
        failed = true;
    }
  });
  writer.join(); reader.join();
  require(!failed, "concurrent immutable publication and lookup");
  std::cout << "{\"passed\":true,\"typed_identity_cases\":14,\"concurrent_publications\":5000,\"concurrent_lookups\":15000,\"physical_fold_verified\":false}\n";
}
