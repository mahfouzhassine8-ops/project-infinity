#!/usr/bin/env python3
"""Post-transform hardening for Cobra Full Feature Candidate 2.

This deliberately wraps the Candidate 2 source transform so the accepted
Candidate 1 baseline and the large feature transform remain independently
reviewable. It fixes multi-provider guide merging, VOD resume/auto-next,
play-behind guide behavior, custom EPG gap filling and live auto-refresh before
we spend a full native build.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import infinity_1_0_9_cobra_full as full
import infinity_1_0_8_deep_rebrand as deep

RELEASE = full.RELEASE
VERSION_CODE = full.VERSION_CODE
LIVE_ACTIVITY = full.LIVE_ACTIVITY


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"{label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"{label}: end marker missing")
    return text[:a] + replacement + text[b:]


def harden_activity(java: str) -> str:
    # All enabled providers may contribute guide data. Candidate 1 intentionally
    # rejected guide callbacks from a non-active source; Candidate 2 must not.
    java = replace_once(
        java,
        "        runOnUiThread(() -> {\n"
        "          if (source != mActiveSource) return;\n"
        "          for (Map.Entry<String, ProgramPair> entry : parsed.entrySet())\n",
        "        runOnUiThread(() -> {\n"
        "          if (!mFeatures.sourceEnabled(source.id)) return;\n"
        "          for (Map.Entry<String, ProgramPair> entry : parsed.entrySet())\n",
        "multi-provider EPG callback",
    )

    # Add episode queue, auto-refresh, stall watchdog and guide-overlay state.
    java = replace_once(
        java,
        '  private String mPlayingVodTitle = "";\n',
        '  private String mPlayingVodTitle = "";\n'
        '  private final ArrayList<VodItem> mEpisodeQueue = new ArrayList<>();\n'
        '  private int mEpisodeQueueIndex = -1;\n'
        '  private AlertDialog mGuideOverlay;\n'
        '  private long mBufferingSince = 0L;\n'
        '  private final Runnable mStallWatchdog = new Runnable() {\n'
        '    @Override public void run() {\n'
        '      if (mPlayer != null && mPlayer.getPlaybackState() == Player.STATE_BUFFERING) {\n'
        '        if (mBufferingSince == 0L) mBufferingSince = System.currentTimeMillis();\n'
        '        if (System.currentTimeMillis() - mBufferingSince >= 12000L) {\n'
        '          mPlaybackRetryCount++;\n'
        '          try { mPlayer.prepare(); mPlayer.play(); } catch (Exception ignored) {}\n'
        '          mBufferingSince = System.currentTimeMillis();\n'
        '        }\n'
        '        mMain.postDelayed(this, 4000L);\n'
        '      } else { mBufferingSince = 0L; }\n'
        '    }\n'
        '  };\n'
        '  private final Runnable mAutoRefresh = new Runnable() {\n'
        '    @Override public void run() {\n'
        '      if (!isFinishing() && mPlayerOverlay == null && mMultiOverlay == null && !mSources.isEmpty())\n'
        '        loadAllEnabledSources(false);\n'
        '      mMain.postDelayed(this, 30L * 60L * 1000L);\n'
        '    }\n'
        '  };\n',
        "Candidate 2 recovery fields",
    )

    java = replace_once(
        java,
        "    if (mSources.isEmpty()) {\n      showWelcome();\n",
        "    mMain.removeCallbacks(mAutoRefresh);\n"
        "    mMain.postDelayed(mAutoRefresh, 30L * 60L * 1000L);\n"
        "    if (mSources.isEmpty()) {\n      showWelcome();\n",
        "Candidate 2 auto refresh start",
    )
    java = replace_once(
        java,
        "    releaseSinglePlayer();\n    releaseMulti();\n    mIo.shutdownNow();\n",
        "    mMain.removeCallbacks(mAutoRefresh);\n"
        "    mMain.removeCallbacks(mStallWatchdog);\n"
        "    mMain.removeCallbacks(mProgressTicker);\n"
        "    releaseSinglePlayer();\n    releaseMulti();\n    mIo.shutdownNow();\n",
        "Candidate 2 callback cleanup",
    )

    # The VOD identity must be assigned *after* closePlayer(), because
    # closePlayer intentionally clears the previous media's resume identity.
    old_vod = '''  private void playVodUrl(VodItem item, String url, String group) {
    mPlayingVodKey = item.sourceId + ":" + item.id; mPlayingVodTitle = item.title; mPendingResumeMs = mPrefs.getLong(mFeatures.profileKey("resume:" + mPlayingVodKey), 0L);
    Channel media = new Channel("vod:" + mPlayingVodKey, item.title, group + " • " + (sourceById(item.sourceId) == null ? "Provider" : sourceById(item.sourceId).name), "", item.icon, url, "", Collections.emptyMap()); playChannel(media);
  }
'''
    new_vod = '''  private void playVodUrl(VodItem item, String url, String group) {
    releaseMulti();
    closePlayer();
    mPlayingVodKey = item.sourceId + ":" + item.id;
    mPlayingVodTitle = item.title;
    mPendingResumeMs = mPrefs.getLong(mFeatures.profileKey("resume:" + mPlayingVodKey), 0L);
    Channel media = new Channel("vod:" + mPlayingVodKey, item.title,
        group + " • " + (sourceById(item.sourceId) == null ? "Provider" : sourceById(item.sourceId).name),
        "", item.icon, url, "", Collections.emptyMap());
    mPlaying = media;
    mPlayingIndex = -1;
    mTriedFallback = false;
    mPlaybackRetryCount = 0;
    openPlayerOverlay(media);
    startSinglePlayer(url);
  }
'''
    java = replace_once(java, old_vod, new_vod, "VOD resume ordering")

    # Track an episode queue and roll straight into the next episode.
    old_episode_click = '''        new AlertDialog.Builder(this).setTitle(item.title).setItems(labels, (d, which) -> { VodItem ep = episodes.get(which); String url = source.server + "/series/" + encPath(source.username) + "/" + encPath(source.password) + "/" + encPath(ep.id) + "." + ep.extension; playVodUrl(ep, url, item.title); }).setNegativeButton("Close", null).show();
'''
    new_episode_click = '''        new AlertDialog.Builder(this).setTitle(item.title).setItems(labels, (d, which) -> {
          mEpisodeQueue.clear(); mEpisodeQueue.addAll(episodes); mEpisodeQueueIndex = which;
          VodItem ep = episodes.get(which);
          String url = source.server + "/series/" + encPath(source.username) + "/" + encPath(source.password) + "/" + encPath(ep.id) + "." + ep.extension;
          playVodUrl(ep, url, item.title);
        }).setNegativeButton("Close", null).show();
'''
    java = replace_once(java, old_episode_click, new_episode_click, "series queue")

    java = replace_once(
        java,
        '          } else if (playbackState == Player.STATE_ENDED) state.setText("ENDED");\n',
        '          } else if (playbackState == Player.STATE_ENDED) {\n'
        '            state.setText("ENDED");\n'
        '            saveVodProgress();\n'
        '            if (!mEpisodeQueue.isEmpty() && mEpisodeQueueIndex + 1 < mEpisodeQueue.size())\n'
        '              mMain.postDelayed(() -> playNextEpisode(), 650L);\n'
        '          }\n',
        "episode auto next",
    )

    # Candidate 2 keeps a small persistent continue-watching catalogue rather
    # than only anonymous per-ID offsets.
    old_progress_start = "  private void saveVodProgress() {\n"
    old_progress_end = "  private void toggleWatchlist(VodItem item) {\n"
    progress = r'''  private void saveVodProgress() {
    if (mPlayer == null || mPlayingVodKey.isEmpty() || mPlaying == null) return;
    try {
      long pos = Math.max(0L, mPlayer.getCurrentPosition());
      long dur = Math.max(0L, mPlayer.getDuration());
      SharedPreferences.Editor editor = mPrefs.edit();
      String offsetKey = mFeatures.profileKey("resume:" + mPlayingVodKey);
      if (dur > 0 && pos > dur * 0.92) editor.remove(offsetKey); else if (pos > 5000) editor.putLong(offsetKey, pos);
      String catalogueKey = mFeatures.profileKey("continue_items");
      JSONArray old;
      try { old = new JSONArray(mPrefs.getString(catalogueKey, "[]")); } catch (Exception e) { old = new JSONArray(); }
      JSONArray next = new JSONArray();
      if (!(dur > 0 && pos > dur * 0.92) && pos > 5000) {
        JSONObject current = new JSONObject();
        current.put("key", mPlayingVodKey);
        current.put("title", mPlayingVodTitle);
        current.put("url", mPlaying.primaryUrl);
        current.put("group", mPlaying.group);
        current.put("position", pos);
        current.put("duration", dur);
        current.put("updated", System.currentTimeMillis());
        next.put(current);
      }
      for (int i = 0; i < old.length() && next.length() < 40; i++) {
        JSONObject item = old.optJSONObject(i);
        if (item == null || mPlayingVodKey.equals(item.optString("key"))) continue;
        next.put(item);
      }
      editor.putString(catalogueKey, next.toString()).apply();
    } catch (Exception ignored) {}
  }

  private void playNextEpisode() {
    if (mEpisodeQueueIndex + 1 >= mEpisodeQueue.size()) return;
    mEpisodeQueueIndex++;
    VodItem ep = mEpisodeQueue.get(mEpisodeQueueIndex);
    LiveSource source = sourceById(ep.sourceId);
    if (source == null) return;
    String url = source.server + "/series/" + encPath(source.username) + "/" +
        encPath(source.password) + "/" + encPath(ep.id) + "." + ep.extension;
    playVodUrl(ep, url, ep.category);
  }

'''
    java = replace_between(java, old_progress_start, old_progress_end,
                           progress + old_progress_end, "continue watching catalogue")

    old_continue = '''  private void showContinueWatching() {
    clearStage("COBRA • CONTINUE WATCHING"); status("Resume positions are stored per profile");
    mStage.addView(text("Continue Watching is populated as you play provider Movies and Series. Open Movies/Series to resume a title from its saved position.", mTheme.muted, 15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1));
  }
'''
    new_continue = r'''  private void showContinueWatching() {
    clearStage("COBRA • CONTINUE WATCHING");
    status("Resume positions are stored per profile");
    ScrollView scroll = new ScrollView(this); LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); scroll.addView(list);
    JSONArray items;
    try { items = new JSONArray(mPrefs.getString(mFeatures.profileKey("continue_items"), "[]")); }
    catch (Exception e) { items = new JSONArray(); }
    for (int i = 0; i < items.length(); i++) {
      JSONObject item = items.optJSONObject(i); if (item == null) continue;
      String key = item.optString("key"), title = item.optString("title", "Continue Watching"), url = item.optString("url"), group = item.optString("group", "On demand");
      long pos = item.optLong("position", 0), dur = item.optLong("duration", 0);
      int pct = dur > 0 ? (int) Math.min(99, (pos * 100L) / dur) : 0;
      Button row = action("▶  " + title + "\\n     " + (pct > 0 ? pct + "% watched" : "Resume")); row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      row.setOnClickListener(v -> playSavedVod(key, title, url, group, pos));
      list.addView(row, new LinearLayout.LayoutParams(-1, dp(70)));
    }
    if (items.length() == 0) list.addView(text("Nothing to resume yet.", mTheme.muted, 15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, dp(140)));
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void playSavedVod(String key, String title, String url, String group, long position) {
    if (url == null || url.isEmpty()) return;
    releaseMulti(); closePlayer();
    mPlayingVodKey = key; mPlayingVodTitle = title; mPendingResumeMs = position;
    Channel media = new Channel("vod:" + key, title, group, "", "", url, "", Collections.emptyMap());
    mPlaying = media; mPlayingIndex = -1; mTriedFallback = false; mPlaybackRetryCount = 0;
    openPlayerOverlay(media); startSinglePlayer(url);
  }
'''
    java = replace_once(java, old_continue, new_continue, "real continue watching")

    # Keep video playing under a guide overlay. Long-pressing a guide row opens
    # the detailed multi-day programme actions already built by Candidate 2.
    java = replace_once(
        java,
        '    guide.setOnClickListener(v -> { closePlayer(); showGuide(); });\n',
        '    guide.setOnClickListener(v -> showGuideOverlay());\n',
        "play-behind guide button",
    )
    guide_overlay = r'''  private void showGuideOverlay() {
    if (mChannels.isEmpty()) return;
    ArrayList<Channel> visible = new ArrayList<>(filteredChannels(false, false));
    String[] labels = new String[visible.size()];
    for (int i = 0; i < visible.size(); i++) {
      Channel channel = visible.get(i); ProgramPair pair = programFor(channel);
      labels[i] = channel.name + (pair != null && !pair.now.isEmpty() ? "\\nNOW • " + pair.now : "") +
          (pair != null && !pair.next.isEmpty() ? "\\nNEXT • " + pair.next : "");
    }
    mGuideOverlay = new AlertDialog.Builder(this)
        .setTitle("Cobra Guide • video continues behind")
        .setItems(labels, (dialog, which) -> playChannel(visible.get(which)))
        .setNeutralButton("FULL GUIDE", (dialog, which) -> { closePlayer(); showGuide(); })
        .setNegativeButton("CLOSE", null)
        .create();
    mGuideOverlay.setOnShowListener(ignore -> mGuideOverlay.getListView().setOnItemLongClickListener((parent, view, position, id) -> {
      showProgramGuide(visible.get(position)); return true;
    }));
    mGuideOverlay.show();
  }

'''
    java = replace_once(java, "  private void showRecordings() {\n",
                        guide_overlay + "  private void showRecordings() {\n",
                        "play-behind guide method")

    # Allow a user-supplied XMLTV source to supplement provider XMLTV. Existing
    # provider entries win; custom guide entries fill missing channel/time data.
    java = replace_once(
        java,
        "        String xml = httpGet(target);\n"
        "        Map<String, ProgramPair> parsed = parseXmlTv(xml);\n"
        "        Map<String, ArrayList<GuideProgram>> programmes = parseXmlTvPrograms(xml);\n",
        "        String xml = httpGet(target);\n"
        "        Map<String, ProgramPair> parsed = parseXmlTv(xml);\n"
        "        Map<String, ArrayList<GuideProgram>> programmes = parseXmlTvPrograms(xml);\n"
        "        String customEpg = mPrefs.getString(\"cobra_custom_epg:\" + source.id, \"\");\n"
        "        if (customEpg != null && !customEpg.trim().isEmpty() && !customEpg.equals(target)) {\n"
        "          try {\n"
        "            String customXml = httpGet(customEpg);\n"
        "            Map<String, ProgramPair> customNow = parseXmlTv(customXml);\n"
        "            Map<String, ArrayList<GuideProgram>> customPrograms = parseXmlTvPrograms(customXml);\n"
        "            for (Map.Entry<String, ProgramPair> entry : customNow.entrySet())\n"
        "              if (!parsed.containsKey(entry.getKey())) parsed.put(entry.getKey(), entry.getValue());\n"
        "            for (Map.Entry<String, ArrayList<GuideProgram>> entry : customPrograms.entrySet())\n"
        "              if (!programmes.containsKey(entry.getKey()) || programmes.get(entry.getKey()).isEmpty())\n"
        "                programmes.put(entry.getKey(), entry.getValue());\n"
        "          } catch (Exception ignored) {}\n"
        "        }\n",
        "custom EPG gap fill",
    )

    java = replace_once(
        java,
        '    Button health = action("COBRA HEALTH SNAPSHOT");\n'
        '    health.setOnClickListener(v -> showError("Cobra diagnostics (redacted)", mFeatures.healthSnapshot()));\n',
        '    Button health = action("COBRA HEALTH SNAPSHOT");\n'
        '    health.setOnClickListener(v -> showError("Cobra diagnostics (redacted)", mFeatures.healthSnapshot()));\n\n'
        '    Button customEpg = action("CUSTOM EPG FOR ACTIVE SOURCE");\n'
        '    customEpg.setOnClickListener(v -> editCustomEpg());\n',
        "custom EPG setting",
    )
    java = replace_once(
        java,
        '    list.addView(health, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n',
        '    list.addView(health, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n'
        '    list.addView(customEpg, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n',
        "custom EPG setting row",
    )
    custom_epg = r'''  private void editCustomEpg() {
    if (mActiveSource == null) { toast("Choose an active source first"); return; }
    EditText input = field("Optional XMLTV URL", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
    input.setText(mPrefs.getString("cobra_custom_epg:" + mActiveSource.id, ""));
    new AlertDialog.Builder(this).setTitle("Custom EPG • " + mActiveSource.name).setView(input)
        .setPositiveButton("SAVE", (d, w) -> {
          String value = input.getText().toString().trim();
          if (!value.isEmpty() && !isHttpUrl(value)) { toast("Use an http:// or https:// XMLTV URL"); return; }
          mPrefs.edit().putString("cobra_custom_epg:" + mActiveSource.id, value).apply();
          loadGuideAsync(mActiveSource); toast(value.isEmpty() ? "Custom EPG cleared" : "Custom EPG saved");
        }).setNegativeButton("Cancel", null).show();
  }

'''
    java = replace_once(java, "  private void playChannel(Channel channel) {\n",
                        custom_epg + "  private void playChannel(Channel channel) {\n",
                        "custom EPG editor")

    # Start/stop a short stall watchdog while Media3 buffers.
    java = replace_once(
        java,
        '          if (playbackState == Player.STATE_BUFFERING) state.setText("BUFFERING");\n',
        '          if (playbackState == Player.STATE_BUFFERING) {\n'
        '            state.setText("BUFFERING");\n'
        '            if (mBufferingSince == 0L) mBufferingSince = System.currentTimeMillis();\n'
        '            mMain.removeCallbacks(mStallWatchdog); mMain.postDelayed(mStallWatchdog, 4000L);\n'
        '          }\n',
        "stall watchdog start",
    )
    java = replace_once(
        java,
        '          else if (playbackState == Player.STATE_READY) {\n',
        '          else if (playbackState == Player.STATE_READY) {\n'
        '            mBufferingSince = 0L; mMain.removeCallbacks(mStallWatchdog);\n',
        "stall watchdog stop",
    )

    return java


def source_phase(source: Path, receipt: Path) -> None:
    full.source_phase(source, receipt)
    live = source.resolve() / LIVE_ACTIVITY
    java = harden_activity(live.read_text(encoding="utf-8"))
    live.write_text(java, encoding="utf-8")
    verify_source(source)
    data = json.loads(receipt.read_text(encoding="utf-8"))
    data.update({
        "multi_provider_epg_merge": True,
        "custom_epg_gap_fill": True,
        "guide_playback_behind_overlay": True,
        "vod_resume_catalogue": True,
        "series_auto_next": True,
        "live_stall_watchdog": True,
        "auto_playlist_refresh_minutes": 30,
    })
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Cobra Full Feature Candidate 2 hardening applied")


def verify_source(source: Path) -> None:
    full.verify_source(source)
    java = (source.resolve() / LIVE_ACTIVITY).read_text(encoding="utf-8")
    for needle in (
        "if (!mFeatures.sourceEnabled(source.id)) return;",
        "playSavedVod(",
        "playNextEpisode()",
        "showGuideOverlay()",
        "cobra_custom_epg:",
        "mStallWatchdog",
        "mAutoRefresh",
        "continue_items",
    ):
        if needle not in java:
            raise RuntimeError("Candidate 2 hardening contract missing: " + needle)
    if 'if (source != mActiveSource) return;' in java[java.find('private void loadGuideAsync'):java.find('private Map<String, ProgramPair> parseXmlTv')]:
        raise RuntimeError("Candidate 1 single-provider EPG guard survived")


def configure_deep() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("source"); p.add_argument("--source", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-source"); p.add_argument("--source", type=Path, required=True)
    p = sub.add_parser("apk"); p.add_argument("--input", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-apk"); p.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "source": source_phase(args.source, args.receipt)
    elif args.cmd == "verify-source": verify_source(args.source); print("PASS: Cobra Candidate 2 hardened source verification")
    elif args.cmd == "apk": configure_deep(); deep.apk_phase(args.input, args.output, args.receipt)
    else: configure_deep(); deep.verify_apk(args.apk); print("PASS: Cobra Candidate 2 hardened APK branding verification")


if __name__ == "__main__":
    main()
