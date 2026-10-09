// HOST TEST DOUBLE. Simulates a blocking manager completion callback.
#pragma once
#include <functional>
class CScriptInvocationManager {
public:
  std::function<void(int)> callback;
  void OnExecutionDone(int id) { if (callback) callback(id); }
};
