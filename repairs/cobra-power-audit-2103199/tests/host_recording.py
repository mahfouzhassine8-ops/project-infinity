"""Execute extracted recording methods with deterministic fake URL connections.

This tests Java transport/recording decisions, not Android service integration,
provider compatibility, actual socket interruption, or physical-device playback.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess

spec = importlib.util.spec_from_file_location('recording_tools', Path(__file__).resolve().parents[1] / 'apply_timeshift.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def class_member(source, name):
    start = source.index('  private static final class ' + name + ' {')
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def compile_run(source, out):
    text = source.read_text()
    out.mkdir(parents=True, exist_ok=True)
    names = ['record', 'recordDirect', 'recordHls', 'textGet', 'open', 'expired', 'stopSession', 'looksHls', 'fileName']
    if 'class HlsPlaylist' in text:
        names += ['recordingActive', 'recordingHlsAttribute', 'recordingMediaPlaylist']
    methods = '\n'.join(mod.member(text, name) for name in names)
    methods += '\n' + class_member(text, 'Session')
    if 'class HlsPlaylist' in text:
        methods += '\n' + class_member(text, 'HlsPlaylist')
    java = r'''import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class ActualRecordingHarness {
  interface Checked { void run() throws Exception; }
  static int failures, passed;
  static final Map<String, Fixture> routes = new ConcurrentHashMap<>();
  static final List<Connection> connections = Collections.synchronizedList(new ArrayList<>());
  static final String ROOT = "https://provider.invalid/live/";
  static final class Fixture {
    byte[] body; int status = 200, reads, hits; String finalUrl;
    Runnable firstRead, onRequest; boolean failResponse, failRead; int maxChunk = Integer.MAX_VALUE;
    Fixture(byte[] body) { this.body = body; }
  }
  static final class Connection extends HttpURLConnection {
    final Fixture fixture; boolean disconnected;
    Connection(URL url, Fixture fixture) { super(url); this.fixture = fixture; fixture.hits++; if (fixture.onRequest != null) fixture.onRequest.run(); }
    public boolean usingProxy() { return false; }
    public void connect() {}
    public void disconnect() { disconnected = true; }
    public int getResponseCode() throws IOException {
      if (fixture.failResponse) throw new IOException("controlled response failure");
      if (fixture.finalUrl != null) url = new URL(fixture.finalUrl);
      return fixture.status;
    }
    public InputStream getInputStream() {
      return new InputStream() {
        int position; boolean first = true;
        public int read() throws IOException { byte[] b = new byte[1]; int n = read(b, 0, 1); return n < 0 ? -1 : b[0] & 255; }
        public int read(byte[] b, int offset, int count) throws IOException {
          fixture.reads++;
          if (fixture.failRead) throw new IOException("controlled read failure");
          if (position == fixture.body.length) return -1;
          int n = Math.min(count, Math.min(fixture.maxChunk, fixture.body.length - position));
          System.arraycopy(fixture.body, position, b, offset, n); position += n;
          if (first) { first = false; if (fixture.firstRead != null) fixture.firstRead.run(); }
          return n;
        }
      };
    }
  }
  static final class Features {
    File directory; String outcome = "", detail = ""; boolean space = true;
    Features() throws IOException { directory = Files.createTempDirectory("cobra-recordings-").toFile(); }
    File recordingsDir() { return directory; }
    boolean hasRecordingSpace() { return space; }
    void writeHealth(String area, String source, String channel, String state, String detail, int a, int b, int c, String outcome, String more) { this.outcome = outcome; this.detail = detail; }
  }
  final Features features = new Features();
  final ConcurrentHashMap<String, Session> sessions = new ConcurrentHashMap<>();
  int errors, stops;
  ActualRecordingHarness() throws IOException {}
  void notifyError(String text) { errors++; }
  void stopForeground(boolean remove) {}
  void stopSelf() { stops++; }
''' + methods + r'''
  static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
  static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
  static Fixture route(String url, String body) { return route(url, bytes(body)); }
  static Fixture route(String url, byte[] body) { Fixture value = new Fixture(body); routes.put(url, value); return value; }
  static String media(String segment) { return "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\n" + segment + "\n#EXT-X-ENDLIST\n"; }
  static String master(String variant) { return "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\n" + variant + "\n"; }
  static File output() throws IOException { return File.createTempFile("cobra-recording-", ".ts"); }
  static String content(File file) throws IOException { return new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8); }
  static void runHls(ActualRecordingHarness h, String url, File file) throws Exception { h.recordHls(new Session("one"), url, Collections.emptyMap(), file, System.currentTimeMillis() + 250); }
  static void errorContains(Checked action, String text) throws Exception {
    try { action.run(); } catch (Exception error) { check(error.getMessage().contains(text), "wrong error: " + error); return; }
    throw new AssertionError("expected error containing " + text);
  }
  static void test(String name, Checked action) {
    routes.clear(); connections.clear(); Thread.interrupted();
    try { action.run(); passed++; System.out.println("PASS " + name); }
    catch (Throwable error) { failures++; System.out.println("FAIL " + name + ": " + error.getMessage()); }
  }
  static void allDisconnected() { for (Connection c : connections) check(c.disconnected, "connection leaked for " + c.getURL()); }
  public static void main(String[] args) {
    URL.setURLStreamHandlerFactory(protocol -> protocol.equals("http") || protocol.equals("https") ? new URLStreamHandler() {
      protected URLConnection openConnection(URL url) {
        Fixture fixture = routes.get(url.toExternalForm());
        if (fixture == null) { fixture = new Fixture(bytes("missing fixture")); fixture.status = 404; }
        Connection c = new Connection(url, fixture); connections.add(c); return c;
      }
    } : null);
    test("direct media segments retain order and bytes", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      route(ROOT + "media.m3u8", "#EXTM3U\n#EXTINF:2,\na.ts\n#EXTINF:2,\n../b.ts?token=fake\n#EXT-X-ENDLIST\n");
      route(ROOT + "a.ts", "segment-A"); route("https://provider.invalid/b.ts?token=fake", "segment-B");
      runHls(h, ROOT + "media.m3u8", file); check(content(file).equals("segment-Asegment-B"), "media bytes differ"); allDisconnected();
    });
    test("master follows first ordinary variant instead of recording playlist text", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      route(ROOT + "master.m3u8", master("one/media.m3u8") + "#EXT-X-STREAM-INF:BANDWIDTH=2000000\ntwo/media.m3u8\n");
      route(ROOT + "one/media.m3u8", media("one.ts")); route(ROOT + "one/one.ts", "chosen-ts");
      Fixture other = route(ROOT + "two/media.m3u8", media("two.ts"));
      runHls(h, ROOT + "master.m3u8", file); check(content(file).equals("chosen-ts"), "output contains variant playlist text"); check(other.hits == 0, "combined variants"); allDisconnected();
    });
    test("nested masters resolve to media", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      route(ROOT + "master.m3u8", master("nested/next.m3u8")); route(ROOT + "nested/next.m3u8", master("../media.m3u8"));
      route(ROOT + "media.m3u8", media("a.ts")); route(ROOT + "a.ts", "TS");
      runHls(h, ROOT + "master.m3u8", file); check(content(file).equals("TS"), "nested playlist recorded as media");
    });
    test("cyclic master fails without writing playlists", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      route(ROOT + "a.m3u8", master("b.m3u8")); route(ROOT + "b.m3u8", master("a.m3u8"));
      errorContains(() -> runHls(h, ROOT + "a.m3u8", file), "cycle"); check(file.length() == 0, "cycle wrote playlist"); check(connections.size() == 2, "cycle not bounded"); allDisconnected();
    });
    test("master nesting has finite request bound", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      for (int i = 0; i < 10; i++) route(ROOT + i + ".m3u8", master((i + 1) + ".m3u8"));
      errorContains(() -> runHls(h, ROOT + "0.m3u8", file), "nesting"); check(connections.size() == 8, "unexpected master request bound"); check(file.length() == 0, "deep chain wrote playlist");
    });
    test("redirected master and media use final relative URI bases", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      route(ROOT + "master.m3u8", master("variants/media.m3u8")).finalUrl = "https://cdn.invalid/root/master.m3u8";
      route("https://cdn.invalid/root/variants/media.m3u8", media("../chunks/1.ts")).finalUrl = "https://cdn.invalid/session/video/media.m3u8";
      route("https://cdn.invalid/session/chunks/1.ts", "redirected-TS");
      runHls(h, ROOT + "master.m3u8", file); check(content(file).equals("redirected-TS"), "stale redirect base"); allDisconnected();
    });
    test("redirected direct media uses final segment base", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      route(ROOT + "media.m3u8", media("a.ts")).finalUrl = "https://cdn.invalid/media/index.m3u8"; route("https://cdn.invalid/media/a.ts", "TS");
      runHls(h, ROOT + "media.m3u8", file); check(content(file).equals("TS"), "direct media used pre-redirect base");
    });
    test("live polls retain provider entry URL when redirect target changes", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      Fixture entry = route(ROOT + "media.m3u8", media("a.ts").replace("#EXT-X-ENDLIST\n", "")); entry.finalUrl = "https://cdn.invalid/first/media.m3u8";
      entry.onRequest = () -> { if (entry.hits == 2) { entry.finalUrl = "https://cdn.invalid/second/media.m3u8"; entry.body = bytes(media("b.ts")); } };
      route("https://cdn.invalid/first/a.ts", "A"); route("https://cdn.invalid/second/b.ts", "B");
      h.recordHls(new Session("one"), ROOT + "media.m3u8", Collections.emptyMap(), file, System.currentTimeMillis() + 3000);
      check(content(file).equals("AB") && entry.hits == 2, "polling froze redirected URI or lost redirected segments"); allDisconnected();
    });
    test("overlapping live windows do not duplicate completed segments", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      Fixture entry = route(ROOT + "media.m3u8", "#EXTM3U\n#EXT-X-TARGETDURATION:2\na.ts\nb.ts\n");
      entry.onRequest = () -> { if (entry.hits == 2) entry.body = bytes("#EXTM3U\n#EXT-X-TARGETDURATION:2\nb.ts\nc.ts\n#EXT-X-ENDLIST\n"); };
      route(ROOT + "a.ts", "A"); Fixture middle = route(ROOT + "b.ts", "B"); route(ROOT + "c.ts", "C");
      h.recordHls(new Session("one"), ROOT + "media.m3u8", Collections.emptyMap(), file, System.currentTimeMillis() + 3000);
      check(content(file).equals("ABC") && middle.hits == 1, "overlapping window duplicated media"); allDisconnected();
    });
    test("source headers and established timeout policy are preserved", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output();
      route(ROOT + "media.m3u8", media("a.ts")); route(ROOT + "a.ts", "TS"); Map<String,String> headers = new HashMap<>(); headers.put("X-Source-Header", "fake-fixture");
      h.recordHls(new Session("one"), ROOT + "media.m3u8", headers, file, 0);
      for (Connection c : connections) { check(c.getRequestProperty("X-Source-Header").equals("fake-fixture"), "source header lost"); check(c.getRequestProperty("User-Agent").equals("Infinity Cobra DVR/2.0"), "user-agent changed"); check(c.getConnectTimeout() == 15000 && c.getReadTimeout() == 20000 && c.getInstanceFollowRedirects(), "connection policy changed"); } allDisconnected();
    });
    test("cancellation during segment read prevents subsequent writes and reads", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); Session session = new Session("one"); File file = output();
      route(ROOT + "media.m3u8", media("a.ts")); Fixture segment = route(ROOT + "a.ts", new byte[200000]); segment.firstRead = () -> session.cancel.set(true);
      h.recordHls(session, ROOT + "media.m3u8", Collections.emptyMap(), file, 0);
      check(segment.reads == 1 && file.length() == 0, "continued reading/writing after stop: reads=" + segment.reads + ", bytes=" + file.length()); allDisconnected();
    });
    test("cancellation during playlist read prevents subsequent reads and requests", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); Session session = new Session("one"); File file = output();
      Fixture playlist = route(ROOT + "media.m3u8", new byte[30000]); playlist.firstRead = () -> session.cancel.set(true);
      h.recordHls(session, ROOT + "media.m3u8", Collections.emptyMap(), file, 0);
      check(playlist.reads == 1 && connections.size() == 1 && file.length() == 0, "playlist read continued after cancellation"); allDisconnected();
    });
    test("deadline reached inside segment read prevents late output", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", media("a.ts"));
      Fixture segment = route(ROOT + "a.ts", new byte[200000]); segment.firstRead = () -> { try { Thread.sleep(120); } catch (InterruptedException e) { throw new RuntimeException(e); } };
      h.recordHls(new Session("one"), ROOT + "media.m3u8", Collections.emptyMap(), file, System.currentTimeMillis() + 80);
      check(segment.reads == 1 && file.length() == 0, "writes continued past scheduled end"); allDisconnected();
    });
    test("stop during playlist polling is observed within short sleep slices", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); Session session = new Session("one"); h.sessions.put(session.id, session); File file = output(); CountDownLatch read = new CountDownLatch(1); List<Throwable> errors = new ArrayList<>();
      route(ROOT + "media.m3u8", "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\na.ts\n"); route(ROOT + "a.ts", "TS").firstRead = () -> read.countDown();
      Thread worker = new Thread(() -> { try { h.recordHls(session, ROOT + "media.m3u8", Collections.emptyMap(), file, 0); } catch (Throwable e) { errors.add(e); } });
      worker.start(); check(read.await(2, TimeUnit.SECONDS), "recording never read segment"); Thread.sleep(50); long start = System.nanoTime(); h.stopSession("one"); worker.join(750); boolean stopped = !worker.isAlive(); worker.join(2000);
      check(stopped && errors.isEmpty(), "polling stop exceeded 750 ms or threw"); check(TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - start) < 1000, "unexpected stop delay"); check(content(file).equals("TS"), "stop lost completed segment");
    });
    test("encrypted HLS is reported instead of saved as corrupt success", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", media("a.ts").replace("#EXTINF", "#EXT-X-KEY:METHOD=AES-128,URI=\"key.bin\"\n#EXTINF")); Fixture segment = route(ROOT + "a.ts", "encrypted");
      errorContains(() -> runHls(h, ROOT + "media.m3u8", file), "Encrypted"); check(segment.hits == 0 && file.length() == 0, "encrypted bytes written");
    });
    test("METHOD NONE remains supported", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", media("a.ts").replace("#EXTINF", "#EXT-X-KEY:METHOD=NONE\n#EXTINF")); route(ROOT + "a.ts", "TS");
      runHls(h, ROOT + "media.m3u8", file); check(content(file).equals("TS"), "unencrypted media rejected");
    });
    test("initialization map cannot produce misleading TS success", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", media("a.m4s").replace("#EXTINF", "#EXT-X-MAP:URI=\"init.mp4\"\n#EXTINF")); route(ROOT + "a.m4s", "fragment");
      errorContains(() -> runHls(h, ROOT + "media.m3u8", file), "initialization"); check(file.length() == 0, "fragment written without initialization");
    });
    test("byte ranges cannot produce duplicate whole-file success", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", media("a.ts").replace("#EXTINF", "#EXT-X-BYTERANGE:10@0\n#EXTINF")); route(ROOT + "a.ts", "whole-resource");
      errorContains(() -> runHls(h, ROOT + "media.m3u8", file), "byte ranges"); check(file.length() == 0, "range ignored");
    });
    test("external audio rendition is not silently dropped", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "master.m3u8", "#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"aud\",NAME=\"Main\",URI=\"audio.m3u8\"\n#EXT-X-STREAM-INF:BANDWIDTH=1000000,CODECS=\"avc1.4d,mp4a.40.2\",AUDIO=\"aud\"\nvideo.m3u8\n"); route(ROOT + "video.m3u8", media("a.ts")); route(ROOT + "a.ts", "video-only");
      errorContains(() -> runHls(h, ROOT + "master.m3u8", file), "separate audio"); check(file.length() == 0, "claimed success without audio");
    });
    test("in-band audio group remains supported", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "master.m3u8", "#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"aud\",NAME=\"Main\"\n#EXT-X-STREAM-INF:BANDWIDTH=1000000,AUDIO=\"aud\"\nvideo.m3u8\n"); route(ROOT + "video.m3u8", media("a.ts")); route(ROOT + "a.ts", "multiplexed-TS");
      runHls(h, ROOT + "master.m3u8", file); check(content(file).equals("multiplexed-TS"), "in-band audio rejected");
    });
    test("segment HTTP failure does not claim successful completed recording", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", media("missing.ts")); route(ROOT + "missing.ts", "error").status = 503;
      errorContains(() -> runHls(h, ROOT + "media.m3u8", file), "HTTP 503"); check(file.length() == 0, "error body written"); allDisconnected();
    });
    test("segment read exceptions still release connection", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", media("a.ts")); route(ROOT + "a.ts", "TS").failRead = true;
      errorContains(() -> runHls(h, ROOT + "media.m3u8", file), "controlled read"); allDisconnected();
    });
    test("playlist response exceptions still release connection", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "media.m3u8", "").failResponse = true;
      errorContains(() -> runHls(h, ROOT + "media.m3u8", file), "controlled response"); allDisconnected();
    });
    test("cancelled network exception reports stopped and removes session", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); Session session = new Session("one"); h.sessions.put(session.id, session); route(ROOT + "media.m3u8", media("a.ts"));
      Fixture segment = route(ROOT + "a.ts", new byte[200000]); segment.firstRead = () -> { session.cancel.set(true); throw new RuntimeException("cancelled transport"); };
      h.record(session, ROOT + "media.m3u8", "Channel", Collections.emptyMap(), 0, "source", "channel");
      check(h.features.outcome.equals("stopped") && h.errors == 0, "cancellation reported as provider failure"); check(h.sessions.isEmpty() && h.stops == 1, "service/session retained"); allDisconnected();
    });
    test("unsupported format reports existing error path and removes empty file", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); Session session = new Session("one"); h.sessions.put(session.id, session); route(ROOT + "media.m3u8", media("a.ts").replace("#EXTINF", "#EXT-X-KEY:METHOD=AES-128,URI=\"key.bin\"\n#EXTINF")); route(ROOT + "a.ts", "encrypted");
      h.record(session, ROOT + "media.m3u8", "Channel", Collections.emptyMap(), 0, "source", "channel");
      check(h.features.outcome.equals("error") && h.errors == 1 && h.features.detail.contains("unsupported"), "unsupported format not visible as error"); check(h.features.directory.list().length == 0 && h.sessions.isEmpty(), "empty recording/session retained");
    });
    test("direct TS recorder remains byte exact", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); byte[] data = new byte[150000]; for (int i = 0; i < data.length; i++) data[i] = (byte)i;
      route(ROOT + "direct.ts", data); h.recordDirect(new Session("one"), ROOT + "direct.ts", Collections.emptyMap(), file, 0);
      check(Arrays.equals(data, Files.readAllBytes(file.toPath())), "direct TS bytes changed"); check(connections.get(0).getReadTimeout() == 30000, "direct timeout changed"); allDisconnected();
    });
    test("direct response exception releases connection", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); route(ROOT + "direct.ts", "").failResponse = true;
      errorContains(() -> h.recordDirect(new Session("one"), ROOT + "direct.ts", Collections.emptyMap(), file, 0), "controlled response"); allDisconnected();
    });
    test("direct stop during pending read prevents one late chunk write", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); Session session = new Session("one"); File file = output();
      Fixture stream = route(ROOT + "direct.ts", new byte[200000]); stream.firstRead = () -> session.cancel.set(true);
      h.recordDirect(session, ROOT + "direct.ts", Collections.emptyMap(), file, 0);
      check(stream.reads == 1 && file.length() == 0, "direct stream wrote a chunk after cancellation"); allDisconnected();
    });
    test("direct deadline reached inside read prevents late output", () -> {
      ActualRecordingHarness h = new ActualRecordingHarness(); File file = output(); Fixture stream = route(ROOT + "direct.ts", new byte[200000]);
      stream.firstRead = () -> { try { Thread.sleep(120); } catch (InterruptedException e) { throw new RuntimeException(e); } };
      h.recordDirect(new Session("one"), ROOT + "direct.ts", Collections.emptyMap(), file, System.currentTimeMillis() + 80);
      check(stream.reads == 1 && file.length() == 0, "direct stream wrote after scheduled end"); allDisconnected();
    });
    System.out.println("TOTAL passed=" + passed + " failures=" + failures); System.exit(failures == 0 ? 0 : 1);
  }
}
'''
    java_file = out / 'ActualRecordingHarness.java'
    java_file.write_text(java)
    compiled = subprocess.run(['java', 'com.sun.tools.javac.Main', str(java_file)], capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError(compiled.stderr)
    run = subprocess.run(['java', '-cp', str(out), 'ActualRecordingHarness'], capture_output=True, text=True, timeout=90)
    result = {'source': str(source), 'sha256': hashlib.sha256(text.encode()).hexdigest(),
              'kind': 'Host tests on actual extracted Java recording methods with fake HTTP connections; not Android, real-network, codec, or physical-device verification',
              'exit_code': run.returncode, 'output': run.stdout, 'stderr': run.stderr,
              'passed': run.stdout.count('\nPASS ') + int(run.stdout.startswith('PASS ')),
              'failed': run.stdout.count('\nFAIL ') + int(run.stdout.startswith('FAIL '))}
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(compile_run(args.source, args.out)['exit_code'])
