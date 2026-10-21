// Translation-unit-local, memory-only touch pairs. No existing control gains
// a data member or virtual slot: preserve all original class layouts/thunks.
#include <atomic>
#include <chrono>
#include <mutex>
#include <string>
#include <unordered_map>
namespace
{
enum class InfinityTouchDecision { SelectOnly, Activate, Context };
struct InfinityTouchPair
{
  std::string key;
  std::chrono::steady_clock::time_point suppressUntil{};
};
struct InfinityTouchStore
{
  std::mutex mutex;
  std::unordered_map<const void*,InfinityTouchPair> pairs;
};
std::atomic<InfinityTouchStore*> gInfinityTouchStore{nullptr};
InfinityTouchStore& InfinityTouchStoreForPress()
{
  // Process lifetime avoids static-destruction ordering with GUI controls.
  // Control destructors erase their entries; clear/forget never allocate.
  static auto* const store=[] {
    auto* value=new InfinityTouchStore;
    gInfinityTouchStore.store(value,std::memory_order_release);
    return value;
  }();
  return *store;
}
InfinityTouchDecision InfinityTouchPress(const void* owner,const std::string& key,
    bool sameSelection,bool hold,std::chrono::steady_clock::time_point now)
{
  auto& store=InfinityTouchStoreForPress();
  std::lock_guard<std::mutex> lock(store.mutex);
  auto& pair=store.pairs[owner];
  if(hold)
  {
    pair.key.clear();pair.suppressUntil=now+std::chrono::milliseconds(600);
    return InfinityTouchDecision::Context;
  }
  if(now<pair.suppressUntil)return InfinityTouchDecision::SelectOnly;
  if(sameSelection && !key.empty() && pair.key==key)
  {
    pair.key.clear();return InfinityTouchDecision::Activate;
  }
  pair.key=key;return InfinityTouchDecision::SelectOnly;
}
void InfinityTouchClearForAction(const void* owner)
{
  auto* store=gInfinityTouchStore.load(std::memory_order_acquire);
  if(!store)return;
  std::lock_guard<std::mutex> lock(store->mutex);
  const auto found=store->pairs.find(owner);
  if(found!=store->pairs.end())found->second.key.clear();
}
void InfinityTouchForget(const void* owner)
{
  auto* store=gInfinityTouchStore.load(std::memory_order_acquire);
  if(!store)return;
  std::lock_guard<std::mutex> lock(store->mutex);
  store->pairs.erase(owner);
}
} // No GUI, file I/O or callback runs while the sidecar mutex is held.
