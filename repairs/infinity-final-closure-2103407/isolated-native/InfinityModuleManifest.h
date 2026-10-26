#pragma once

// Infinity-only trust primitive. This portable verifier has no Kodi globals,
// worker, writer, GUI, player, shutdown or termination side effects.
#include <map>
#include <set>
#include <string>

namespace InfinityModuleManifest
{
constexpr unsigned int PROTOCOL_API = 1;

struct Verified
{
  std::string packageVersion;
  std::string manifestSha256;
  unsigned int protocolApi{0};
  std::set<std::string> capabilities;
  std::map<std::string, std::string> files;
  std::map<std::string, std::string> entries;
};

// Production adapters must supply the immutable original Infinity public key
// and a native-resolved installed add-ons root. Neither is read from the signed
// manifest or from a Python-owned success/property receipt.
// Every call rechecks actual bounded source files and rejects symlinks.
bool Verify(const std::string& addonsRoot,
            const std::string& trustedPublicKeyPem,
            Verified& result,
            std::string& failure);

// No wildcard addon/owner classification. The path must be an exact signed
// entry in the verified bundle, with its explicit first-party addon identity.
std::string EntryOwner(const Verified& bundle,
                       const std::string& relativeScript,
                       const std::string& addonId);
} // namespace InfinityModuleManifest
