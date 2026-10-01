from pathlib import Path
import argparse,subprocess,concurrent.futures,re
ap=argparse.ArgumentParser();ap.add_argument('kodi',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
n=a.kodi.resolve()/'lib/libUPnP/Neptune/Source'
cmake=(a.kodi/'lib/libUPnP/CMakeLists.txt').read_text()
src=[n/p for p in sorted(set(re.findall(r'Neptune/Source/([\w/]+\.cpp)',cmake))) if '/Win32/' not in p and p not in ['System/Bsd/NptBsdSockets.cpp']]
# Match the CMake source set, with function section elimination for unexercised APIs.
flags=['-std=c++17','-O1','-g','-pthread','-DINFINITY_SOCKET_POLL_TEST','-DNPT_CONFIG_ENABLE_LOGGING','-ffunction-sections','-fdata-sections','-I'+str(n/'Core'),'-I'+str(n/'System/Bsd'),'-I'+str(n/'System/Posix')]
src.extend([n/'System/StdC/NptStdcFile.cpp', n/'System/StdC/NptStdcConsole.cpp', n/'System/Posix/NptPosixFile.cpp'])
src.append(Path(__file__).parent/'neptune_test.cpp')
def compile(p):
 obj=a.output/(str(p).replace('/','_')+'.o')
 subprocess.run(['c++',*flags,'-c',str(p),'-o',str(obj)],check=True)
 return obj
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:objects=list(ex.map(compile,src))
exe=a.output/'neptune-test'
subprocess.run(['c++','-pthread','-Wl,--gc-sections',*[str(p) for p in objects],'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
