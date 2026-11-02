package com.projectinfinity.kodi;

/** Small request-owned state model, independent of Android and existing owners. */
public final class InfinityExternalState {
    public enum Phase { IDLE, OPENING, PREPARING, READY, PLAYING, PAUSED, ENDED, ERROR, RELEASED }
    private long generation;
    private String request;
    private Phase phase = Phase.IDLE;
    public long begin(String id) {
        if (id != null && id.equals(request) && phase != Phase.RELEASED) return -1;
        request = id; phase = Phase.OPENING; return ++generation;
    }
    public boolean current(long token) { return token == generation && phase != Phase.RELEASED; }
    public boolean set(long token, Phase next) {
        if (!current(token)) return false;
        phase = next; return true;
    }
    public void release() { ++generation; phase = Phase.RELEASED; }
    public Phase phase() { return phase; }
    public boolean loading() { return phase == Phase.OPENING || phase == Phase.PREPARING; }
}
