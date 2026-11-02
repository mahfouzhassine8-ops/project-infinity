package com.projectinfinity.kodi;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.FileDescriptor;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.UUID;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** Preview-only history. Every method is called on the existing decoder worker. */
final class InfinityExternalResume extends SQLiteOpenHelper {
    static final String DATABASE = "infinity_preview_resume_v1.db";
    static final int LIMIT = 1000;
    static final long INTERVAL = 10000;
    private byte[] salt;

    static final class Identity {
        final String uri, file, sample;
        final long size, modified;
        Identity(String uri, String file, String sample, long size, long modified) {
            this.uri = uri; this.file = file; this.sample = sample;
            this.size = size; this.modified = modified;
        }
    }
    static final class Entry {
        final String id;
        final Identity identity;
        final long duration, position;
        Entry(String id, Identity identity, long duration, long position) {
            this.id = id; this.identity = identity; this.duration = duration; this.position = position;
        }
    }
    InfinityExternalResume(Context context) { super(context, DATABASE, null, 1); }
    @Override public void onConfigure(SQLiteDatabase db) { db.setForeignKeyConstraintsEnabled(true); }
    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE secret (value BLOB NOT NULL)");
        byte[] bytes = new byte[32]; new SecureRandom().nextBytes(bytes);
        ContentValues secret = new ContentValues(); secret.put("value", bytes); db.insertOrThrow("secret", null, secret);
        db.execSQL("CREATE TABLE video (id TEXT PRIMARY KEY, position INTEGER NOT NULL, duration INTEGER NOT NULL, size INTEGER NOT NULL, modified INTEGER NOT NULL, file TEXT NOT NULL, sample TEXT NOT NULL, updated INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE alias (key TEXT PRIMARY KEY, video TEXT NOT NULL REFERENCES video(id) ON DELETE CASCADE)");
        db.execSQL("CREATE INDEX alias_video ON alias(video)");
    }
    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        throw new IllegalStateException("No Preview history migration is defined");
    }
    private String key(String value) {
        try {
            if (salt == null) try (Cursor c = getReadableDatabase().rawQuery("SELECT value FROM secret", null)) {
                if (!c.moveToFirst()) throw new IllegalStateException("Missing Preview history key");
                salt = c.getBlob(0);
            }
            Mac mac = Mac.getInstance("HmacSHA256"); mac.init(new SecretKeySpec(salt, "HmacSHA256"));
            return hex(mac.doFinal(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        } catch (java.security.GeneralSecurityException failure) { throw new IllegalStateException(failure); }
    }
    static String documentIdentity(Uri uri) {
        // No provider query, guessed storage path or retained URI permission.
        // A tree/document and plain document URI can identify the same object.
        try {
            if ("content".equals(uri.getScheme()) && uri.getPathSegments().contains("document"))
                return "document:" + uri.getAuthority() + ":" + DocumentsContract.getDocumentId(uri);
        } catch (IllegalArgumentException ignored) { /* Non-document provider: use its complete URI. */ }
        return "uri:" + uri.normalizeScheme().toString();
    }
    Identity identify(Uri uri, FileDescriptor fd, long offset, long length) {
        String file = "", sample = ""; long size = -1, modified = -1;
        if (fd != null) try {
            StructStat stat = Os.fstat(fd);
            if (OsConstants.S_ISREG(stat.st_mode)) {
                size = length >= 0 ? length : Math.max(0, stat.st_size - offset);
                file = key("file:" + stat.st_dev + ":" + stat.st_ino + ":" + offset + ":" + size);
                modified = stat.st_mtime;
                // Bounded, non-seeking reads of an already granted regular file.
                // This validates known identities; it never merges by sampled bytes.
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                byte[] buffer = new byte[32768];
                for (long at : new long[]{offset, offset + Math.max(0, size - buffer.length)}) {
                    int remaining = (int)Math.min(buffer.length, Math.max(0, offset + size - at));
                    while (remaining > 0) {
                        int count = Os.pread(fd, buffer, 0, remaining, at);
                        if (count <= 0) break;
                        digest.update(buffer, 0, count); remaining -= count; at += count;
                    }
                }
                sample = key("sample:" + hex(digest.digest()));
            }
        } catch (Exception unavailable) {
            // Pipes/remote descriptors may not expose stable file metadata.
            // Stable document/URI identity still works; no guessed aliases.
            file = ""; sample = ""; size = -1; modified = -1;
        }
        return new Identity(key(documentIdentity(uri)), file, sample, size, modified);
    }
    static boolean resumable(long position, long duration) {
        return duration > 0 && position >= 30000 && position < duration
                && duration - position > 30000 && position < duration * .95;
    }
    Entry load(Identity identity, long duration) {
        SQLiteDatabase db = getWritableDatabase();
        for (String alias : new String[]{identity.uri, identity.file}) {
            if (alias.isEmpty()) continue;
            try (Cursor c = db.rawQuery("SELECT v.id,v.position,v.duration,v.size,v.modified,v.file,v.sample FROM video v JOIN alias a ON a.video=v.id WHERE a.key=?", new String[]{alias})) {
                if (!c.moveToFirst()) continue;
                boolean same = Math.abs(c.getLong(2) - duration) <= 1000
                        && (identity.size < 0 || c.getLong(3) < 0 || identity.size == c.getLong(3))
                        && (identity.sample.isEmpty() || c.getString(6).isEmpty() || identity.sample.equals(c.getString(6)))
                        && (identity.file.isEmpty() || !identity.file.equals(c.getString(5)) || identity.modified == c.getLong(4));
                if (same && resumable(c.getLong(1), duration))
                    return new Entry(c.getString(0), identity, duration, c.getLong(1));
            }
            // A provider can reuse its URI for replaced content. Detach only
            // that alias, leaving independent old-media aliases untouched.
            db.delete("alias", "key=?", new String[]{alias});
        }
        return new Entry(UUID.randomUUID().toString(), identity, duration, 0);
    }
    void save(Entry entry, long position) {
        if (entry == null) return;
        if (!resumable(position, entry.duration)) { clear(entry); return; }
        SQLiteDatabase db = getWritableDatabase(); db.beginTransaction();
        try {
            ContentValues values = new ContentValues();
            values.put("id", entry.id); values.put("position", position); values.put("duration", entry.duration);
            values.put("size", entry.identity.size); values.put("modified", entry.identity.modified);
            values.put("file", entry.identity.file); values.put("sample", entry.identity.sample);
            values.put("updated", System.currentTimeMillis());
            if (db.update("video", values, "id=?", new String[]{entry.id}) == 0) db.insertOrThrow("video", null, values);
            for (String alias : new String[]{entry.identity.uri, entry.identity.file}) if (!alias.isEmpty()) {
                ContentValues link = new ContentValues(); link.put("key", alias); link.put("video", entry.id);
                db.insertWithOnConflict("alias", null, link, SQLiteDatabase.CONFLICT_REPLACE);
            }
            db.execSQL("DELETE FROM video WHERE id NOT IN (SELECT id FROM video ORDER BY updated DESC,id LIMIT " + LIMIT + ") OR id NOT IN (SELECT video FROM alias)");
            // Multiple temporary provider URIs must not grow history indefinitely.
            db.execSQL("DELETE FROM alias WHERE rowid NOT IN (SELECT rowid FROM alias ORDER BY rowid DESC LIMIT 4000)");
            db.setTransactionSuccessful();
        } finally { db.endTransaction(); }
    }
    void clear(Entry entry) {
        if (entry != null) getWritableDatabase().delete("video", "id=?", new String[]{entry.id});
    }
    private static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder(bytes.length * 2);
        for (byte value : bytes) result.append(Character.forDigit((value >>> 4) & 15, 16)).append(Character.forDigit(value & 15, 16));
        return result.toString();
    }
}
