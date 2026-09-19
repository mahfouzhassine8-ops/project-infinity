#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re,hashlib

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--patch",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
 checks={
   "default_off":'mPrefs.getBoolean(COBRA_LIVE_REWIND_ENABLED,false)' in text,
   "setting_visible":'LIVE TV REWIND  •  ' in text and 'cobra_live_rewind' in text,
   "rewind_control":'cobra_live_rewind_30' in text and 'cobraRewindLive(30000L)' in text,
   "live_control":'cobra_live_edge' in text and 'cobraGoLive()' in text,
   "restart_current_program":'Restart current program' in text and 'cobraRestartCurrentProgram()' in text,
   "xtream_archive_metadata":'tv_archive' in text and 'tv_archive_duration' in text and 'catchupTimezone' in text,
   "standard_timeshift_endpoint":'"/timeshift/"' in text,
   "seekable_window_guard":'mPlayer.isCurrentMediaItemSeekable()' in text,
   "no_second_player":'new ExoPlayer' not in text[text.index('private static final String COBRA_LIVE_REWIND_ENABLED'):],
   "no_cache_recorder":all(x not in text[text.index('private static final String COBRA_LIVE_REWIND_ENABLED'):] for x in ("SimpleCache","CacheDataSource","TeeDataSource")),
   "screen_2103175_preserved":'cobra-browse-background' in text and 'cobra-browse-safe-content' in text,
   "provider_catchup_explicit_only":'cobraStartProviderCatchup(' in text and 'setMediaItem(mediaItem(url),offset)' in text,
   "native_unchanged":patch.get("native_changed") is False,
   "physical_unverified":patch.get("physical_device_verified") is False,
 }
 failed=[k for k,v in checks.items() if not v]
 out={"passed":not failed,"checks":checks,"failed":failed}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/"source-audit.json").write_text(json.dumps(out,indent=2)+"\n")
 if failed:raise RuntimeError("2103176 source audit failed: "+", ".join(failed))
 print("PASS:",len(checks),"Live TV rewind/catch-up source checks")
if __name__=="__main__":main()
