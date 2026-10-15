#!/usr/bin/env python3
"""Execute the real short-EPG request/cache method with structured JSON/network doubles.

This exercises changed request and cache control flow, not Android JSON parsing,
real Xtream credentials, network authentication or device playback.
"""
from pathlib import Path
import argparse,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT.parent))
from apply_epg_repair import span,digest
ADAPTERS=r'''
  // Structured transport/JSON doubles: supplied entries represent a decoded provider payload.
  static final Map<String,JSONArray> payloads=new HashMap<>();
  static class JSONObject {
    Map<String,Object> values=new HashMap<>();JSONArray entries;
    JSONObject(){}JSONObject(String key){entries=payloads.get(key);if(entries==null)throw new IllegalArgumentException("Unknown test payload");}
    JSONObject put(String key,Object v){values.put(key,v);return this;}
    JSONArray optJSONArray(String key){return "epg_listings".equals(key)?entries:null;}
    String optString(String key,String def){Object v=values.get(key);return v==null?def:v.toString();}
    long optLong(String key,long def){Object v=values.get(key);return v instanceof Number?((Number)v).longValue():def;}
  }
  static class JSONArray {List<JSONObject> entries=new ArrayList<>();JSONArray add(JSONObject v){entries.add(v);return this;}int length(){return entries.size();}JSONObject optJSONObject(int i){return entries.get(i);}}
  private String xtreamUrl(LiveSource source,String action){return source.epgUrl+"?action="+action;}
  private String enc(String value){return java.net.URLEncoder.encode(value,StandardCharsets.UTF_8);}
  private String httpGet(String address)throws Exception{requested.add(address);Response response=responses.get(address);if(response==null||response.code!=200)throw new IOException("Injected provider failure");return new String(response.body,StandardCharsets.UTF_8);}
  private String shortUrl(LiveSource source){return xtreamUrl(source,"get_short_epg")+"&stream_id=1&limit=24";}
  private void shortReply(LiveSource source,long now,String title){JSONArray array=new JSONArray();array.add(new JSONObject().put("title",java.util.Base64.getEncoder().encodeToString(bytes(title))).put("description","").put("start_timestamp",now/1000-1).put("stop_timestamp",now/1000+60));array.add(new JSONObject().put("title","Next show").put("start_timestamp",now/1000+60).put("end_timestamp",now/1000+120));String key="payload"+payloads.size();payloads.put(key,array);responses.put(shortUrl(source),new Response(200,bytes(key)));}
'''
CASES=r'''
  public static void main(String[] args)throws Exception {
    routeHttp();
    runCase("S01","Decoded short schedule supplies current and next with saved cache",h->{LiveSource s=h.source();long n=System.currentTimeMillis();h.shortReply(s,n,"Short live");Channel c=channel("fixture:1","News","a");h.cobraRequestShortEpg(c);h.drain();require(h.cobraCurrentProgram(c).title.equals("Short live")&&h.cobraNextProgram(c).title.equals("Next show")&&h.cobraReadEpgCache("@short:"+c.id,h.cobraEpgIdentity(s))!=null,"Short schedule integration failed");});
    runCase("S02","Forced short refresh bypasses complete current schedule and saved cache",h->{LiveSource s=h.source();long n=System.currentTimeMillis();Channel c=channel("fixture:1","News","a");h.shortReply(s,n,"Old");h.cobraRequestShortEpg(c);h.drain();h.shortReply(s,n,"New");h.mCobraForceEpg.add("@short:"+c.id);h.cobraRequestShortEpg(c);h.drain();require(h.cobraCurrentProgram(c).title.equals("New"),"Forced short refresh reused old complete data");});
    runCase("S03","Failed forced short refresh retains its last successful disk snapshot",h->{LiveSource s=h.source();long n=System.currentTimeMillis();Channel c=channel("fixture:1","News","a");h.shortReply(s,n,"Saved");h.cobraRequestShortEpg(c);h.drain();long fetched=h.cobraReadEpgCache("@short:"+c.id,h.cobraEpgIdentity(s)).fetched;responses.clear();h.mCobraForceEpg.add("@short:"+c.id);h.cobraRequestShortEpg(c);h.drain();CobraEpgData d=h.cobraReadEpgCache("@short:"+c.id,h.cobraEpgIdentity(s));require(d!=null&&d.fetched==fetched,"Short failure destroyed successful snapshot");});
    runCase("S04","Disabled source launches no short guide request",h->{h.source();h.mFeatures.enabled=false;h.cobraRequestShortEpg(channel("fixture:1","News","a"));require(h.io.isEmpty(),"Disabled short request queued");});
    runCase("S05","Expired coverage in a recently fetched short snapshot triggers transport",h->{LiveSource s=h.source();long n=System.currentTimeMillis();Channel c=channel("fixture:1","News","a");CobraEpgData d=h.data(s);d.programs.put("@stream:"+c.id,rows(p("@stream:"+c.id,n-120000,n-60000,"Expired")));h.cobraWriteEpgCache("@short:"+c.id,d);h.shortReply(s,n,"Current");h.cobraRequestShortEpg(c);h.drain();require(requested.contains(h.shortUrl(s))&&h.cobraCurrentProgram(c).title.equals("Current"),"Expired short cache blocked current schedule");});
    runCase("S06","Changed guide identity is not blocked by old short retry or complete schedule",h->{LiveSource old=h.source();long n=System.currentTimeMillis();Channel c=channel("fixture:1","News","a");h.shortReply(old,n,"Old source");h.cobraRequestShortEpg(c);h.drain();LiveSource fresh=new LiveSource(old.id,"https://fixture.invalid/new.xml");h.mSources.set(0,fresh);h.shortReply(fresh,n,"New source");h.cobraRequestShortEpg(c);h.drain();require(h.cobraCurrentProgram(c).title.equals("New source")&&h.mCobraEpg.get(old.id).identity.equals(h.cobraEpgIdentity(fresh)),"Old short identity blocked corrected source");});
    runCase("S07","Source identity change rejects obsolete short response in memory",h->{LiveSource old=h.source();long n=System.currentTimeMillis();Channel c=channel("fixture:1","News","a");h.shortReply(old,n,"Obsolete");h.cobraRequestShortEpg(c);h.mSources.set(0,new LiveSource(old.id,"https://fixture.invalid/new.xml"));h.drain();require(!h.mCobraEpg.containsKey(old.id)&&!h.mCobraShortEpgBusy.contains(c.id),"Obsolete short response published or busy flag stuck");});
    runCase("S08","Duplicate short requests remain coalesced",h->{h.source();Channel c=channel("fixture:1","News","a");h.cobraRequestShortEpg(c);h.cobraRequestShortEpg(c);require(h.io.size()==1,"Duplicate short work queued");});
    runCase("S09","Short refresh closes busy state after a failed provider response",h->{h.source();Channel c=channel("fixture:1","News","a");h.cobraRequestShortEpg(c);h.drain();require(!h.mCobraShortEpgBusy.contains(c.id)&&h.mCobraShortEpgStatus.containsKey(c.id),"Short failure left busy state or hid error");});
    System.out.println("SUMMARY\t"+passed+" passed\t"+failed+" failed\tStructured JSON/HTTP doubles; not live provider acceptance");
    java.nio.file.Files.writeString(java.nio.file.Path.of(args[0]),String.join("\n",resultLines)+"\n");if(failed>0)System.exit(1);
  }
'''
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--host',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=a.source.read_text();java=(a.host/'EpgAuditHarness.java').read_text();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    x,y=span(java,'cobraRequestShortEpg');s,e=span(text,'cobraRequestShortEpg');short_sha=digest(text[s:e]);java=java[:x]+text[s:e]+java[y:]
    x,y=span(java,'main');java=java[:x]+CASES.strip()+java[y:]
    s,e=span(text,'cobraDecodeEpgTitle');at=java.rfind('\n}');java=java[:at]+'\n'+ADAPTERS+'\n'+text[s:e]+java[at:]
    (out/'EpgAuditHarness.java').write_text(java)
    for folder in ('android','org'):shutil.copytree(ROOT/folder,out/folder,dirs_exist_ok=True)
    (out/'android/util/Base64.java').write_text('package android.util;public class Base64 {public static final int DEFAULT=0;public static byte[] decode(String s,int flags){return java.util.Base64.getDecoder().decode(s);}}')
    (out/'classes').mkdir(exist_ok=True)
    subprocess.run(['javac','-encoding','UTF-8','-d',str(out/'classes')]+[str(f) for f in out.rglob('*.java')],check=True)
    r=subprocess.run(['java','-Xmx768m','-cp',str(out/'classes'),'EpgAuditHarness',str(out/'results.tsv')],capture_output=True,text=True)
    (out/'output.txt').write_text(r.stdout+r.stderr);print(r.stdout);print(r.stderr,file=sys.stderr)
    report={'source_sha256':digest(text),'short_method_sha256':short_sha,'title_decoder_sha256':digest(text[s:e]),'exit_code':r.returncode,'device_verified':False,'transport_and_json':'structured doubles; actual JSON decoder/network not exercised'}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(r.returncode)
if __name__=='__main__':main()
