"""Selected networking checks only. No Kodi launch, user data or shutdown tests."""
from __future__ import annotations
import http.server
import importlib.util
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import unittest

HERE = Path(__file__).resolve().parent
PROBE = Path(os.environ.get('INFINITY_NETWORK_PROBE',
                            '/workspace/scratch/network-family-host/curl_probe'))


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class V6(Server):
    address_family = socket.AF_INET6


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.server.requests.append((self.path, self.headers.get('Host')))
        if self.path == '/deny':
            self.send_response(403)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if self.path in ('/redirect4', '/redirect6'):
            host = '127.0.0.1' if self.path.endswith('4') else '[::1]'
            self.send_response(302)
            self.send_header('Location', f'http://{host}:{self.server.server_port}/end')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        body = ('family=' + str(self.server.address_family) + ';cookie=' +
                self.headers.get('Cookie', '')).encode()
        self.send_response(200)
        self.send_header('Set-Cookie', 'probe=kept; Path=/')
        self.send_header('Content-Length', str(1000000 if self.path == '/slow' else len(body)))
        self.end_headers()
        try:
            if self.path == '/slow':
                for _ in range(100):
                    self.wfile.write(b'x' * 10000)
                    self.wfile.flush()
                    time.sleep(.05)
            else:
                self.wfile.write(body)
        except (OSError, ssl.SSLError):
            pass


class Transport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='infinity-network-tls-')
        cls.ca = Path(cls.temp.name) / 'ca.pem'
        key = Path(cls.temp.name) / 'key.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', str(key), '-out', str(cls.ca), '-days', '1',
                        '-subj', '/CN=network.test', '-addext',
                        'subjectAltName=DNS:network.test'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.v4 = Server(('127.0.0.1', 0), Handler)
        try:
            cls.v6 = V6(('::1', cls.v4.server_port), Handler)
        except OSError as error:
            cls.v4.server_close()
            cls.temp.cleanup()
            raise RuntimeError('IPv6 loopback unavailable; dual-stack checks NOT EXECUTED') from error
        cls.tls = Server(('127.0.0.1', 0), Handler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cls.ca, key)
        cls.sni = []
        ctx.set_servername_callback(lambda _sock, name, _ctx: cls.sni.append(name))
        cls.tls.socket = ctx.wrap_socket(cls.tls.socket, server_side=True)
        for server in (cls.v4, cls.v6, cls.tls):
            server.requests = []
            threading.Thread(target=server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        # Only disposable test HTTP servers, never application shutdown.
        for server in (cls.v4, cls.v6, cls.tls):
            server.shutdown()
            server.server_close()
        cls.temp.cleanup()

    def probe(self, modes, path='/', addresses='[::1],127.0.0.1', host='network.test',
              tls=False, proxy='', cancel=False, url=None):
        port = self.tls.server_port if tls else self.v4.server_port
        url = url or f'{"https" if tls else "http"}://{host}:{port}{path}'
        resolved = f'{host}:{port}:{addresses}' if addresses else ''
        output = subprocess.check_output([str(PROBE), modes, url, resolved,
                                          str(self.ca) if tls else '', proxy,
                                          'cancel' if cancel else '', 'selected'],
                                         text=True, timeout=12)
        return [json.loads(line) for line in output.splitlines()]

    def test_auto_uses_working_ipv6(self):
        row, = self.probe('0')
        self.assertEqual((row['result'], row['family']), (0, 6))

    def test_auto_falls_back_after_ipv6_connection_refused(self):
        # A refused IPv6 endpoint is a genuine connection failure, not an HTTP error.
        row, = self.probe('0', addresses='[::2],127.0.0.1')
        self.assertEqual((row['result'], row['family']), (0, 4))
        self.assertLess(row['elapsed'], 1.5)

    def test_v4_only_dual_stack(self):
        row, = self.probe('4')
        self.assertEqual((row['result'], row['family']), (0, 4))

    def test_v6_only_dual_stack(self):
        row, = self.probe('6')
        self.assertEqual((row['result'], row['family']), (0, 6))

    def test_only_mode_without_matching_address_fails(self):
        for mode, addresses in [('4', '[::1]'), ('6', '127.0.0.1')]:
            with self.subTest(mode=mode):
                row, = self.probe(mode, addresses=addresses)
                self.assertNotEqual(row['result'], 0)

    def test_opposite_numeric_literals_and_mapped_v6_rejected(self):
        port = self.v4.server_port
        for mode, host in [('4', '[::1]'), ('6', '127.0.0.1'),
                           ('6', '[::ffff:127.0.0.1]')]:
            with self.subTest(mode=mode, host=host):
                row, = self.probe(mode, addresses='', url=f'http://{host}:{port}/')
                self.assertNotEqual(row['result'], 0)

    def test_redirect_cannot_escape_only_mode(self):
        for mode, path in [('4', '/redirect6'), ('6', '/redirect4')]:
            with self.subTest(mode=mode):
                row, = self.probe(mode, path)
                self.assertNotEqual(row['result'], 0)

    def test_pool_mode_change_preserves_cookies_and_reuses_same_mode(self):
        rows = self.probe('4,6,6,0')
        self.assertEqual([r['result'] for r in rows], [0, 0, 0, 0])
        self.assertEqual([r['family'] for r in rows[:3]], [4, 6, 6])
        self.assertEqual([r['fresh'] for r in rows], [True, True, False, True])
        self.assertTrue(all(r['cookie'] for r in rows[1:]))

    def test_https_sni_and_host_verification(self):
        row, = self.probe('4', addresses='127.0.0.1', tls=True)
        self.assertEqual(row['result'], 0)
        self.assertIn('network.test', self.sni)
        self.assertEqual(self.tls.requests[-1][1], f'network.test:{self.tls.server_port}')
        row, = self.probe('4', addresses='127.0.0.1', host='wrong.test', tls=True)
        self.assertEqual(row['result'], 60)  # Peer/hostname verification retained.

    def test_http_rejection_does_not_trigger_family_retry(self):
        before = sum(len(x.requests) for x in (self.v4, self.v6))
        row, = self.probe('0', '/deny')
        self.assertEqual(row['result'], 22)
        self.assertEqual(sum(len(x.requests) for x in (self.v4, self.v6)) - before, 1)

    def test_http_proxy_family_is_local_hop(self):
        port = self.v4.server_port
        proxy = f'http://127.0.0.1:{port}'
        row, = self.probe('4', addresses='', url='http://unresolved-origin.invalid/resource', proxy=proxy)
        self.assertEqual((row['result'], row['family']), (0, 4))
        self.assertEqual(self.v4.requests[-1][0], 'http://unresolved-origin.invalid/resource')
        row, = self.probe('6', addresses='', url='http://unresolved-origin.invalid/resource', proxy=proxy)
        self.assertNotEqual(row['result'], 0)

    def test_cancellation_stops_active_transfer(self):
        row, = self.probe('4', '/slow', cancel=True)
        self.assertEqual(row['result'], 42)
        self.assertLess(row['elapsed'], 1.5)

    def test_dns_failure_is_bounded(self):
        row, = self.probe('0', addresses='', host='infinity-test-no-such-name.invalid')
        # Resolvers may return NXDOMAIN or fail to answer. Both must terminate;
        # this does not claim the environment produced a specific DNS response.
        self.assertIn(row['result'], (6, 28))
        self.assertEqual(row['family'], 0)
        self.assertLess(row['elapsed'], 3.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
