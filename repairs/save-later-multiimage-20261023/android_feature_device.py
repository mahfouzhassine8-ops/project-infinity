"""Feature-only transport for a disposable emulator; no shutdown driver import."""
import json
import shlex
import socket
import subprocess
import time

PACKAGE='com.projectinfinity.kodi'
PRIVATE='/data/user/0/'+PACKAGE
PROFILE='/sdcard/Android/data/'+PACKAGE+'/files/.kodi/userdata'
FORBIDDEN=('CLOSE_KODI','InfinityPowerControlActivity','force-stop','Application.Quit',
           'System.Shutdown','Powerdown(','Quit(','pm clear','pm uninstall','reboot')

def guard(parts):
    command=' '.join(map(str,parts))
    if any(token.casefold() in command.casefold() for token in FORBIDDEN):
        raise RuntimeError('Feature-only transport rejects termination/reset: '+command)

def adb(*args,check=True,binary=False):
    guard(args)
    result=subprocess.run(['adb',*map(str,args)],capture_output=True,text=not binary,timeout=90)
    if check and result.returncode:
        raise RuntimeError('ADB failed: '+str(args[:3])+': '+str(result.stderr)[-1000:])
    return result.stdout

def shell(*args,check=True):
    guard(args)
    return adb('shell',shlex.join(map(str,args)),check=check)

def read_json(path):
    try:return json.loads(shell('cat',path,check=False))
    except (ValueError,TypeError):return {}

def rpc(method,params=None):
    guard((method,json.dumps(params)))
    request={'jsonrpc':'2.0','id':1,'method':method}
    if params is not None:request['params']=params
    with socket.create_connection(('127.0.0.1',19090),timeout=10) as connection:
        connection.sendall(json.dumps(request).encode())
        pending='';decoder=json.JSONDecoder()
        while True:
            chunk=connection.recv(65536)
            if not chunk:raise RuntimeError('RPC closed without response: '+method)
            pending+=chunk.decode()
            while pending.strip():
                try:response,end=decoder.raw_decode(pending.lstrip())
                except ValueError:break
                pending=pending.lstrip()[end:]
                if response.get('id')==1:
                    if 'error' in response:raise RuntimeError('RPC '+method+': '+json.dumps(response['error']))
                    return response['result']

def until(function,seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=function()
        if value:return value
        time.sleep(.25)
    raise RuntimeError('Feature state was not observed before deadline')

def enable_features(out,versions=None):
    adb('forward','tcp:19090','tcp:9090')
    def ready():
        try:return rpc('JSONRPC.Ping')=='pong'
        except (OSError,RuntimeError):return False
    until(ready,180)
    inventory=rpc('Addons.GetAddons',{'properties':['version','enabled']})
    (out/'addon-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    wanted={'script.infinity.commandcenter':'0.3.5.31',
            'script.infinity.uirepair':'0.1.14','script.infinity.watchedbridge':'1.0.12'}
    if versions is not None:
        if not all(name in versions for name in wanted):raise RuntimeError('Signed component version receipt incomplete')
        wanted={name:versions[name] for name in wanted}
    for name,version in wanted.items():
        details=rpc('Addons.GetAddonDetails',{'addonid':name,'properties':['version','enabled']})['addon']
        if details['version']!=version:raise RuntimeError('Unexpected feature component: '+name)
        if not details['enabled']:
            if rpc('Addons.SetAddonEnabled',{'addonid':name,'enabled':True})!='OK':
                raise RuntimeError('Could not enable feature component: '+name)

def running_engine():
    # Process identity only. No Essential-First participant/save handshake.
    state=read_json(PRIVATE+'/files/infinity-kodi-process.json')
    return state if state.get('phase')=='RUNNING' and isinstance(state.get('pid'),int) else None
