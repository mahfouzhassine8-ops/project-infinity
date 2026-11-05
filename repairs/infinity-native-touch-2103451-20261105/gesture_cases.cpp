// Run against extracted real method/dispatcher bodies with mock UI boundaries.
int checks=0,failures=0;
void expect(bool value,const char* name) { ++checks;if(!value){++failures;std::cout<<"FAIL "<<name<<'\n';} }
struct Fixture {
  CGUIBaseContainer view;
  CGUIMediaWindow window;
  CGUIWindow home;
  Fixture(int parent=WINDOW_VIDEO_NAV,int id=50) {
    fixtureGUI.wm=WindowManager{};fixtureSettings.settings=Settings{};fixtureComponents=AppComponents{};
    titleOwnerReady=false;titlePopups.clear();
    view.parentID=parent;view.id=id;
    window.view=id;window.focus=id;window.controls[id]=&view;
    window.directory.path="plugin://plugin.video.fixture/results";
    fixtureGUI.wm.active=parent;fixtureGUI.wm.windows[parent]=&window;
    if(parent!=WINDOW_HOME)fixtureGUI.wm.windows[WINDOW_HOME]=&home;
    for(int i=0;i<2;++i){auto item=std::make_shared<CFileItem>();item->path="plugin://plugin.video.fixture/item"+std::to_string(i);view.m_items.push_back(item);}
    InfinityTouchForget(&view);
  }
  ~Fixture(){InfinityTouchForget(&view);}
  CFileItem& item(int i=0){return *std::static_pointer_cast<CFileItem>(view.m_items[i]);}
  void typed(const std::string& kind="movie"){for(int i=0;i<2;++i){item(i).tagged=true;item(i).tag.m_type=kind;}}
  bool tap(int row=0){return view.OnInfinityMediaTouch(25,50+100*row,false);}
  bool hold(int row=0){return view.OnInfinityMediaTouch(25,50+100*row,true);}
};
int main(){
  {
    Fixture f;
    expect(f.tap() && f.view.actions.empty(),"untyped provider first tap selects only");
    expect(f.tap() && f.view.actions.size()==1 && f.view.actions.back().first==ACTION_SELECT_ITEM,"untyped provider second tap activates once");
    expect(f.view.actions.size()==1 && f.view.actions.back().second==f.item().path,"original selected provider route retained");
  }
  for(const auto& kind:{"movie","tvshow","season","episode"}){
    Fixture f;f.typed(kind);
    expect(f.tap() && f.view.actions.empty(),"typed first tap with existing focus never activates");
    expect(f.tap() && f.view.actions.size()==1,"typed immediate second tap activates without arbitrary lower time bound");
  }
  {
    Fixture f;expect(f.tap(),"arm row0");expect(f.tap(1) && f.view.actions.empty(),"different row needs fresh first tap");
    expect(f.tap(1) && f.view.actions.size()==1 && f.view.actions.back().second==f.item(1).path,"second tap activates actual new row");
  }
  {
    Fixture f(WINDOW_FAVOURITES);f.item().path="favourites://fixture-item";
    expect(f.tap() && f.view.actions.empty(),"native Favorites first tap");
    expect(f.tap() && f.view.actions.size()==1,"native Favorites second tap");
  }
  for(int id:{8109,8609,8709,8809}){
    Fixture f(WINDOW_HOME,id);f.item().favourite=true;
    expect(f.tap() && f.view.actions.empty(),"Home Favorite first tap");
    expect(f.tap() && f.view.actions.size()==1,"Home Favorite second tap");
  }
  {
    Fixture f(WINDOW_HOME,8109);expect(!f.tap() && f.view.actions.empty(),"unmarked Home item retains original fallback");
  }
  {
    Fixture f;f.window.directory.path="sources://video/";f.item().path="/fixture/folder";f.item().m_bIsFolder=true;
    expect(f.tap() && f.view.actions.empty(),"local folder first tap");expect(f.tap() && f.view.actions.size()==1,"local folder second tap");
  }
  {
    Fixture f;f.item().parent=true;f.item().path="..";
    expect(!f.tap() && f.view.actions.empty(),"parent Back row not intercepted");
  }
  {
    Fixture f;expect(f.hold() && f.view.actions.size()==1 && f.view.actions.back().first==ACTION_CONTEXT_MENU,"untyped hold opens native context once");
    expect(f.tap() && f.view.actions.size()==1,"hold release never activates");
  }
  {
    Fixture f;f.typed();f.window.directory.path="plugin://script.infinity.commandcenter/search";titleOwnerReady=true;
    expect(f.hold() && titlePopups.size()==1 && f.view.actions.empty(),"owned title retains authenticated popup context owner");
    expect(f.tap() && f.view.actions.empty(),"owned hold suppresses ghost tap");
  }
  {
    Fixture f;f.view.m_posY=20;f.view.m_cachedTransform.scale=2;f.view.m_cachedTransform.translation=10;
    expect(f.view.OnInfinityMediaTouch(60,350,false) && f.view.selected==1 && f.view.actions.empty(),"transformed coordinates select actual hit row");
    expect(f.view.OnInfinityMediaTouch(60,350,false) && f.view.actions.size()==1,"transformed second tap activates same hit row");
  }
  {
    Fixture f;f.window.view=51;expect(!f.tap(),"inactive view cannot intercept");
    f.window.view=50;fixtureGUI.wm.active=WINDOW_HOME;expect(!f.tap(),"inactive owner cannot intercept");
    fixtureGUI.wm.active=WINDOW_VIDEO_NAV;fixtureGUI.wm.modal=1;expect(!f.tap(),"modal retains input ownership");
    fixtureGUI.wm.modal=WINDOW_INVALID;fixtureSettings.settings.skin="other.skin";expect(!f.tap(),"other skin unchanged");
    fixtureSettings.settings.skin="skin.infinity.diggz";f.view.visible=false;expect(!f.tap(),"hidden view unchanged");
    f.view.visible=true;f.view.disabled=true;expect(!f.tap(),"disabled view unchanged");
    f.view.disabled=false;CGUIControl parent;parent.disabled=true;f.view.ancestor=&parent;expect(!f.tap(),"disabled ancestor unchanged");
    f.view.ancestor=nullptr;f.view.processed=false;expect(!f.tap(),"unprocessed control unchanged");
    f.view.processed=true;f.view.m_gestureActive=true;expect(!f.tap(),"active gesture unchanged");
    f.view.m_gestureActive=false;expect(!f.view.OnInfinityMediaTouch(600,600,false),"out of bounds unchanged");
  }
  {
    Fixture f;f.item().path="";expect(!f.tap(),"empty identity refused");
    f.item().path=std::string(32769,'x');expect(!f.tap(),"oversized identity refused");
    f.item().path="fixture";f.item().file=false;expect(!f.tap(),"non-file row unchanged");
    f.item().file=true;f.window.refuseFocus=true;f.window.focus=99;expect(!f.tap() && f.view.actions.empty(),"failed focus dispatch never activates");
  }
  {
    Fixture f(WINDOW_HOME,8103);f.typed();expect(!f.tap(),"shared row without authenticated opt-in unchanged");
  }
  {
    Fixture f;Event event;
    expect(DispatchActualBlock(event) && f.view.actions.empty(),"actual pre-hover dispatcher first tap consumes");
    expect(DispatchActualBlock(event) && f.view.actions.size()==1,"actual dispatcher second tap activates once");
  }
  {
    Fixture f(WINDOW_FAVOURITES);Event event;expect(DispatchActualBlock(event),"actual dispatcher admits active native Favorites view");
  }
  {
    Fixture f(WINDOW_HOME,8109);f.item().favourite=true;Event event;expect(DispatchActualBlock(event),"actual dispatcher admits Home Favorites");
  }
  {
    Fixture f;Event event;event.touch.pointers=2;expect(!DispatchActualBlock(event),"multiple pointers keep original path");
    event.touch.pointers=1;event.touch.action=999;expect(!DispatchActualBlock(event),"non tap hold keeps original path");
    event.touch.action=ACTION_TOUCH_TAP;fixtureComponents.power->screensaver=true;expect(!DispatchActualBlock(event),"screensaver keeps ownership");
    fixtureComponents.power.reset();expect(!DispatchActualBlock(event),"missing power owner refuses interception");
  }
  {
    Fixture f;CGUIControl button;f.window.controls[50]=&button;Event event;
    expect(!DispatchActualBlock(event),"Close Back Power direct buttons are not media containers");
    expect(f.view.actions.empty(),"media controller never dispatches a direct button");
  }
  std::cout<<checks<<" host assertions, "<<failures<<" failing; mocked UI boundaries, Android NOT RUN.\n";
  return failures?1:0;
}
