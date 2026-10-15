  // 2103153: presentation/guide state. No Kodi/native owners are replaced.
  private static final long COBRA_GUIDE_TTL_MS = 4L * 60L * 60L * 1000L;
  private final Map<String, CobraEpgData> mCobraEpg = new HashMap<>();
  private final Map<String, String> mCobraEpgStatus = new HashMap<>();
  private final Map<String, String> mCobraEpgRequest = new HashMap<>();
  private final Set<String> mCobraShortEpgBusy = new HashSet<>();
  private final Map<String, Long> mCobraShortEpgAttempt = new HashMap<>();
  private final Map<String, String> mCobraShortEpgStatus = new HashMap<>();
  private final Map<String, String> mCobraResolvedEpg = new HashMap<>();
  private long mCobraGuideWindow = 0L;
  private String mCobraGuideSource = "";
  private String mCobraGuideRoute = "channels";
  private String mCobraGuideStyle = "mobile";
  private FrameLayout mCobraGuideShell;
  private FrameLayout mCobraGuideVideo;
  private LinearLayout mCobraGuideDetails;
  private LinearLayout mCobraGuideBrowser;
  private LinearLayout mCobraGuideDirectory;
  private android.widget.BaseAdapter mCobraGuideAdapter;
  private android.widget.AbsListView mCobraGuideList;
  private android.widget.ProgressBar mCobraGuideProgress;
  private TextView mCobraGuideNowLabel, mCobraGuideNextLabel;
  private int mCobraLastGuideWidth = -1, mCobraLastGuideHeight = -1;
  private long mCobraGuideUiStamp = Long.MIN_VALUE;
  private FrameLayout mCobraActionSheet;
  private String mCobraSheetKind = "";
  private View mCobraSheetPreviousFocus;
  private FrameLayout mCobraPlayerDrawer;
  private String mCobraDrawerFilter = "ALL";
  private android.widget.ListView mCobraPlayerDrawerList;
  private boolean mCobraDrawerGroups = false;
  private int mCobraPlayerUiWidth = -1, mCobraPlayerUiHeight = -1;
  private TextView mCobraPlayerProgram, mCobraPlayerSchedule, mCobraPlayerUpcoming;
  private android.widget.ProgressBar mCobraPlayerProgramProgress;
  private boolean mCobraCreatingMulti = false;
  private final CobraTileStore<CobraVideoTile> mCobraTiles = new CobraTileStore<>();
  private FrameLayout mCobraMultiCanvas;
  private final java.util.IdentityHashMap<ExoPlayer, CobraPlayerBinding> mCobraPlayerBindings =
      new java.util.IdentityHashMap<>();
  private long mCobraPreviewGeneration = 0L;
  private int mCobraLastTickerMinute = -1;
  private final Runnable mCobraPresentationTick = new Runnable() {
    @Override public void run() {
      if (!isCobraAsyncAlive()) return;
      cobraRefreshProgrammeLabels();
      cobraInspectMultiHealth();
      int minute = (int)(System.currentTimeMillis() / 60000L);
      if (minute != mCobraLastTickerMinute) {
        mCobraLastTickerMinute = minute;
        if (mCobraGuideAdapter != null) mCobraGuideAdapter.notifyDataSetChanged();
      }
      if (mCobraPreviewPlayer != null || mPlayer != null || !mCobraTiles.isEmpty())
        mMain.postDelayed(this, 1000L);
    }
  };
  private boolean mCobraPreviewAutoplayAllowed = true;
  private final Map<String,Long> mCobraEpgLastAttempt = new HashMap<>();
  private long mCobraLastCachePrune = 0L;
  private final Runnable mCobraVisibleGuideFetch = () -> cobraFetchVisibleGuides();
