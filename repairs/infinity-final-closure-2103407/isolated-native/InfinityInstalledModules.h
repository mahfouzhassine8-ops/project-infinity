#pragma once

#include <cstddef>
#include <string>

namespace InfinityInstalledModules
{
// Admission and participant checks always verify the signed manifest and its
// actual code. Unknown addons never enter this trust path.
std::string Classify(const std::string& absoluteScript, const std::string& addonId);
bool Participant(const std::string& packageVersion,
                 unsigned int protocolApi,
                 const std::string& manifestSha256);

// An availability hint for existing Infinity GUI ownership gates. It performs
// no hashing, imports, writes, scanning or native admission. A real invocation
// still must pass Classify and the existing write/identity fences.
bool CapabilityReady(const std::string& addonId,
                     const std::string& addonRoot,
                     const std::string& capability);
} // namespace InfinityInstalledModules

// Read-only handshake for the authenticated Command Center bootstrap. The
// supplied root must equal a native-resolved installed Command Center root.
// No caller-supplied public key, success flag, source hash list or writer lease.
extern "C" __attribute__((visibility("default"))) int InfinityCommandCenterIdentityV1(
    const char* commandCenterRoot,
    char* packageVersion, size_t versionCapacity,
    char* manifestSha256, size_t hashCapacity,
    unsigned int* protocolApi);
