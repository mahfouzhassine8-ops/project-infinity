#!/usr/bin/env python3
"""Native-only transforms. All inputs AND staged outputs are checked before writes."""
from pathlib import Path
import argparse, hashlib, json, re
HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()

def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('Unexpected native preimage: ' + repr(old[:100]))
    return text.replace(old, new, 1)

def convert(text):
    text = re.sub(r'\bfd_set\b', 'InfinitySocketPoll::FdSet', text)
    for old, new in [('FD_ZERO','Clear'),('FD_SET','Add'),('FD_ISSET','Contains'),('select','Wait')]:
        text = re.sub(r'\b'+old+r'\s*\(', 'InfinitySocketPoll::'+new+'(', text)
    return text

def stage(base):
    changes = {}
    def record(path, text):
        changes[path] = text.encode()
    for path, anchor in {
        'xbmc/network/Network.cpp':'/* slightly modified in_ether',
        'xbmc/network/TCPServer.cpp':'using namespace std::chrono_literals;',
        'xbmc/network/AirPlayServer.cpp':'using KODI::UTILITY::CDigest;',
        'xbmc/network/UdpClient.cpp':'using namespace std::chrono_literals;',
        'xbmc/network/Socket.h':'namespace SOCKETS',
        'xbmc/network/Socket.cpp':'using namespace SOCKETS;',
        'xbmc/platform/posix/filesystem/SMBWSDiscoveryListener.cpp':'using namespace WSDiscovery;',
    }.items():
        text = convert((base/path).read_text())
        text = once(text, anchor, '#include "network/InfinitySocketPoll.h"\n\n'+anchor)
        if path.endswith('/Network.cpp'):
            assert text.count('InfinitySocketPoll::Wait(FD_SETSIZE,') == 2
            text = text.replace('InfinitySocketPoll::Wait(FD_SETSIZE,', 'InfinitySocketPoll::Wait(static_cast<intptr_t>(soc) + 1,')
        elif path.endswith('/TCPServer.cpp'):
            text = once(text, '            CLog::Log(LOGERROR, "JSONRPC Server: Accept of new connection failed: {}", errno);',
                '            const int acceptError = errno;\n            delete newconnection;\n            CLog::Log(LOGERROR, "JSONRPC Server: Accept of new connection failed: {}", acceptError);')
            text = once(text, '            if (EBADF == errno)', '            if (EBADF == acceptError)')
        elif path.endswith('/UdpClient.cpp'):
            text = once(text, 'int nfds = (int)(client_socket);', 'int nfds = (int)(client_socket) + 1;')
            text = once(text, '    CLog::Log(UDPCLIENT_DEBUG_LEVEL, "UDPCLIENT: Unable to set socket option.");\n    return false;',
                '    CLog::Log(UDPCLIENT_DEBUG_LEVEL, "UDPCLIENT: Unable to set socket option.");\n    closesocket(client_socket);\n    client_socket = INVALID_SOCKET;\n    return false;')
            text = once(text, '  ioctlsocket(client_socket, FIONBIO, &nonblocking);',
                '  if (ioctlsocket(client_socket, FIONBIO, &nonblocking) == SOCKET_ERROR)\n  {\n    closesocket(client_socket);\n    client_socket = INVALID_SOCKET;\n    return false;\n  }')
            text = once(text, '  StopThread();\n  closesocket(client_socket);',
                '  StopThread();\n  if (client_socket != INVALID_SOCKET)\n  {\n    closesocket(client_socket);\n    client_socket = INVALID_SOCKET;\n  }')
            text = once(text, '  closesocket(client_socket);\n\n  CLog::Log(UDPCLIENT_DEBUG_LEVEL, "UDPCLIENT: Stopped listening.");',
                '  closesocket(client_socket);\n  client_socket = INVALID_SOCKET;\n\n  CLog::Log(UDPCLIENT_DEBUG_LEVEL, "UDPCLIENT: Stopped listening.");')
        elif path.endswith('SMBWSDiscoveryListener.cpp'):
            text = once(text, '      char msgbuf[UDPBUFFSIZE];', '      char msgbuf[UDPBUFFSIZE + 1];')
            text = once(text, "      msgbuf[nbytes] = '\\0';\n      // turn msgbuf into std::string\n      bufferoutput.append(msgbuf, nbytes);\n\n      ParseBuffer(bufferoutput);",
                "      if (nbytes >= 0)\n      {\n        msgbuf[nbytes] = '\\0';\n        bufferoutput.append(msgbuf, nbytes);\n        ParseBuffer(bufferoutput);\n      }")
        record(path, text)
    path = 'xbmc/network/UdpClient.h'
    record(path, once((base/path).read_text(), '  SOCKET client_socket;', '  SOCKET client_socket{INVALID_SOCKET};'))
    path = 'lib/libUPnP/Neptune/Source/System/Bsd/NptBsdSockets.cpp'
    text = (base/path).read_text()
    start = text.index('NPT_Result\nNPT_BsdSocketFd::WaitForCondition(')
    end = text.index('/*----------------------------------------------------------------------\n|   NPT_BsdSocketFd::Cancel', start)
    text = text[:start]+'#include "InfinitySocketPoll.h"\n\n'+convert(text[start:end])+text[end:]
    record(path, text)
    path = 'xbmc/filesystem/DllLibCurl.h'
    text = (base/path).read_text()
    text = once(text, '  CURLMcode multi_timeout(CURLM* multi_handle, long* timeout);',
'''#if defined(TARGET_ANDROID)
  CURLMcode multi_poll(CURLM* multi_handle, int timeout_ms, int* numfds);
#endif
  CURLMcode multi_timeout(CURLM* multi_handle, long* timeout);''')
    record(path, text)
    path = 'xbmc/filesystem/DllLibCurl.cpp'
    text = (base/path).read_text()
    text = once(text, 'CURLMcode DllLibCurl::multi_timeout(CURLM* multi_handle, long* timeout)',
'''#if defined(TARGET_ANDROID)
CURLMcode DllLibCurl::multi_poll(CURLM* multi_handle, int timeout_ms, int* numfds)
{
  return curl_multi_poll(multi_handle, nullptr, 0, timeout_ms, numfds);
}
#endif

CURLMcode DllLibCurl::multi_timeout(CURLM* multi_handle, long* timeout)''')
    record(path, text)
    path = 'xbmc/filesystem/CurlFile.cpp'
    text = (base/path).read_text()
    text = once(text, '  fd_set fdread;\n  fd_set fdwrite;\n  fd_set fdexcep;',
'''#if !defined(TARGET_ANDROID)
  fd_set fdread;
  fd_set fdwrite;
  fd_set fdexcep;
#endif''')
    start = text.index('        int maxfd = -1;', text.index('int8_t CCurlFile::CReadState::FillBuffer'))
    end = text.index('      }\n      break;\n      case CURLM_CALL_MULTI_PERFORM:', start)
    legacy = text[start:end]
    text = text[:start]+'''#if defined(TARGET_ANDROID)
        // libcurl owns its socket set. Do not squeeze it through fd_set.
        // A 200ms upper bound also keeps cancellation responsive. libcurl
        // honours any shorter internal timer and sleeps if it has no sockets.
        int ready = 0;
        const CURLMcode waitResult = g_curlInterface.multi_poll(m_multiHandle, 200, &ready);
        if (waitResult != CURLM_OK)
        {
          CLog::Log(LOGERROR, "CCurlFile::CReadState::{} - multi_poll failed with code {}",
                    __FUNCTION__, static_cast<int>(waitResult));
          return FILLBUFFER_FAIL;
        }
#else
'''+legacy+'''#endif
'''+text[end:]
    record(path, text)
    path = 'xbmc/network/WebServer.cpp'
    text = (base/path).read_text()
    text = once(text, 'struct MHD_Daemon* CWebServer::StartMHD(unsigned int flags, int port)\n{',
'''struct MHD_Daemon* CWebServer::StartMHD(unsigned int flags, int port)
{
#if defined(TARGET_ANDROID)
  // Both TLS and plain HTTP must avoid libmicrohttpd's select backend.
  flags |= MHD_USE_POLL;
#endif''')
    record(path, text)
    return changes

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--receipt',type=Path,required=True); ap.add_argument('--verify',action='store_true'); args=ap.parse_args()
    root=args.source.resolve(); plan=json.loads((HERE/'manifest.json').read_text())
    for path, identity in plan['files'].items():
        if sha((root/path).read_bytes()) != identity['after' if args.verify else 'before']:
            raise SystemExit('Source identity mismatch: '+path)
    if not args.verify:
        changes=stage(root)
        if set(changes) != set(plan['files']): raise SystemExit('Unexpected change inventory')
        for path, data in changes.items():
            if sha(data) != plan['files'][path]['after']: raise SystemExit('Staged output mismatch: '+path)
        header=(HERE/'InfinitySocketPoll.h').read_bytes()
        for path, expected in plan['added'].items():
            if (root/path).exists() or sha(header) != expected: raise SystemExit('New header identity mismatch: '+path)
        for path, data in changes.items(): (root/path).write_bytes(data)
        for path in plan['added']: (root/path).write_bytes(header)
    for path, identity in plan['files'].items():
        if sha((root/path).read_bytes()) != identity['after']: raise SystemExit('Output verification failed: '+path)
    for path, expected in plan['added'].items():
        if sha((root/path).read_bytes()) != expected: raise SystemExit('Header verification failed: '+path)
    receipt={'schema':1,'scope':'native descriptor readiness; no skin changes','base':plan['base_kodi_commit'],'files':plan['files'],'added':plan['added'],'verified':True,'device_tested':False,'descriptor_leak_cause_proven':False}
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('PASS: 13 changed native sources and two identical poll headers; hashes verified')

if __name__ == '__main__': main()
