  // TEST DOUBLES: model/provider endpoints, preferences, thread queues, widgets and ticker.
  // Real extracted code below supplies parsing, cache format, resolution, refresh, HTTP handling.
  private static final long COBRA_GUIDE_TTL_MS=4L*60*60*1000;
  private boolean mCobraAsyncDestroyed=false;
  private final Map<String,CobraEpgData> mCobraEpg=new HashMap<>();
  private final Map<String,String> mCobraEpgStatus=new HashMap<>(),mCobraEpgRequest=new HashMap<>(),mCobraResolvedEpg=new HashMap<>(),mCobraShortEpgStatus=new HashMap<>();
  private final Map<String,Long> mCobraEpgLastAttempt=new HashMap<>(),mCobraShortEpgAttempt=new HashMap<>();
  private final Map<String,ArrayList<GuideProgram>> mGuidePrograms=new HashMap<>();
  private final Set<String> mCobraShortEpgBusy=new HashSet<>();
  private final ArrayList<LiveSource> mSources=new ArrayList<>();
  private final FakePrefs mPrefs=new FakePrefs();private final FakeFeatures mFeatures=new FakeFeatures();
  private Channel mGuidePreviewChannel,mPlaying;
  private android.widget.BaseAdapter mCobraGuideAdapter;
  private FakeList mCobraPlayerDrawerList;
  private final LinkedList<Runnable> io=new LinkedList<>(),ui=new LinkedList<>();
  private final File files;private int labels,visibleQueue,shortRequests;
  private final FakeHandler mMain=new FakeHandler();private int mCobraLastTickerMinute=-1;
  private Object mCobraPreviewPlayer,mPlayer;private final Set<String> mCobraTiles=new HashSet<>();
  static final class FakeList {Object getAdapter(){return null;}}
  static final class FakeHandler {final List<Runnable> pending=new ArrayList<>();void removeCallbacks(Runnable r){pending.removeIf(x->x==r);}void postDelayed(Runnable r,long n){pending.add(r);}}
  static final class FakeFeatures {boolean enabled=true;boolean sourceEnabled(String s){return enabled;}}
  static final class FakePrefs {Map<String,String> store=new HashMap<>();String getString(String k,String d){return store.getOrDefault(k,d);}FakePrefs edit(){return this;}FakePrefs putString(String k,String v){store.put(k,v);return this;}void apply(){}}
  static final class LiveSource {
    final String id,type,epgUrl,playlistUrl;LiveSource(String id,String url){this(id,"xtream",url,"https://fixture.invalid/channels.m3u");}
    LiveSource(String id,String type,String url,String playlist){this.id=id;this.type=type;this.epgUrl=url;this.playlistUrl=playlist;}
    // Identity dependencies are deterministic doubles; production hashing and identity checks execute.
    String toJson(){return id+"|"+type+"|"+epgUrl+"|"+playlistUrl;}
  }
  EpgAuditHarness()throws Exception{files=java.nio.file.Files.createTempDirectory("cobra-epg-audit-").toFile();}
  private File getFilesDir(){return files;}
  private boolean isCobraAsyncAlive(){return !mCobraAsyncDestroyed;}
  private boolean submitCobraIo(Runnable r){if(!isCobraAsyncAlive())return false;io.add(r);return true;}
  private void publishCobraUi(Runnable r){if(isCobraAsyncAlive())ui.add(r);}
  private void cobraRefreshProgrammeLabels(){labels++;}
  private void cobraQueueVisibleGuides(){visibleQueue++;}
  private void cobraRequestShortEpg(Channel c){shortRequests++;} // transport not exercised; fallback output is fixture data
  private void cobraPruneShortGuideCache(){}
  private void cobraInspectMultiHealth(){}
  private void toast(String text){}
  private String xtreamEpgUrl(LiveSource s){return s.epgUrl;}
  private void drain(){int budget=100;while(!io.isEmpty()||!ui.isEmpty()){if(--budget==0)throw new AssertionError("queue loop");if(!io.isEmpty())io.removeFirst().run();while(!ui.isEmpty())ui.removeFirst().run();}}
  private void drainUi(){while(!ui.isEmpty())ui.removeFirst().run();}
  private void clean()throws Exception{try(var paths=java.nio.file.Files.walk(files.toPath())){paths.sorted(Comparator.reverseOrder()).forEach(p->{try{java.nio.file.Files.deleteIfExists(p);}catch(IOException e){throw new RuntimeException(e);}});}}
  // Fake HttpURLConnection: never sends traffic to a real provider or external network.
  static final Map<String,Response> responses=new HashMap<>();static final List<String> requested=new ArrayList<>();
  static final class Response {final int code;final byte[] body;Response(int c,byte[] b){code=c;body=b;} }
  static class FakeConnection extends HttpURLConnection {
    final Response reply;boolean closed;FakeConnection(URL u){super(u);requested.add(u.toString());reply=responses.getOrDefault(u.toString(),new Response(503,new byte[0]));}
    public int getResponseCode(){return reply.code;}public InputStream getInputStream(){return new ByteArrayInputStream(reply.body);}
    public void disconnect(){closed=true;}public boolean usingProxy(){return false;}public void connect(){}
  }
  static void routeHttp(){URL.setURLStreamHandlerFactory(protocol->("http".equals(protocol)||"https".equals(protocol))?new URLStreamHandler(){protected URLConnection openConnection(URL u){return new FakeConnection(u);}}:null);}
  static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
  static String time(long n){SimpleDateFormat f=new SimpleDateFormat("yyyyMMddHHmmss Z",Locale.US);f.setTimeZone(TimeZone.getTimeZone("UTC"));return f.format(new Date(n));}
  static String xmlProgramme(String channel,long start,long stop,String title){return "<programme channel=\""+channel+"\" start=\""+time(start)+"\" stop=\""+time(stop)+"\"><title>"+title+"</title></programme>";}
  static String wrap(String s){return "<?xml version=\"1.0\"?><tv>"+s+"</tv>";}
  static String channelXml(String id,String name){return "<channel id=\""+id+"\"><display-name>"+name+"</display-name></channel>";}
  static GuideProgram p(String ch,long start,long stop,String title){GuideProgram p=new GuideProgram();p.channel=ch;p.start=start;p.stop=stop;p.title=title;return p;}
  static ArrayList<GuideProgram> rows(GuideProgram... p){return new ArrayList<>(Arrays.asList(p));}
  static Channel channel(String id,String name,String epg){return new Channel(id,name,"News",epg,"","https://fixture.invalid/stream","",Collections.emptyMap());}
  LiveSource source(){LiveSource s=new LiveSource("fixture","https://fixture.invalid/guide.xml");mSources.add(s);return s;}
  CobraEpgData data(LiveSource s)throws Exception{CobraEpgData d=new CobraEpgData();d.identity=cobraEpgIdentity(s);d.fetched=System.currentTimeMillis();return d;}
  CobraEpgData parse(String s)throws Exception{return cobraParseGuide(new ByteArrayInputStream(bytes(s)));}
  interface Case {void run(EpgAuditHarness h)throws Exception;}
  static int passed,failed;static final List<String> resultLines=new ArrayList<>();
  static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
  static void runCase(String id,String name,Case f)throws Exception{
    EpgAuditHarness h=new EpgAuditHarness();responses.clear();requested.clear();String state="PASS",detail="";
    try{f.run(h);passed++;}catch(AssertionError e){state="FAIL";detail=e.getMessage();failed++;}catch(Exception e){state="ERROR";detail=e.getClass().getSimpleName()+": "+e.getMessage();failed++;}
    finally{h.clean();}
    String line=id+"\t"+state+"\t"+name+"\t"+detail;resultLines.add(line);System.out.println(line);
  }
