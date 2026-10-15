#!/usr/bin/env python3
"""Surgical diagnostics-only transforms over the sealed 2103197 Java owners.

No player, source selection, native, UI, or measurement behavior is changed.
"""
from hashlib import sha256
import re

ARCHIVE_PREIMAGE = "23fd8289c405d53e2d2bd9c2d9a85e79db7e26c20f73b2634416304f4bdcba74"
DIAGNOSTICS_PREIMAGE = "1e3669deb9c1f5881d9f5a8c8526b778af1e8b0373cfae195b746d10065ab2cc"


def _preimage(text, expected):
    if sha256(text.encode()).hexdigest() != expected:
        raise ValueError("Diagnostics owner differs from the protected source")


def _once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Diagnostics source anchor drift")
    return text.replace(before, after, 1)


ARCHIVE_PATTERNS = r'''  // Socket errors often omit URI schemes. Keep versions, timestamps and stack frames intact.
  private static final String SOCKET_HOST = "[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?";
  private static final String SOCKET_IP = "(?:(?:[0-9]{1,3}\\.){3}[0-9]{1,3}|\\[[0-9a-f:.]+(?:%[a-z0-9_.-]+)?\\])";
  private static final Pattern SOCKET_ENDPOINT = Pattern.compile("(?i)(?<![a-z0-9_.-])(?:(?:"+SOCKET_HOST+")?/"+SOCKET_IP+"(?::[0-9]{1,5})?|"+SOCKET_IP+":[0-9]{1,5})(?![a-z0-9_.:-])");
  private static final Pattern CONNECT_ENDPOINT = Pattern.compile("(?i)(\\b(?:failed to connect to|unable to connect to|connecting to|connected to)\\s+)[^\\s\\\\\\\"'<>;,]+");
'''

ATTACHMENT_OBSERVER = r'''  private static void addObservedFile(Map<String,String> entries,String name,File root,String relative,int limit,JSONObject metadata){
    addFile(entries,name,root,relative,limit);
    try{
      JSONObject row=new JSONObject();long now=System.currentTimeMillis();row.put("observed_at_ms",now);
      row.put("freshness_basis","filesystem modification time; does not establish event freshness or association with current playback");
      File file=new File(root.getCanonicalFile(),relative);
      if(!file.getCanonicalFile().equals(file.getAbsoluteFile()))row.put("file_state","omitted_noncanonical");
      else if(!file.isFile())row.put("file_state","unavailable");
      else{
        long modified=file.lastModified();row.put("file_state","present");row.put("file_modified_at_ms",modified>0?modified:-1);
        row.put("file_age_ms",modified>0&&modified<=now?now-modified:-1);row.put("source_file_bytes",file.length());
        row.put("text_may_be_truncated",file.length()>limit);
      }
      metadata.put(name,row);
    }catch(Exception unavailable){try{JSONObject row=new JSONObject();row.put("file_state","metadata_unavailable");metadata.put(name,row);}catch(Exception ignored){}}
  }
'''


def transform_archive(text):
    _preimage(text, ARCHIVE_PREIMAGE)
    text = _once(text, "  private CobraDiagnosticArchive() {}",
                 ARCHIVE_PATTERNS + "  private CobraDiagnosticArchive() {}")
    anchor = '    out = URL.matcher(out).replaceAll("[redacted-uri]");'
    return _once(text, anchor, anchor + '\n'
        '    out = CONNECT_ENDPOINT.matcher(out).replaceAll("$1[redacted-endpoint]");\n'
        '    out = SOCKET_ENDPOINT.matcher(out).replaceAll("[redacted-endpoint]");')


def transform_diagnostics(text):
    _preimage(text, DIAGNOSTICS_PREIMAGE)
    anchor = "  private static final AtomicInteger DROPPED=new AtomicInteger();"
    text = _once(text, anchor, anchor + "\n  private static final int EVENT_HISTORY_LIMIT=47;")
    text = _once(text, "while(rows.size()>=47)rows.remove(0);",
                 "while(rows.size()>=EVENT_HISTORY_LIMIT)rows.remove(0);")
    anchor = "          Map<String,String> entries=new LinkedHashMap<>();"
    text = _once(text, anchor, anchor + "\n          JSONObject attachmentMetadata=new JSONObject();")
    # All seven existing bounded attachment reads keep the same targets and limits.
    pattern = r'(\s+)addFile\(entries,("[^"]+"),([^\n]+?),([^\n]+?),([^\n]+?)\);'
    text, count = re.subn(pattern,
        lambda m: m[1] + "addObservedFile(entries," + ",".join(m.groups()[1:]) + ",attachmentMetadata);", text)
    if count != 7:
        raise ValueError("Diagnostics attachment inventory drift")
    anchor = '          manifest.put("event_queue_flushed",eventsFlushed);manifest.put("exported_at_ms",System.currentTimeMillis());manifest.put("diagnostic_events_dropped",DROPPED.get());'
    text = _once(text, anchor, anchor + '''
          manifest.put("event_history_retained_limit",EVENT_HISTORY_LIMIT);
          manifest.put("event_history_policy","latest bounded events; older entries may be evicted even when diagnostic_events_dropped is zero");
          manifest.put("diagnostic_events_dropped_scope","capture, queue, and write failures; excludes normal history eviction");
          manifest.put("attachment_metadata",attachmentMetadata);''')
    anchor = "  private static void addFile(Map<String,String> entries,String name,File root,String relative,int limit){"
    return _once(text, anchor, ATTACHMENT_OBSERVER + anchor)
