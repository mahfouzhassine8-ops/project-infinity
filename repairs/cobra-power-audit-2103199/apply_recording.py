"""Repair the existing recording paths; no recording UI or policy changes.

Follow ordinary master variants before writing media, resolve relative references
after redirects, reject playlist formats that cannot be concatenated as TS, and
observe the existing cancellation flag between reads and polling sleeps.
Direct TS additionally releases response failures and checks stop/end after reads.
"""
from pathlib import Path
import hashlib
import importlib.util

BASE_SHA256 = '0954e39836038dffe4d60e59899bc3b81e67c85778fc45df44763010b3b118dd'
_spec = importlib.util.spec_from_file_location('recording_source_tools', Path(__file__).with_name('apply_timeshift.py'))
_tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools)

RECORD_DIRECT = r'''  private void recordDirect(Session session, String url, Map<String, String> headers,
                            File output, long endAt) throws Exception {
    HttpURLConnection connection = open(url, headers, 30000);
    try {
      int code = connection.getResponseCode();
      if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);
      try (InputStream raw = new BufferedInputStream(connection.getInputStream());
           BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream(output))) {
        byte[] buffer = new byte[64 * 1024];
        int read;
        while (!session.cancel.get() && !expired(endAt) && (read = raw.read(buffer)) != -1) {
          if (!recordingActive(session, endAt)) break;
          out.write(buffer, 0, read);
          if (!features.hasRecordingSpace()) throw new IllegalStateException("recording storage exhausted");
        }
        out.flush();
      }
    } finally {
      connection.disconnect();
    }
  }'''

RECORD_HLS = r'''  private void recordHls(Session session, String playlistUrl, Map<String, String> headers,
                         File output, long endAt) throws Exception {
    Set<String> seen = new HashSet<>();
    int idleCycles = 0;
    try (BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream(output))) {
      while (recordingActive(session, endAt)) {
        HlsPlaylist page = recordingMediaPlaylist(session, playlistUrl, headers, endAt);
        if (page == null) break;
        String playlist = page.text;
        ArrayList<String> segments = new ArrayList<>();
        double targetSeconds = 4.0;
        for (String raw : playlist.replace("\r", "").split("\n")) {
          String line = raw.trim();
          if (line.startsWith("#EXT-X-KEY:") && !"NONE".equals(recordingHlsAttribute(line.substring(11), "METHOD")))
            throw new IllegalStateException("Encrypted HLS recording is unsupported");
          if (line.startsWith("#EXT-X-MAP:") || line.startsWith("#EXT-X-BYTERANGE:"))
            throw new IllegalStateException("HLS initialization maps and byte ranges are unsupported for TS recording");
          if (line.startsWith("#EXT-X-TARGETDURATION:")) {
            try { targetSeconds = Double.parseDouble(line.substring(line.indexOf(':') + 1)); }
            catch (Exception ignored) {}
          } else if (!line.isEmpty() && !line.startsWith("#")) {
            segments.add(new URL(new URL(page.url), line).toString());
          }
        }
        int wrote = 0;
        for (String segment : segments) {
          if (!recordingActive(session, endAt)) break;
          if (seen.contains(segment)) continue;
          HttpURLConnection c = open(segment, headers, 20000);
          try {
            int code = c.getResponseCode();
            if (code < 200 || code >= 300) throw new IllegalStateException("HLS segment HTTP " + code);
            try (InputStream in = new BufferedInputStream(c.getInputStream())) {
              byte[] buffer = new byte[64 * 1024];
              int read;
              while (recordingActive(session, endAt) && (read = in.read(buffer)) != -1) {
                if (!recordingActive(session, endAt)) break;
                out.write(buffer, 0, read);
                if (!features.hasRecordingSpace()) throw new IllegalStateException("recording storage exhausted");
              }
            }
          } finally {
            c.disconnect();
          }
          if (!recordingActive(session, endAt)) break;
          seen.add(segment);
          wrote++;
        }
        out.flush();
        if (!recordingActive(session, endAt) || playlist.contains("#EXT-X-ENDLIST")) break;
        idleCycles = wrote == 0 ? idleCycles + 1 : 0;
        if (idleCycles > 12) throw new IllegalStateException("HLS playlist stalled");
        long wait = Math.max(1200L, Math.min(6000L, (long) (targetSeconds * 500.0)));
        long remaining = wait;
        while (remaining > 0 && recordingActive(session, endAt)) {
          long slice = Math.min(200L, remaining);
          try { Thread.sleep(slice); }
          catch (InterruptedException stopped) { Thread.currentThread().interrupt(); session.cancel.set(true); break; }
          remaining -= slice;
        }
      }
    }
  }'''

TEXT_GET = r'''  private HlsPlaylist textGet(Session session, String url, Map<String, String> headers,
                              long endAt) throws Exception {
    if (!recordingActive(session, endAt)) return null;
    HttpURLConnection c = open(url, headers, 20000);
    try {
      int code = c.getResponseCode();
      if (code < 200 || code >= 300) throw new IllegalStateException("HLS HTTP " + code);
      try (InputStream in = new BufferedInputStream(c.getInputStream());
           ByteArrayOutputStream out = new ByteArrayOutputStream()) {
        byte[] buffer = new byte[8192];
        int read;
        while (recordingActive(session, endAt) && (read = in.read(buffer)) != -1) {
          if (!recordingActive(session, endAt)) return null;
          if (out.size() + read > 2 * 1024 * 1024) throw new IllegalStateException("HLS playlist too large");
          out.write(buffer, 0, read);
        }
        if (!recordingActive(session, endAt)) return null;
        String text = new String(out.toByteArray(), StandardCharsets.UTF_8);
        if (text.startsWith("\ufeff")) text = text.substring(1);
        if (!text.trim().startsWith("#EXTM3U")) throw new IllegalStateException("Invalid HLS playlist");
        return new HlsPlaylist(c.getURL().toExternalForm(), text);
      }
    } finally {
      c.disconnect();
    }
  }'''

HELPERS = r'''
  private static final class HlsPlaylist {
    final String url, text;
    HlsPlaylist(String url, String text) { this.url = url; this.text = text; }
  }

  private boolean recordingActive(Session session, long endAt) {
    return !session.cancel.get() && !expired(endAt) && !Thread.currentThread().isInterrupted();
  }

  private String recordingHlsAttribute(String attributes, String name) {
    java.util.regex.Matcher value = java.util.regex.Pattern.compile(
        "(?:^|,)\\s*" + name + "=(?:\"([^\"]*)\"|([^,]*))").matcher(attributes);
    return value.find() ? (value.group(1) != null ? value.group(1) : value.group(2)).trim() : "";
  }

  private HlsPlaylist recordingMediaPlaylist(Session session, String url,
                                             Map<String, String> headers, long endAt) throws Exception {
    Set<String> visited = new HashSet<>();
    for (int depth = 0; depth < 8; depth++) {
      if (!visited.add(url)) throw new IllegalStateException("HLS master playlist cycle");
      HlsPlaylist page = textGet(session, url, headers, endAt);
      if (page == null) return null;
      if (!page.url.equals(url) && !visited.add(page.url)) throw new IllegalStateException("HLS redirected playlist cycle");
      String attributes = null, variant = null;
      String[] lines = page.text.replace("\r", "").split("\n");
      for (String raw : lines) {
        String line = raw.trim();
        if (line.startsWith("#EXT-X-STREAM-INF:")) {
          if (attributes != null) throw new IllegalStateException("HLS master variant URI missing");
          attributes = line.substring(18);
        } else if (attributes != null && !line.isEmpty() && !line.startsWith("#")) {
          variant = new URL(new URL(page.url), line).toString(); break;
        }
      }
      if (attributes == null) return page;
      if (variant == null) throw new IllegalStateException("HLS master variant URI missing");
      String audio = recordingHlsAttribute(attributes, "AUDIO");
      if (!audio.isEmpty()) for (String raw : lines) {
        String line = raw.trim();
        if (!line.startsWith("#EXT-X-MEDIA:")) continue;
        String rendition = line.substring(13);
        if ("AUDIO".equals(recordingHlsAttribute(rendition, "TYPE"))
            && audio.equals(recordingHlsAttribute(rendition, "GROUP-ID"))
            && !recordingHlsAttribute(rendition, "URI").isEmpty())
          throw new IllegalStateException("HLS separate audio recording is unsupported");
      }
      url = variant;
    }
    throw new IllegalStateException("HLS master playlist nesting limit");
  }
'''


def transform(text):
    if hashlib.sha256(text.encode()).hexdigest() != BASE_SHA256:
        raise RuntimeError('Recording service does not match the protected baseline')
    for name, replacement in [('recordDirect', RECORD_DIRECT), ('recordHls', RECORD_HLS), ('textGet', TEXT_GET)]:
        start, end = _tools.span(text, name)
        text = text[:start] + replacement + text[end:]
    # A cooperative cancellation is a stopped recording, never a provider failure.
    old = '''      features.writeHealth("recording", sourceId, channelId, "idle",
          e.getClass().getSimpleName() + ": " + e.getMessage(), 0, 0, -1, "error", "");
      notifyError("Recording failed • " + name);'''
    new = '''      if (session.cancel.get()) {
        features.writeHealth("recording", sourceId, channelId, "idle", "", 0, 0, -1, "stopped", "");
      } else {
        features.writeHealth("recording", sourceId, channelId, "idle",
            e.getClass().getSimpleName() + ": " + e.getMessage(), 0, 0, -1, "error", "");
        notifyError("Recording failed • " + name);
      }'''
    text = _tools.once(text, old, new, 'recording cancellation outcome')
    end = text.rfind('}')
    return text[:end] + HELPERS + text[end:]
