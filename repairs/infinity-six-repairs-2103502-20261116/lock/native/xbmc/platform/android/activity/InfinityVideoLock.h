#pragma once

#include <string>
#include <vector>

class CAction;

namespace InfinityVideoLock
{
// Internal Kodi integration only. JNI methods are registered privately, so the
// existing exported native ABI and all non-lock entry points remain unchanged.
__attribute__((visibility("hidden"))) int Open(const std::vector<std::string>& params);
__attribute__((visibility("hidden"))) bool BlocksAction(const CAction& action);
}
