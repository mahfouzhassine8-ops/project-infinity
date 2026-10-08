/* SPDX-License-Identifier: GPL-2.0-or-later */
package com.projectinfinity.kodi.shutdown;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Authoritative Android-side normal-close transaction, independent of Activity teardown.
 * No implementation of persistence or process termination is supplied here.
 * The injected channel MUST represent one authenticated, existing engine binding.
 * Public observers receive immutable snapshots and cannot manufacture a save acknowledgement.
 */
public final class InfinityShutdownTransaction {
  public static final int SCHEMA = 1;
  public enum Phase {
    IDLE, QUIESCE, CHECKPOINT_REQUESTED, PERSISTING, SAFE_TO_TERMINATE,
    ENGINE_TERMINATING, COMPLETE, CHECKPOINT_FAILED
  }
  public enum SaveResult { COMMITTED, ALREADY_DURABLE, FAILED }
  public interface Clock { long elapsedMillis(); }

  /** A transport exception, lost binding, or deadline NEVER authorizes termination. */
  public interface EngineChannel {
    EngineIdentity identity();
    void quiesce(Session session, QuiesceReply reply) throws Exception;
    void checkpoint(Session session, Manifest manifest, CheckpointReply reply) throws Exception;
    void terminate(TerminationAuthorization authorization) throws Exception;
  }
  public interface QuiesceReply {
    void ready(Manifest manifest);
    void failed(String detail);
  }
  public interface CheckpointReply {
    void started();
    void completed(Receipt receipt);
    void failed(String detail);
  }

  public static final class EngineIdentity {
    public final UUID owner;
    public final int pid;
    /** Changes on every authenticated Binder connection, even for the same PID. */
    public final UUID binding;
    public EngineIdentity(UUID owner, int pid, UUID binding) {
      if (owner == null || binding == null || pid <= 0) throw new IllegalArgumentException("engine identity");
      this.owner = owner; this.pid = pid; this.binding = binding;
    }
    public boolean same(EngineIdentity other) {
      return other != null && pid == other.pid && owner.equals(other.owner) && binding.equals(other.binding);
    }
  }
  public static final class Session {
    public final UUID id;
    public final EngineIdentity engine;
    public final long startedAt, deadline;
    private Session(EngineIdentity engine, long startedAt, long deadline) {
      this(UUID.randomUUID(), engine, startedAt, deadline);
    }
    /** Wire DTO constructor; receiving adapters still authenticate the bound peer first. */
    public Session(UUID id, EngineIdentity engine, long startedAt, long deadline) {
      if (id == null || engine == null || startedAt < 0 || deadline <= startedAt)
        throw new IllegalArgumentException("session identity/deadline");
      this.id = id; this.engine = engine;
      this.startedAt = startedAt; this.deadline = deadline;
    }
    public boolean same(Session other) {
      return other != null && id.equals(other.id) && engine.same(other.engine) &&
          startedAt == other.startedAt && deadline == other.deadline;
    }
  }
  public static final class OwnerCut {
    public final String owner;
    public final long generation;
    public final boolean dirty;
    public OwnerCut(String owner, long generation, boolean dirty) {
      requireName(owner);
      if (generation < 0) throw new IllegalArgumentException("negative generation");
      this.owner = owner; this.generation = generation; this.dirty = dirty;
    }
  }
  /** Captured only after every enrolled writer has stopped admitting new mutations. */
  public static final class Manifest {
    public final int schema;
    public final Session session;
    public final long generation;
    public final boolean admissionSealed;
    public final List<OwnerCut> owners;
    public Manifest(int schema, Session session, long generation, boolean admissionSealed,
                    List<OwnerCut> owners) {
      this.schema = schema; this.session = session; this.generation = generation;
      this.admissionSealed = admissionSealed;
      this.owners = Collections.unmodifiableList(new ArrayList<OwnerCut>(owners));
    }
    public boolean sameCut(Manifest other) {
      if (other == null || schema != other.schema || session == null || !session.same(other.session) ||
          generation != other.generation || admissionSealed != other.admissionSealed ||
          owners.size() != other.owners.size()) return false;
      Map<String, OwnerCut> byName = new LinkedHashMap<String, OwnerCut>();
      for (OwnerCut item : owners)
        if (item == null || byName.put(item.owner, item) != null) return false;
      Set<String> seen = new LinkedHashSet<String>();
      for (OwnerCut item : other.owners) {
        if (item == null || !seen.add(item.owner)) return false;
        OwnerCut expected = byName.get(item.owner);
        if (expected == null || expected.generation != item.generation || expected.dirty != item.dirty) return false;
      }
      return true;
    }
  }
  public static final class OwnerResult {
    public final String owner;
    public final SaveResult result;
    public final long observedGeneration, durableGeneration;
    public final boolean requiredWritesFinished;
    public OwnerResult(String owner, SaveResult result, long observedGeneration,
                       long durableGeneration, boolean requiredWritesFinished) {
      requireName(owner);
      this.owner = owner; this.result = result; this.observedGeneration = observedGeneration;
      this.durableGeneration = durableGeneration; this.requiredWritesFinished = requiredWritesFinished;
    }
  }
  /** Native acknowledgement, not a request accepted response or historical status file. */
  public static final class Receipt {
    public final int schema;
    public final Session session;
    public final UUID checkpoint;
    public final long generation;
    public final boolean admissionSealed;
    public final List<OwnerResult> owners;
    public Receipt(int schema, Session session, UUID checkpoint, long generation,
                   boolean admissionSealed, List<OwnerResult> owners) {
      this.schema = schema; this.session = session; this.checkpoint = checkpoint;
      this.generation = generation; this.admissionSealed = admissionSealed;
      this.owners = Collections.unmodifiableList(new ArrayList<OwnerResult>(owners));
    }
    /** Exact immutable proof comparison, including every owner result; survives IPC decoding. */
    public boolean sameProof(Receipt other) {
      if (other == null || schema != other.schema || session == null || !session.same(other.session) ||
          checkpoint == null || !checkpoint.equals(other.checkpoint) || generation != other.generation ||
          admissionSealed != other.admissionSealed || owners.size() != other.owners.size()) return false;
      Map<String, OwnerResult> byName = new LinkedHashMap<String, OwnerResult>();
      for (OwnerResult item : owners)
        if (item == null || byName.put(item.owner, item) != null) return false;
      Set<String> seen = new LinkedHashSet<String>();
      for (OwnerResult item : other.owners) {
        if (item == null || !seen.add(item.owner)) return false;
        OwnerResult expected = byName.get(item.owner);
        if (expected == null || expected.result != item.result ||
            expected.observedGeneration != item.observedGeneration ||
            expected.durableGeneration != item.durableGeneration ||
            expected.requiredWritesFinished != item.requiredWritesFinished) return false;
      }
      return true;
    }
  }
  /** Only this coordinator can create this one-shot capability after validating a receipt. */
  public static final class TerminationAuthorization {
    public final Session session;
    public final Receipt receipt;
    private final EngineChannel channel;
    private boolean consumed, revoked;
    private TerminationAuthorization(Session session, Receipt receipt, EngineChannel channel) {
      this.session = session; this.receipt = receipt; this.channel = channel;
    }
    synchronized boolean consume(EngineIdentity recipient, Session current, Receipt nativeReceipt,
                                 long now) {
      if (consumed || revoked || !session.engine.same(recipient) ||
          !session.engine.same(channel.identity()) || !session.same(current) || !receipt.sameProof(nativeReceipt) ||
          now < session.startedAt || now >= session.deadline) return false;
      consumed = true;
      return true;
    }
    synchronized boolean revoke() {
      if (consumed) return false;
      revoked = true; return true;
    }
  }
  public static final class Snapshot {
    public final Phase phase;
    public final Session session;
    public final String failure;
    public final Receipt receipt;
    private Snapshot(Phase phase, Session session, String failure, Receipt receipt) {
      this.phase = phase; this.session = session; this.failure = failure; this.receipt = receipt;
    }
  }

  private final Clock clock;
  private final long timeoutMillis;
  private final Set<String> requiredOwners;
  private Phase phase = Phase.IDLE;
  private Session session;
  private EngineChannel channel;
  private Manifest manifest;
  private Receipt receipt;
  private TerminationAuthorization authorization;
  private String failure = "";

  /** Owners come from an audited persistence registry; an empty registry fails closed. */
  public InfinityShutdownTransaction(Clock clock, long timeoutMillis, Set<String> requiredOwners) {
    if (clock == null || timeoutMillis <= 0 || requiredOwners == null || requiredOwners.isEmpty())
      throw new IllegalArgumentException("clock, finite positive timeout, and audited owners required");
    LinkedHashSet<String> copy = new LinkedHashSet<String>();
    for (String owner : requiredOwners) { requireName(owner); copy.add(owner); }
    this.clock = clock; this.timeoutMillis = timeoutMillis;
    this.requiredOwners = Collections.unmodifiableSet(copy);
  }

  /** Duplicate presses return the same session, including after failure; never silently retry. */
  public Session close(EngineChannel engine) {
    final Session target;
    synchronized (this) {
      if (phase != Phase.IDLE) return session;
      if (engine == null || engine.identity() == null) throw new IllegalArgumentException("bound engine required");
      long now = clock.elapsedMillis();
      if (now < 0 || now > Long.MAX_VALUE - timeoutMillis) throw new IllegalStateException("invalid clock");
      channel = engine; session = new Session(engine.identity(), now, now + timeoutMillis);
      phase = Phase.QUIESCE; target = session;
    }
    try {
      engine.quiesce(target, new QuiesceReply() {
        public void ready(Manifest cut) { onQuiesced(engine, target, cut); }
        public void failed(String detail) { onFailure(engine, target, "quiesce_failed:" + detail); }
      });
    } catch (Exception problem) { onFailure(engine, target, "quiesce_transport_failed"); }
    return target;
  }
  private void onQuiesced(final EngineChannel engine, final Session target, Manifest cut) {
    synchronized (this) {
      if (!current(engine, target) || expired() || phase != Phase.QUIESCE) return;
      String problem = validateManifest(target, requiredOwners, cut);
      if (problem != null) { fail(problem); return; }
      manifest = cut; phase = Phase.CHECKPOINT_REQUESTED;
    }
    try {
      engine.checkpoint(target, cut, new CheckpointReply() {
        public void started() {
          synchronized (InfinityShutdownTransaction.this) {
            if (current(engine, target) && !expired() && phase == Phase.CHECKPOINT_REQUESTED)
              phase = Phase.PERSISTING;
          }
        }
        public void completed(Receipt saved) { onCheckpoint(engine, target, saved); }
        public void failed(String detail) { onFailure(engine, target, "checkpoint_failed:" + detail); }
      });
    } catch (Exception problem) { onFailure(engine, target, "checkpoint_transport_failed"); }
  }
  private void onCheckpoint(EngineChannel engine, Session target, Receipt saved) {
    final TerminationAuthorization permit;
    synchronized (this) {
      if (!current(engine, target) || expired() || terminal()) return;
      if (phase == Phase.ENGINE_TERMINATING) return; // Replayed callbacks cannot revoke/discard a valid dispatch.
      if (phase != Phase.PERSISTING) { fail("acknowledgement_out_of_order"); return; }
      String problem = validateReceipt(target, requiredOwners, manifest, saved);
      if (problem != null) { fail(problem); return; }
      receipt = saved; phase = Phase.SAFE_TO_TERMINATE;
      authorization = new TerminationAuthorization(session, saved, engine); permit = authorization;
      // No lifecycle observer can perform this transition. Only the matched channel gets the capability.
      phase = Phase.ENGINE_TERMINATING;
    }
    try { engine.terminate(permit); }
    catch (Exception problem) { onFailure(engine, target, "termination_dispatch_failed"); }
  }
  private synchronized void onFailure(EngineChannel engine, Session target, String detail) {
    if (current(engine, target) && !terminal() &&
        (phase != Phase.ENGINE_TERMINATING || "termination_dispatch_failed".equals(detail))) fail(detail);
  }
  /** Adapter calls only after authenticated bound-engine death / owner-lease release. */
  public synchronized void engineDied(EngineChannel engine, Session target) {
    if (!current(engine, target) || terminal()) return;
    if (phase == Phase.ENGINE_TERMINATING && receipt != null) phase = Phase.COMPLETE;
    else fail("engine_died_before_authorized_termination");
  }
  public synchronized void transportLost(EngineChannel engine, Session target) {
    if (current(engine, target) && !terminal()) fail("bound_endpoint_lost_without_death_proof");
  }
  /** Schedule externally using Android elapsedRealtime; timeout records failure, never kills. */
  public synchronized void checkDeadline() { expired(); }
  public synchronized Snapshot snapshot() { return new Snapshot(phase, session, failure, receipt); }

  private boolean current(EngineChannel engine, Session target) {
    return engine == channel && session != null && session.same(target) && session.engine.same(engine.identity());
  }
  private boolean terminal() { return phase == Phase.COMPLETE || phase == Phase.CHECKPOINT_FAILED; }
  private boolean expired() {
    if (session == null || terminal()) return terminal();
    long now = clock.elapsedMillis();
    if (now < session.startedAt || now >= session.deadline) { fail("checkpoint_deadline_exceeded"); return true; }
    return false;
  }
  private void fail(String detail) {
    if (authorization != null && !authorization.revoke()) {
      // Consumption is the irreversible authorization boundary. A transport exception after that
      // point cannot undo a kill; retain pending/unknown until matching process-death evidence.
      failure = "termination_confirmation_pending:" + detail; return;
    }
    phase = Phase.CHECKPOINT_FAILED; failure = detail;
  }

  static String validateManifest(Session target, Set<String> required, Manifest cut) {
    if (cut == null || cut.schema != SCHEMA || !target.same(cut.session) || cut.generation <= 0 ||
        !cut.admissionSealed) return "invalid_quiescence_manifest";
    Set<String> names = new LinkedHashSet<String>();
    for (OwnerCut owner : cut.owners)
      if (owner == null || !names.add(owner.owner)) return "duplicate_or_missing_owner_cut";
    return names.equals(required) ? null : "required_owner_registry_mismatch";
  }
  static String validateReceipt(Session target, Set<String> required, Manifest cut, Receipt saved) {
    String problem = validateManifest(target, required, cut);
    if (problem != null) return problem;
    if (saved == null || saved.schema != SCHEMA || !target.same(saved.session) || saved.checkpoint == null ||
        saved.generation != cut.generation || !saved.admissionSealed) return "invalid_checkpoint_receipt";
    Map<String, OwnerCut> cuts = new LinkedHashMap<String, OwnerCut>();
    for (OwnerCut item : cut.owners) cuts.put(item.owner, item);
    Set<String> names = new LinkedHashSet<String>();
    for (OwnerResult result : saved.owners) {
      if (result == null || !names.add(result.owner)) return "duplicate_or_missing_owner_result";
      OwnerCut owner = cuts.get(result.owner);
      if (owner == null || !result.requiredWritesFinished || result.observedGeneration != owner.generation ||
          result.durableGeneration != owner.generation || result.result !=
          (owner.dirty ? SaveResult.COMMITTED : SaveResult.ALREADY_DURABLE)) return "owner_persistence_unconfirmed";
    }
    return names.equals(required) ? null : "missing_required_owner_result";
  }
  private static void requireName(String owner) {
    if (owner == null || !owner.matches("[a-z][a-z0-9_.-]{0,63}")) throw new IllegalArgumentException("owner name");
  }
}
