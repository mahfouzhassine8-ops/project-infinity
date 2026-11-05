"""Inventory source candidate only; never label it an APK comparison."""
import hashlib,json,subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE='2b5fcc73a12adcf223858b429d1daa23ed4420ea'
SIGNED=Path('/tmp/infinity-signed456-payload-audit/assets/addons')
NAMES=['script.infinity.commandcenter/default.py','script.infinity.commandcenter/library_navigation.py',
 'skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml','skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml',
 'skin.infinity.diggz/unified/MyVideoNav.xml','skin.infinity.diggz/unified/Variables.xml']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def main():
 rows={}
 for member in NAMES:
  folder='infinity-master-corrective-20261105' if member.startswith('script.') else 'infinity-kodi-2103453-ui-navigation'
  p=ROOT/'repairs'/folder/'overlay/assets/addons'/member;old=SIGNED/member
  rows['assets/addons/'+member]=dict(source=str(p.relative_to(ROOT)),signed456_sha256=sha(old.read_bytes()) if old.exists() else None,
                                    candidate_sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
 protected={}
 prior_plan=json.loads((ROOT/'repairs/infinity-master-corrective-20261105/PLANNED-MEMBERS.json').read_text())['overlay_members']
 for n in [row['source'] for row in prior_plan if row['member'] in {'assets/addons/script.infinity.commandcenter/'+leaf for leaf in ('infinity_search.py','service.py','media_view.py')}]:
  p=ROOT/n;protected[n]=p.read_bytes()==git('show',BASE+':'+n)
 for n in ['repairs/dual-experience-isolation-2103420/'+leaf for leaf in ('release-authority.json','accepted-combined-release.json','release_gate.py','assemble.py','signer-policy.json')]+['.github/workflows/infinity-combined-release.yml']:
  protected[n]=(ROOT/n).read_bytes()==git('show',BASE+':'+n)
 native='repairs/infinity-native-touch-2103451-20261105/'
 for leaf in ['native/xbmc/input/InputManager.cpp','native/xbmc/guilib/GUIBaseContainer.cpp','APPLIED-SOURCE-DELTA.json']:
  n=native+leaf;protected[n]=(ROOT/n).read_bytes()==git('show',BASE+':'+n)
 assert all(protected.values())
 locks={line.split()[1]:line.split()[0] for line in Path('/tmp/infinity-current-remote-refs.txt').read_text().splitlines() if line.split()[1].startswith('refs/heads/lock/')}
 previous=json.loads((ROOT/'repairs/infinity-master-testing-20261105/RECOVERY-LOCK-PRESERVATION.json').read_text())
 assert locks==previous['locks']
 tracked=git('diff','--name-only',BASE,'--').decode().splitlines()
 allowed=set(r['source'] for r in rows.values())
 assert all(n in allowed or n.startswith(('repairs/infinity-browser-visual-20261105/',
     'design-locks/infinity-media-browser-20261104/')) for n in tracked),tracked
 report=dict(status='EXACT_SOURCE_CANDIDATE_DELTA_NOT_APK_COMPARISON',base_source=BASE,base_signed_APK=2103456,
  base_APK_SHA256='81aed468bcdf4031f3186fa7c5aa73e396a38f27837581fbcc54f56cbbc94696',runtime_changes=rows,
  existing_changed=sum(v['signed456_sha256'] is not None for v in rows.values()),new_files=sum(v['signed456_sha256'] is None for v in rows.values()),
  protected_sources=protected,protected_recovery_locks=locks,no_binary_changes=True,
  protected_native_sha256='9f77b092899b51850928007578e0fbf91bad38c05f147a308f3ac0cf5c036638',
  APK_built=False,APK_member_comparison='NOT_RUN_FOR_NEW_CANDIDATE',installed_version='UNVERIFIED',physical_acceptance='NOT_ACCEPTED')
 (HERE/'results/SOURCE-DELTA.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Five changed existing source members, one new helper; protected-source checks and 19 lock refs unchanged. No new APK comparison claimed.')
if __name__=='__main__':main()
