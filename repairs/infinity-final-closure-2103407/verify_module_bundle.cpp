// Build-only adapter. Not linked into or packaged with the Android application.
#include "isolated-native/InfinityModuleManifest.h"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc, char** argv)
{
  if (argc != 3) return 2;
  std::ifstream input(argv[2]);
  const std::string key{std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>()};
  InfinityModuleManifest::Verified bundle;
  std::string failure;
  if (!InfinityModuleManifest::Verify(argv[1],key,bundle,failure))
  {
    std::cerr << "Module verification failed: " << failure << '\n';
    return 1;
  }
  std::cout << "NATIVE_VERIFIED package=" << bundle.packageVersion << " protocol="
            << bundle.protocolApi << " files=" << bundle.files.size() << " entries="
            << bundle.entries.size() << " manifest=" << bundle.manifestSha256 << '\n';
  return 0;
}
