/* Resource/deadline feasibility prototype; no production activation. */
#pragma once
#include "wire.h"
#include <atomic>
#include <string>

enum class DnsOutcome { Answer, Timeout, Cancelled, Unsupported, Capacity, Failed };
struct DnsResult {
  int preexec_extra_fds = -1;
  DnsOutcome outcome = DnsOutcome::Failed;
  dns_reply reply{};
  double spawn_seconds = 0, return_seconds = 0, cleanup_seconds = 0;
  int wait_error = 0;
  int child_code = 0, child_status = 0;
};
DnsResult OwnedLookup(const std::string& absoluteHelper, const dns_request& request,
                      int deadlineMs, const std::atomic<bool>* cancelled);
