#include "native/xbmc/guilib/InfinitySavedNavigationState.h"
#include <cassert>
#include <iostream>
#include <thread>
using namespace InfinitySavedNavigation;
WatchOrigin origin(std::string token="a")
{
  WatchOrigin value;
  value.token=token; value.key="saved"; value.profile="profile-A";
  value.selection="capsule"; value.route="plugin://plugin.video.pov/?mode=play_media";
  value.provider="plugin.video.pov";
  value.identity={"episode", "111", "", "", 1, 2};
  return value;
}
WatchOrigin current(Correlation& state)
{
  auto observed = *state.WatchCurrent(origin().route,"profile-A");
  return *state.WatchClaimResolver(observed,"resolver-instance");
}
int main()
{
  Correlation state;
  state.WatchBegin(origin());
  // This is the wrapper's actual inference boundary: same path/profile alone is insufficient.
  assert(state.WatchCurrent(origin().route,"profile-A"));
  assert(!state.WatchItemPermit("",origin().route,"profile-A"));
  assert(!state.WatchItemPermit("wrong-item-seal",origin().route,"profile-A"));
  auto observed=current(state);
  assert(!state.WatchClaimResolver(observed,"ordinary-concurrent-same-route"));
  state.WatchDispatch(10,observed);
  assert(!state.WatchConsume(11,observed.provider,observed.profile,observed.identity,"stream"));
  auto enriched=observed.identity; enriched.imdb="tt123";
  assert(state.WatchConsume(10,observed.provider,observed.profile,enriched,"stream"));
  assert(!state.WatchConsume(10,observed.provider,observed.profile,enriched,"stream"));
  assert(state.WatchReceipt(observed.token,observed.profile,enriched,"stream"));
  assert(!state.WatchReceipt(observed.token,observed.profile,enriched,"reused-url"));
  assert(!state.WatchReceipt(observed.token,"profile-B",enriched,"stream"));
  state.WatchBegin(origin()); observed=current(state);
  state.WatchDispatch(10,observed); state.WatchDispatch(10,{});
  assert(!state.WatchConsume(10,observed.provider,observed.profile,enriched,"stream"));
  state.WatchDispatch(10,observed);
  auto mismatch=enriched; mismatch.episode=3;
  assert(!state.WatchConsume(10,observed.provider,observed.profile,mismatch,"stream"));
  assert(!state.WatchConsume(10,observed.provider,observed.profile,enriched,"stream"));
  auto child=observed; child.token="child"; child.route="child-route";
  assert(state.WatchSeal(observed.generation,child));
  assert(!state.WatchSelect("child","other-route",observed.profile));
  assert(!state.WatchSelect("child",child.route,"profile-B"));
  assert(state.WatchSelect("child",child.route,observed.profile));
  auto itemPermit=state.WatchItemPermit("child",child.route,observed.profile);
  assert(itemPermit);
  auto resolver=state.WatchClaimResolver(*itemPermit,"selected-exact-instance");
  assert(resolver);
  assert(!state.WatchClaimResolver(*itemPermit,"ordinary-concurrent-instance"));
  state.WatchDispatch(40,*resolver);
  // Unobserved same-route result has no instance id; wrong/stale instance cannot consume it.
  assert(!state.WatchConsume(-1,resolver->provider,resolver->profile,resolver->identity,"stream","selected-exact-instance"));
  assert(!state.WatchConsume(40,resolver->provider,resolver->profile,resolver->identity,"stream","ordinary-concurrent-instance"));
  assert(state.WatchConsume(40,resolver->provider,resolver->profile,resolver->identity,"stream","selected-exact-instance"));
  assert(!state.WatchSelect("child",child.route,observed.profile));
  assert(!state.WatchSeal(observed.generation,child));
  state.WatchDispatch(10,observed);
  assert(!state.WatchConsume(10,observed.provider,observed.profile,enriched,"stream"));
  state.WatchBegin(origin("new")); observed=current(state);
  std::thread a([&]{state.WatchDispatch(20,observed);});
  std::thread b([&]{state.WatchDispatch(21,{});}); a.join(); b.join();
  assert(!state.WatchConsume(21,observed.provider,observed.profile,enriched,"stream"));
  assert(state.WatchConsume(20,observed.provider,observed.profile,enriched,"stream"));
  state.WatchInvalidate();
  assert(!state.WatchReceipt(observed.token,observed.profile,enriched,"stream"));
  auto selected=origin(); selected.selectedToken="click";
  state.WatchBegin(selected);
  auto request=origin("launch"); request.launchToken="request"; request.selection="stale";
  assert(!state.WatchLaunch("click",request));
  request.selection=selected.selection;
  assert(state.WatchLaunch("click",request));
  assert(!state.WatchLaunch("click",request));
  assert(!state.WatchLaunch("",request)); // Popup-style replay cannot bypass the nonce ledger.
  state.WatchBegin(origin()); observed=current(state);
  state.WatchDispatch(30,observed); state.WatchFail(observed.route);
  assert(!state.WatchConsume(30,observed.provider,observed.profile,enriched,"stream"));
  state.WatchBegin(origin()); observed=current(state);
  state.WatchDispatch(31,observed);
  assert(!state.WatchConsume(31,"plugin.video.ordinary",observed.profile,enriched,"stream"));
  assert(!state.WatchConsume(31,observed.provider,observed.profile,enriched,"stream"));
  state.WatchDispatch(32,observed);
  assert(state.WatchConsume(32,observed.provider,observed.profile,enriched,"stream"));
  // POV may finish its original resolver unsuccessfully after its fresh self.play handoff.
  state.WatchFail(observed.route);
  assert(state.WatchReceipt(observed.token,observed.profile,enriched,"stream"));
  state.WatchInvalidate(); // Explicit cancellation invalidates an already issued receipt.
  assert(!state.WatchReceipt(observed.token,observed.profile,enriched,"stream"));
  state.WatchBegin(origin()); observed=current(state);
  for (int i=0; i<256; ++i) assert(state.WatchSeal(observed.generation,origin(std::to_string(i))));
  assert(!state.WatchSeal(observed.generation,origin("overflow")));
  // Recovery correlation is independent of origin supersession/cancellation.
  Ticket recovery; recovery.token="recovery"; recovery.path="recovery-route";
  state.Begin(recovery); state.WatchInvalidate();
  assert(state.Read()->token=="recovery");
  std::cout << "PASS native Watchlist focused state contract\n";
}
