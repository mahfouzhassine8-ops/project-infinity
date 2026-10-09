// HOST TEST DOUBLE. Not a production Kodi header.
#pragma once
#include <atomic>
#include <memory>
#include <string>
#include <vector>
namespace ADDON {
struct TestAddon { std::string id; const std::string& ID() const { return id; } };
using AddonPtr = std::shared_ptr<TestAddon>;
}
enum InvokerState { InvokerStateUninitialized, InvokerStateInitialized, InvokerStateRunning,
  InvokerStateStopping, InvokerStateScriptDone, InvokerStateExecutionDone, InvokerStateFailed };
class ILanguageInvoker {
public:
  explicit ILanguageInvoker(void*) {}
  virtual ~ILanguageInvoker() = default;
  bool Execute(const std::string& script, const std::vector<std::string>& args = {}) { return execute(script,args); }
  bool Stop(bool wait=false) { return stop(wait); }
  void SetId(int id) { m_id=id; }
  int GetId() const { return m_id; }
  void SetAddon(const ADDON::AddonPtr& addon) { m_addon=addon; }
  InvokerState GetState() const { return m_state.load(); }
  virtual void onExecutionDone() {}
  virtual void onExecutionFailed() {}
protected:
  virtual bool execute(const std::string&,const std::vector<std::string>&)=0;
  virtual bool stop(bool)=0;
  ADDON::AddonPtr m_addon;
  std::atomic<InvokerState> m_state{InvokerStateUninitialized};
private:
  int m_id{-1};
};
using LanguageInvokerPtr = std::shared_ptr<ILanguageInvoker>;
