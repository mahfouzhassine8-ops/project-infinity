"""Disposable Kodi SDK network observer. Never shipped in the application."""
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

QA = 'script.infinity.networkqa'
CC = 'script.infinity.commandcenter'
PROFILE = Path(xbmcvfs.translatePath('special://profile/addon_data/' + QA))
ROOT = Path(__file__).parent
PROFILE.mkdir(parents=True, exist_ok=True)
EVENTS = []
HITS = []
SERVERS = []
NATIVE_LIBRARY = None


def require(value, label):
    if not value:
        raise RuntimeError(label)


def admitted_url(url, playback=False):
    parts = urlsplit(url.split('|', 1)[0])
    require(parts.username is None and parts.password is None and not parts.fragment, 'NO_URL_CREDENTIALS_OR_FRAGMENT')
    hosts = {'127.0.0.1': SERVERS[0].server_port, '::1': SERVERS[1].server_port,
             '::ffff:127.0.0.1': SERVERS[0].server_port, 'localhost': SERVERS[0].server_port}
    if playback:
        require(parts.scheme == 'http' and parts.hostname in ('127.0.0.1', '::1') and
                parts.port == hosts[parts.hostname] and parts.path in ('/fixture.mp4', '/stalled.mp4'), 'EXACT_REGISTERED_PLAYBACK_FIXTURE')
    elif parts.scheme == 'https':
        require((parts.hostname == 'example.com' and parts.port is None and parts.path == '/') or
                (parts.hostname == '127.0.0.1' and parts.port == SERVERS[2].server_port), 'FIXED_TLS_CONTROLS_ONLY')
    else:
        require(parts.scheme == 'http' and ((parts.hostname in hosts and parts.port == hosts[parts.hostname]) or
                (parts.hostname == 'infinity-networkqa.invalid' and parts.port is None)), 'FIXED_REGISTERED_NETWORK_QA_ENDPOINTS')


def save(name, value):
    path = PROFILE / name
    tmp = path.with_suffix('.pending')
    tmp.write_text(json.dumps(value, sort_keys=True))
    tmp.replace(path)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_HEAD(self):
        self.serve(False)

    def do_GET(self):
        self.serve(True)

    def serve(self, body):
        self.connection.settimeout(10)
        path = self.path.split('?', 1)[0]
        hit = dict(path=path, family=self.server.address_family,
                   method=self.command, at=time.monotonic(), bytes_sent=0)
        HITS.append(hit)
        del HITS[:-2000]
        if path == '/redirect':
            target = '/echo'
            self.send_response(302)
            self.send_header('Location', target)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if path == '/cross-v4':
            self.send_response(302)
            self.send_header('Location', 'http://127.0.0.1:%d/echo' % SERVERS[0].server_port)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        video = path in ('/fixture.mp4', '/stalled.mp4')
        data = (ROOT / 'fixture.mp4').read_bytes() if video else json.dumps(
            dict(networkqa=True, family=self.server.address_family)).encode()
        status = 403 if path == '/deny' else 200
        first, last = 0, len(data) - 1
        requested = self.headers.get('Range', '')
        if video and requested.startswith('bytes='):
            pair = requested[6:].split('-', 1)
            first = int(pair[0] or 0)
            last = min(int(pair[1]) if pair[1] else last, last)
            status = 206
        self.send_response(status)
        self.send_header('Content-Type', 'video/mp4' if video else 'application/json')
        self.send_header('Content-Length', str(max(0, last - first + 1)))
        self.send_header('Accept-Ranges', 'bytes')
        if status == 206:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (first, last, len(data)))
        self.end_headers()
        if body:
            try:
                if path == '/stalled.mp4':
                    # Bounded server delay; no resolver/socket replacement.
                    hit['delay_enter'] = time.monotonic()
                    time.sleep(8)
                if video:
                    for offset in range(first, last + 1, 8192):
                        chunk = data[offset:min(offset + 8192, last + 1)]
                        self.wfile.write(chunk)
                        self.wfile.flush()
                        hit['bytes_sent'] += len(chunk)
                        hit['last_byte'] = time.monotonic()
                        time.sleep(.04)
                else:
                    self.wfile.write(data[first:last + 1])
            except (BrokenPipeError, ConnectionResetError, socket.timeout):
                pass


class IPv6Server(ThreadingHTTPServer):
    address_family = socket.AF_INET6


class Player(xbmc.Player):
    def onAVStarted(self):
        EVENTS.append(dict(event='AVStarted', at=time.monotonic()))

    def onPlayBackStopped(self):
        EVENTS.append(dict(event='Stopped', at=time.monotonic()))

    def onPlayBackError(self):
        EVENTS.append(dict(event='Error', at=time.monotonic()))


PLAYER = Player()


def identity():
    global NATIVE_LIBRARY
    addon = xbmcaddon.Addon(CC)
    root = Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))
    manifest = root / 'INFINITY-MODULES.v1'
    manifest_bytes = manifest.read_bytes()
    skin = xbmcaddon.Addon(xbmc.getSkinDir())
    import ctypes
    if NATIVE_LIBRARY is None:
        NATIVE_LIBRARY = ctypes.CDLL(os.path.join(os.environ['KODI_ANDROID_LIBS'], 'libkodi.so'),
                                    mode=os.RTLD_NOLOAD | os.RTLD_NOW)
    native = NATIVE_LIBRARY.InfinityCommandCenterIdentityV1
    native.argtypes = (ctypes.c_char_p, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t,
                       ctypes.POINTER(ctypes.c_char), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint))
    native.restype = ctypes.c_int
    version, digest, protocol = ctypes.create_string_buffer(49), ctypes.create_string_buffer(65), ctypes.c_uint()
    authenticated = native(str(root).encode(), version, len(version), digest, len(digest), ctypes.byref(protocol))
    return dict(CC=addon.getAddonInfo('version'), CC_path=str(root),
                manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                declared_sources=sum(line.startswith('file\t') for line in manifest_bytes.decode('ascii').splitlines()),
                mode=addon.getSetting('network_family'), skin=skin.getAddonInfo('version'),
                skin_path=skin.getAddonInfo('path'), pid=os.getpid(),
                native_authenticated=authenticated, native_version=version.value.decode(),
                native_manifest=digest.value.decode(), protocol=protocol.value,
                fd_count=len(os.listdir('/proc/self/fd')), thread_count=len(os.listdir('/proc/self/task')))


def action(request):
    name = request['action']
    if name == 'identity':
        return identity()
    if name == 'focus_hub':
        xbmc.executebuiltin('ActivateWindow(1191)')
        for _ in range(30):
            if xbmcgui.getCurrentWindowDialogId() == 11191:
                break
            xbmc.sleep(100)
        window = xbmcgui.Window(11191)
        window.setFocusId(1191105)
        for _ in range(40):
            if window.getFocusId() == 1191105:
                break
            xbmc.sleep(50)
        return dict(window=xbmcgui.getCurrentWindowDialogId(), focus=window.getFocusId(),
                    label=window.getControl(1191105).getLabel())
    if name == 'popup':
        dialog = xbmcgui.getCurrentWindowDialogId()
        if dialog in (0, 9999):
            return dict(title='', label='', focus=0, ready=False)
        window = xbmcgui.Window(dialog)
        title, focus = window.getProperty('Infinity.UI.Title'), window.getFocusId()
        if title != 'Network Connections' or focus != 50:
            return dict(title=title, label='', focus=focus, ready=False)
        # Foreign Window.getControl wrappers have an empty Python vecItems even
        # when the native dialog is populated. Query the actual GUI container.
        count_text = xbmc.getInfoLabel('Container(50).NumItems')
        position_text = xbmc.getInfoLabel('Container(50).CurrentItem')
        label = xbmc.getInfoLabel('Container(50).ListItem.Label')
        count = int(count_text) if count_text.isdigit() else 0
        index = int(position_text) - 1 if position_text.isdigit() else -1
        ready = (0 <= index < count and count == 4 and xbmcgui.getCurrentWindowDialogId() == dialog
                 and window.getProperty('Infinity.UI.Title') == title and window.getFocusId() == 50)
        return dict(title=title, label=label, focus=focus, position=index, count=count, ready=ready)
    if name == 'fetch':
        # Only fixed test servers and public TLS/DNS controls; never credentials.
        url = request['url']
        admitted_url(url)
        start = time.monotonic()
        result = dict(opened=False, bytes=0)
        stream = None
        try:
            stream = xbmcvfs.File(url)
            data = stream.readBytes(4096)
            result.update(opened=bool(data), bytes=len(data))
            if data and b'networkqa' in data:
                result['response'] = json.loads(bytes(data))
        except (OSError, RuntimeError) as error:
            # Only the SDK's explicit file-open failure is a transport result.
            # Programming/SDK failures remain observer errors and block the test.
            if str(error) not in ('Error opening file', 'Error opening file.', 'File is not open', 'File is not open.'):
                raise
            result['error'] = str(error)
        finally:
            if stream is not None:
                stream.close()
        result.update(seconds=time.monotonic() - start, hits=HITS[-20:])
        return result
    if name == 'play':
        admitted_url(request['url'], playback=True)
        item = xbmcgui.ListItem(label='Disposable network transport fixture', path=request['url'])
        item.setMimeType('video/mp4')
        PLAYER.play(request['url'], item)
        return dict(requested=True)
    if name == 'playing':
        playing = PLAYER.isPlaying()
        position, source = None, None
        if playing:
            try:
                position, source = PLAYER.getTime(), PLAYER.getPlayingFile()
            except RuntimeError as error:
                # The SDK can transition between isPlaying and getTime on Stop.
                # Only accept its documented not-playing transition, after recheck.
                if PLAYER.isPlaying() or str(error) not in ('Kodi is not playing any file', 'Kodi is not playing any file.'):
                    raise
                playing = False
        return dict(playing=playing, video=PLAYER.isPlayingVideo(), source=source,
                    time=position, events=EVENTS[-100:], hits=HITS[-30:])
    if name == 'stop':
        PLAYER.stop()
        return dict(requested=True)
    if name == 'close':
        return dict(closing=True)
    raise ValueError('Unknown selected diagnostic action')


def run():
    try:
        for cls, address in ((ThreadingHTTPServer, ('127.0.0.1', 0)), (IPv6Server, ('::1', 0))):
            server = cls(address, Handler)
            server.daemon_threads = True
            SERVERS.append(server)
            threading.Thread(target=server.serve_forever, daemon=True).start()
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.daemon_threads = True
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(str(ROOT / 'server.crt'), str(ROOT / 'server.key'))
        server.socket = tls.wrap_socket(server.socket, server_side=True)
        SERVERS.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        save('ready.json', dict(qa=QA, pid=os.getpid(), identity=identity(),
             ipv4=SERVERS[0].server_port, ipv6=SERVERS[1].server_port, tls=SERVERS[2].server_port))
        monitor, last = xbmc.Monitor(), 0
        while not monitor.abortRequested():
            path = PROFILE / 'request.json'
            if path.exists():
                request = json.loads(path.read_text())
                if request.get('pid') == os.getpid() and request['sequence'] > last:
                    last = request['sequence']
                    reply = dict(pid=os.getpid(), sequence=last)
                    try:
                        reply.update(passed=True, result=action(request))
                    except Exception:
                        reply.update(passed=False, error=traceback.format_exc())
                    save('reply.json', reply)
                    if request['action'] == 'close':
                        break
            monitor.waitForAbort(.1)
    finally:
        for server in SERVERS:
            server.shutdown()
            server.server_close()


run()
