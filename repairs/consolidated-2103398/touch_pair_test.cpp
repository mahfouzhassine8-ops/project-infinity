#include "touch_pair_state.inc"
#include <cassert>
#include <iostream>
#include <thread>
#include <vector>
int main()
{
  int first=1,second=2;
  using D=InfinityTouchDecision;
  using Clock=std::chrono::steady_clock;
  const auto t=Clock::time_point(std::chrono::milliseconds(1000));
  assert(gInfinityTouchStore.load()==nullptr);
  InfinityTouchClearForAction(&first);InfinityTouchForget(&first);
  assert(gInfinityTouchStore.load()==nullptr); // Ordinary controls never allocate.
  assert(InfinityTouchPress(&first,"A",true,false,t)==D::SelectOnly);
  assert(InfinityTouchPress(&first,"A",true,false,t)==D::Activate);
  assert(InfinityTouchPress(&first,"A",true,false,t)==D::SelectOnly);
  InfinityTouchClearForAction(&first);
  assert(InfinityTouchPress(&first,"A",true,false,t)==D::SelectOnly);
  assert(InfinityTouchPress(&first,"B",false,false,t)==D::SelectOnly);
  assert(InfinityTouchPress(&first,"B",true,false,t)==D::Activate);
  assert(InfinityTouchPress(&first,"B",true,true,t)==D::Context);
  InfinityTouchClearForAction(&first); // Native context dispatch retains release suppression.
  assert(InfinityTouchPress(&first,"B",true,false,t+std::chrono::milliseconds(500))==D::SelectOnly);
  assert(InfinityTouchPress(&first,"B",true,false,t+std::chrono::milliseconds(601))==D::SelectOnly);
  assert(InfinityTouchPress(&first,"B",true,false,t+std::chrono::milliseconds(602))==D::Activate);
  assert(InfinityTouchPress(&second,"A",true,false,t)==D::SelectOnly);
  InfinityTouchForget(&second);
  assert(InfinityTouchPress(&second,"A",true,false,t)==D::SelectOnly); // Reused address is fresh.
  assert(InfinityTouchPress(&second,"",true,false,t)==D::SelectOnly);
  assert(InfinityTouchPress(&second,"",true,false,t)==D::SelectOnly);
  std::vector<std::thread> threads;
  for(int i=0;i<4;++i)threads.emplace_back([&] {
    for(int j=0;j<1000;++j) {
      InfinityTouchPress(&first,"A",true,false,t);
      InfinityTouchClearForAction(&first);InfinityTouchForget(&first);
    }
  });
  for(auto& thread:threads)thread.join();
  InfinityTouchForget(&first);InfinityTouchForget(&second);
  assert(gInfinityTouchStore.load()->pairs.empty());
  std::cout<<"state external; tap pairs, remote reset, hold release, destruction/address reuse and concurrent cleanup passed\n";
}
