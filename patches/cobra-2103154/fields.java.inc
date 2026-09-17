  // 2103154: five independent presentations; player/guide data ownership stays in 2103153.
  private CobraModeLayout mCobraModeLayout;
  private LinearLayout mCobraModeToolbar,mCobraModeRail,mCobraModeFooter;
  private TextView mCobraModeTitle,mCobraModeSub,mCobraModeEyebrow,mCobraModeDescription,mCobraModeDate;
  private boolean mCobraModeGroupsExpanded=true,mCobraFocusSchedule=false;
  private String mCobraRenderedMode="",mCobraListStateKey="";
  private Channel mCobraInspectedChannel;
  private GuideProgram mCobraInspectedProgram;
  private final LinkedHashMap<String,int[]> mCobraModeScroll=new LinkedHashMap<>();
  private final Map<String,String> mCobraModeFocused=new HashMap<>();
  private String mCobraModePendingFocus="";
  private CobraGuideRuler mCobraGuideRuler;
