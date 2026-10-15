#!/usr/bin/env python3
"""Compile actual system-info classification/work/callback methods and real headers.

OS and network getters are controlled peers. This checks the exact job/callback
pair, inherited overrides, memory-only callback behavior and the named operation;
it does not establish Android ABI or classify arbitrary system/network backends.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from test_checked_sqlite import extract_function


PEERS = r'''
#include "utils/SystemInfo.h"
#include <cassert>
#include <cstring>
#include <iostream>
#include <string>
#include <typeinfo>

// These boundary adapters avoid live OS/network requests in the host harness.
struct CPUInfo { double GetCPUFrequency() const { return 2400; } };
struct CServiceBroker {
  static CPUInfo* GetCPUInfo() { static CPUInfo cpu; return &cpu; }
};
struct StringUtils {
  static std::string Format(const char*, double) { return "2400 MHz"; }
};
struct CTimeUtils { static unsigned int GetFrameTime() { return 42; } };

CSysInfoJob::CSysInfoJob() = default;
CSysInfo::~CSysInfo() = default;
CInfoLoader::~CInfoLoader() = default;
bool CJob::ShouldCancel(unsigned int, unsigned int) const { return false; }
std::string CInfoLoader::TranslateInfo(int) const { return {}; }
std::string CInfoLoader::BusyInfo(int) const { return {}; }
std::string CInfoLoader::GetInfo(int info) { return TranslateInfo(info); }
std::string CSysInfo::TranslateInfo(int) const {
  return m_info.ipAddress + "/" + m_info.systemTotalUptime;
}
bool CSysInfo::Load(const TiXmlNode*) { return true; }
bool CSysInfo::Save(TiXmlNode*) const { return true; }
std::string CSysInfo::GetOsPrettyNameWithVersion() { return "Android"; }
std::string CSysInfo::GetKernelName(bool) { return "Linux"; }
std::string CSysInfo::GetKernelVersionFull() { return "test"; }
std::string CSysInfoJob::GetSystemUpTime(bool total) { return total ? "137" : "1"; }
CSysData::INTERNET_STATE CSysInfoJob::GetInternetState() { return CSysData::CONNECTED; }
std::string CSysInfoJob::GetVideoEncoder() { return "GPU"; }
std::string CSysInfoJob::GetMACAddress() { return "test-mac"; }
std::string CSysInfoJob::GetBatteryLevel() { return "80%"; }
std::string CSysInfoJob::GetIPAddress() { return "192.0.2.1"; }
std::string CSysInfoJob::GetNetMask() { return "255.255.255.0"; }
std::vector<std::string> CSysInfoJob::GetDNSServers() { return {"192.0.2.2"}; }
std::string CSysInfoJob::GetGatewayAddress() { return "192.0.2.3"; }
std::string CSysInfoJob::GetNetworkLinkState() { return "connected"; }
'''

TESTS = r'''
struct UnrelatedCallback : IJobCallback {
  void OnJobComplete(unsigned int, bool, CJob*) override {}
};
struct DerivedCallback : CSysInfo {
  void OnJobComplete(unsigned int, bool, CJob*) override {}
};
struct DerivedJob : CSysInfoJob { bool DoWork() override { return true; } };
struct UnclassifiedJob : CJob { bool DoWork() override { return true; } };

int main() {
  using Responsibility = CJob::CheckpointResponsibility;
  CSysInfoJob job;
  CSysInfo callback;
  IJobCallback* exactCallback = &callback;
  UnrelatedCallback other;
  DerivedCallback derivedCallback;
  DerivedJob derivedJob;
  UnclassifiedJob unclassified;

  assert(job.GetCheckpointResponsibility(nullptr) == Responsibility::NonPersistent);
  assert(job.GetCheckpointResponsibility(exactCallback) == Responsibility::NonPersistent);
  assert(job.GetCheckpointResponsibility(&other) == Responsibility::Unknown);
  assert(job.GetCheckpointResponsibility(&derivedCallback) == Responsibility::Unknown);
  assert(derivedJob.GetCheckpointResponsibility(exactCallback) == Responsibility::Unknown);
  assert(derivedJob.GetCheckpointResponsibility(nullptr) == Responsibility::Unknown);
  assert(unclassified.GetCheckpointResponsibility(nullptr) == Responsibility::Unknown);
  assert(unclassified.GetCheckpointResponsibility(exactCallback) == Responsibility::Unknown);
  assert(std::string(job.GetCheckpointOperation()) == "system-info-read");

  callback.SetTotalUptime(137);
  assert(job.DoWork());
  assert(job.GetData().internetState == CSysData::CONNECTED);
  assert(job.GetData().ipAddress == "192.0.2.1");
  exactCallback->OnJobComplete(7, true, &job);
  assert(callback.GetInfo(0) == "192.0.2.1/137");
  assert(callback.GetTotalUptime() == 137);
  std::cout << "PASS exact_system_info_pair_only_and_callback_preserves_persistent_uptime\n";
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    root = args.runtime.resolve() / "xbmc"
    source = (root / "utils/SystemInfo.cpp").read_text()
    loader = (root / "utils/InfoLoader.cpp").read_text()
    methods = [extract_function(source, signature) for signature in [
        "CJob::CheckpointResponsibility CSysInfoJob::GetCheckpointResponsibility(",
        "const char* CSysInfoJob::GetCheckpointOperation() const",
        "bool CSysInfoJob::DoWork()",
        "const CSysData &CSysInfoJob::GetData() const",
        "CSysInfo::CSysInfo(void)",
        "CJob *CSysInfo::GetJob() const",
        "void CSysInfo::OnJobComplete(unsigned int jobID, bool success, CJob *job)",
    ]]
    methods.extend(extract_function(loader, signature) for signature in [
        "CInfoLoader::CInfoLoader(unsigned int timeToRefresh)",
        "void CInfoLoader::OnJobComplete(unsigned int jobID, bool success, CJob *job)",
    ])
    with tempfile.TemporaryDirectory(prefix="infinity-system-info-") as directory:
        directory = Path(directory)
        cpp, binary = directory / "test.cpp", directory / "test"
        cpp.write_text(PEERS + "\n".join(methods) + TESTS)
        subprocess.run([
            "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter",
            "-I", str(root), str(cpp), "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == "__main__":
    main()
