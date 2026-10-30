package com.projectinfinity.kodi;

import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;

/** Reuses private parsed data only. Current preference values and policy are read on every call. */
public final class CobraProfileDataReuse {
    private static final int MAX_RAW_CHARS = 64 * 1024;
    private static final ThreadLocal<Entry> LOCAL = new ThreadLocal<Entry>();

    private static final class Entry {
        private final String raw;
        private final JSONArray values;
        Entry(String raw, JSONArray values) {
            this.raw = raw;
            this.values = values;
        }
    }

    private CobraProfileDataReuse() {}

    private static JSONArray currentData(SharedPreferences preferences) {
        final String raw;
        try {
            // Keep the original profiles() getter/default and exception behavior.
            raw = preferences.getString("profiles", "[]");
        } catch (Exception failure) {
            LOCAL.remove();
            return new JSONArray();
        }
        boolean admitted = raw != null && raw.length() <= MAX_RAW_CHARS;
        Entry prior = LOCAL.get();
        if (admitted && prior != null && raw.equals(prior.raw)) {
            return prior.values;
        }
        JSONArray values;
        try {
            values = new JSONArray(raw);
        } catch (Exception failure) {
            values = new JSONArray();
        }
        if (admitted) {
            LOCAL.set(new Entry(raw, values));
        } else {
            // Oversize and null input are evaluated normally, without retaining old or large data.
            LOCAL.remove();
        }
        return values;
    }

    public static boolean adultLocked(String activeId, SharedPreferences preferences) {
        JSONArray values = currentData(preferences);
        for (int index = 0; index < values.length(); index++) {
            JSONObject profile = values.optJSONObject(index);
            if (profile != null && activeId.equals(profile.optString("id"))) {
                return profile.optBoolean("adult_locked", false);
            }
        }
        return false;
    }
}
