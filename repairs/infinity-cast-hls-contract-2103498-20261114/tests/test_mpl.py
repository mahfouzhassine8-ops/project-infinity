"""Pinned public Google MPL protocol reproduction, no decoder/physical-TV claim.
Google's library is downloaded for this test only; never copied into the APK.
"""
from pathlib import Path
import hashlib,html,json,re,shutil,subprocess,sys,urllib.request
out=Path(sys.argv[1]).resolve();out.mkdir(exist_ok=True);pin='60b5baf53621d8a39261c780ba36a5b7680807431ca41da551da8b013a0ff7f3'
raw=urllib.request.urlopen('https://www.gstatic.com/cast/sdk/libs/mediaplayer/1.0.0/media_player.js',timeout=30).read();assert hashlib.sha256(raw).hexdigest()==pin
source=raw.decode();needle='}).call(window);';assert source.count(needle)==1
# Expose only the actual private protocol class to inspect its metadata after
# its ORIGINAL network-response callback; parsing/codec selection is unchanged.
source=source.replace(needle,'window.TestMPL={Master:Ho};'+needle)
media=(out/'media.m3u8').read_text();master=(out/'master.m3u8').read_text();expected=re.search(r'CODECS="([^"]+)"',master).group(1)
script='''const cases=INPUT;let results=[];for(const [name,text] of cases){let ready=0,errors=[];const host=new cast.player.api.Host({mediaElement:document.createElement('video'),url:'http://127.0.0.1:8080/media.m3u8'});host.Y=(...a)=>errors.push(a);const protocol=new TestMPL.Master(host,{onManifestReady(){ready++;}},null,null,1,1);protocol.bc.td=host.url;protocol.Gg(text);results.push({name,ready,errors,streams:protocol.Ia.map(s=>s.O)});}document.querySelector('#result').textContent=JSON.stringify(results);'''.replace('INPUT',json.dumps([['unchanged498_media_contract',media],['corrected_actual_master',master]]))
p=out/'mpl-protocol.html';p.write_text('<pre id="result"></pre><script>'+source+'</script><script>'+script+'</script>')
chrome=shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('google-chrome-stable');assert chrome,'Installed Chromium/Chrome required for real public MPL callback'
r=subprocess.run([chrome,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--dump-dom',p.as_uri()],capture_output=True,text=True,timeout=35,check=True)
m=re.search(r'<pre id="result">(.*?)</pre>',r.stdout,re.S);assert m,'Google MPL callback did not run';result=json.loads(html.unescape(m.group(1)));before,after=result
assert before['ready']==after['ready']==1 and not before['errors'] and not after['errors']
assert before['streams'][0]['codecs']=='mp4a.40.2' and before['streams'][0]['codecs']!=expected,'Expected exact498 AAC misclassification'
assert after['streams'][0]['codecs']==expected and after['streams'][0]['codecsProvided'] is True
report=dict(status='PASS_ACTUAL_GOOGLE_MPL_BEFORE_AFTER_CODEC_CONTRACT',Google_public_MPL_sha256=pin,actual_Android_master_sha256=hashlib.sha256(master.encode()).hexdigest(),expected_actual_native_codecs=expected,cases=result,physical_receiver='NOT_TESTED',decoder='NOT_TESTED',limitation='Specific ONN receiver runtime/version and exact owner codec profile unavailable; fixes a causally reproduced public Cast HLS contract defect, not a claim of physical success.')
(out/'GOOGLE-MPL-CONTRACT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');p.unlink();print(json.dumps(report,indent=2))
