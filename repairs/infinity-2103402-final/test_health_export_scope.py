"""Execute actual revised exporter methods; controlled Android/JSON interfaces, not device QA."""
from pathlib import Path
import tempfile,subprocess,json,hashlib,unittest
import health_export_scope as h
ROOT=h.ROOT
SOURCE=ROOT.parents[1]/h.GATE['source']
def method(text,marker):
 start=text.index(marker);p=text.index('{',start);depth=1;i=p+1
 while depth:
  depth+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[start:i]
STUBS=r'''
class JSONObject extends java.util.HashMap<String,Object>{static final Object NULL=new Object(); public JSONObject put(String k,Object v){super.put(k,v);return this;}}
class JSONArray extends java.util.ArrayList<JSONObject>{JSONArray put(JSONObject o){add(o);return this;}}
class Build {static class VERSION {static int SDK_INT=37;}}
class Context {static final String ACTIVITY_SERVICE="activity";java.io.File root;Object manager;
 Context(java.io.File r,Object m){root=r;manager=m;}java.io.File getFilesDir(){return root;}String getPackageName(){return "com.projectinfinity.kodi";}Object getSystemService(String k){return manager;}}
class android {static class app {
 static class ActivityManager {java.util.List<ApplicationExitInfo> entries=new java.util.ArrayList<>(); boolean denied;
 java.util.List<ApplicationExitInfo> getHistoricalProcessExitReasons(String p,int pid,int max){if(denied)throw new SecurityException();return entries;}}
 static class ApplicationExitInfo {static final int REASON_CRASH_NATIVE=5,REASON_ANR=6;int reason,status;java.io.InputStream stream;String process="com.projectinfinity.kodi:kodi";int reads;
 ApplicationExitInfo(int r,int s,java.io.InputStream i){reason=r;status=s;stream=i;}
 int getReason(){return reason;}int getStatus(){return status;}int getPid(){return 9097;}long getTimestamp(){return 1792869738390L;}String getProcessName(){return process;}
 long getPss(){return 0;}long getRss(){if(reason==9)throw new SecurityException("private");return 736256;}int getImportance(){return 100;}
 java.io.InputStream getTraceInputStream(){reads++;return stream;}}
}}
'''
MAIN=r'''
 static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 static class Partial extends InputStream {boolean used,closed;public int read()throws IOException{throw new IOException("private diagnostic text must not be copied into manifest");}
 public int read(byte[] b,int off,int len)throws IOException{if(used)throw new IOException("private");used=true;System.arraycopy(new byte[]{1,2,3,4},0,b,off,4);return 4;}
 public void close(){closed=true;}}
 public static void main(String[] args)throws Exception {
 java.io.File root=new java.io.File(args[0]);root.mkdirs();Context context=new Context(root,null);
 JSONArray rows=new JSONArray();ByteArrayOutputStream bytes=new ByteArrayOutputStream();
 try(ZipOutputStream z=new ZipOutputStream(bytes)){
 attachShutdown(context,z,rows,"missing","missing.txt",16);
 java.nio.file.Files.write(new java.io.File(root,"empty").toPath(),new byte[0]);attachShutdown(context,z,rows,"empty","empty.txt",16);
 java.nio.file.Files.write(new java.io.File(root,"data").toPath(),new byte[]{1,2,3,4});attachShutdown(context,z,rows,"data","data.txt",2);
 }
 check(rows.get(0).get("status").equals("not_present"),"missing");
 check(rows.get(1).get("status").equals("empty_no_evidence")&&rows.get(1).get("available").equals(false),"empty must not claim evidence");
 check(rows.get(2).get("bytes").equals(2)&&rows.get(2).get("truncated").equals(true),"bounded");
 try(java.util.zip.ZipInputStream zin=new java.util.zip.ZipInputStream(new ByteArrayInputStream(bytes.toByteArray()))){check(zin.getNextEntry().getName().equals("data.txt"),"only real evidence");check(zin.readAllBytes().length==2,"payload bound");check(zin.getNextEntry()==null,"valid completed archive");}
 Partial partial=new Partial();Snapshot snap=snapshot(partial,20);check(partial.closed&&snap.data.size()==4&&snap.error.equals("IOException"),"partial retained and closed");
 android.app.ActivityManager manager=new android.app.ActivityManager();context.manager=manager;
 manager.entries.add(new android.app.ApplicationExitInfo(2,7,null));manager.entries.add(new android.app.ApplicationExitInfo(4,0,null));
 manager.entries.add(new android.app.ApplicationExitInfo(6,0,new ByteArrayInputStream(new byte[0])));
 manager.entries.add(new android.app.ApplicationExitInfo(5,0,new Partial()));
 for(int i=0;i<11;i++)manager.entries.add(new android.app.ApplicationExitInfo(5,0,new ByteArrayInputStream(new byte[]{9})));
 rows=new JSONArray();bytes=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(bytes)){Api30.collect(context,z,rows);}
 check(rows.size()==12,"metadata bounded12");check(rows.get(0).get("reason").equals(2)&&rows.get(0).get("exit_status").equals(7),"signal retained honestly");
 check(!rows.get(0).containsKey("format")&&rows.get(0).get("available").equals(false),"signal not fabricated native trace");
 check(rows.get(0).get("rss_kb").equals(736256L)&&rows.get(0).get("pss_kb")==JSONObject.NULL&&rows.get(0).get("importance").equals(100),"OS sample retained; zero PSS is unavailable");
 check(rows.get(1).get("reason").equals(4),"Java retained");check(rows.get(2).get("status").equals("empty_no_evidence"),"empty Android trace");
 check(rows.get(3).get("status").equals("partial_read_failure"),"partial trace marked");
 check(manager.entries.stream().mapToInt(e->e.reads).sum()==4,"trace attempts bounded4");
 check(rows.get(6).get("status").equals("trace_budget_exhausted"),"budget represented");
 manager.entries.clear();manager.entries.add(new android.app.ApplicationExitInfo(9,0,null));
 rows=new JSONArray();try(ZipOutputStream z=new ZipOutputStream(new ByteArrayOutputStream())){Api30.collect(context,z,rows);}
 check(rows.get(0).get("reason").equals(9)&&rows.get(0).get("resource_context_status").equals("unavailable")&&rows.get(0).get("rss_kb")==JSONObject.NULL,"resource failure retains exit identity");
 manager.denied=true;rows=new JSONArray();try(ZipOutputStream z=new ZipOutputStream(new ByteArrayOutputStream())){Api30.collect(context,z,rows);}
 check(rows.get(0).get("status").equals("exit_history_unavailable"),"service failure doesn't abort exporter");
 boolean failed=false;try(ZipOutputStream z=new ZipOutputStream(new OutputStream(){public void write(int b)throws IOException{throw new IOException();}})){attachShutdown(context,z,new JSONArray(),"data","data.txt",16);}catch(IOException wanted){failed=true;}check(failed,"destination failure not swallowed");
 System.out.println("PASS actual Java methods: empty/missing, bounded snapshot, partial input, signal/Java metadata, trace budgets, source failure recovery, destination failure propagation");
 }
'''
class HealthExport(unittest.TestCase):
 def test_actual_java_export_methods(self):
  original=SOURCE.read_bytes();candidate=h.transform(original).decode()
  methods='\n'.join([method(candidate,'  private static void attachShutdown('),method(candidate,'  private static Snapshot snapshot('),method(candidate,'  private static final class Snapshot {'),method(candidate,'  static boolean copyBounded('),method(candidate,'  private static void put('),method(candidate,'  private static final class Api30 {')])
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);code='import java.io.*;import java.util.zip.*;\n'+STUBS+'\npublic class Harness {static final int TRACE_LIMIT=2097152,MAX_TRACES=4;\n'+methods+MAIN+'}\n'
   (p/'Harness.java').write_text(code)
   compiled=subprocess.run(['java','com.sun.tools.javac.Main',str(p/'Harness.java')],capture_output=True,text=True)
   self.assertEqual(compiled.returncode,0,compiled.stderr)
   result=subprocess.run(['java','-cp',td,'Harness',str(p/'data')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertIn('PASS actual Java methods',result.stdout)
 def test_unreviewed_preimage_rejected(self):
  self.assertRaises(ValueError,h.transform,SOURCE.read_bytes()+b' ')
if __name__=='__main__':unittest.main(verbosity=2)
