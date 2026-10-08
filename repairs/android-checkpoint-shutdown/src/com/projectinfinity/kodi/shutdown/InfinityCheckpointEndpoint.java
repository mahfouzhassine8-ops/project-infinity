/* SPDX-License-Identifier: GPL-2.0-or-later */
package com.projectinfinity.kodi.shutdown;

import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Set;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.CheckpointReply;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.Clock;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.EngineChannel;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.EngineIdentity;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.Manifest;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.QuiesceReply;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.Receipt;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.Session;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.TerminationAuthorization;

/**
 * Strict engine endpoint protocol. It cannot certify persistence itself and provides no kill fallback.
 * A real native backend must keep all registered writers sealed through termination or explicit recovery.
 * A Binder adapter must authenticate both peers and preserve these capabilities; no such adapter is
 * provided in this staged implementation. Creating a new service/process to deliver a close is forbidden.
 */
public final class InfinityCheckpointEndpoint implements EngineChannel {
  public interface NativeBackend {
    void quiesce(Session session, Set<String> auditedOwners, QuiesceReply reply) throws Exception;
    void checkpoint(Session session, Manifest manifest, NativeCheckpointReply reply) throws Exception;
    /**
     * Atomically revalidate this exact still-sealed generation and terminate this process only.
     * Throw if the native barrier, current PID/owner, generations, or commit proof no longer match.
     * Must not call Kodi Stop/Cleanup, dispatch Application.Quit, release writers, or substitute a timer.
     */
    void terminateCheckpointedProcess(Session session, Manifest manifest, Receipt receipt) throws Exception;
  }
  public interface NativeCheckpointReply {
    void saved(Receipt receipt);
    void failed(String detail);
  }

  private final EngineIdentity identity;
  private final Clock clock;
  private final NativeBackend backend;
  private final Set<String> requiredOwners;
  private Session session;
  private Manifest manifest;
  private Receipt receipt;
  private boolean checkpointRequested, terminationIssued, failed;

  public InfinityCheckpointEndpoint(EngineIdentity identity, Clock clock, NativeBackend backend,
                                    Set<String> auditedOwners) {
    if (identity == null || clock == null || backend == null || auditedOwners == null || auditedOwners.isEmpty())
      throw new IllegalArgumentException("bound identity, clock, native backend and owners required");
    this.identity = identity; this.clock = clock; this.backend = backend;
    this.requiredOwners = Collections.unmodifiableSet(new LinkedHashSet<String>(auditedOwners));
  }
  public EngineIdentity identity() { return identity; }

  public void quiesce(final Session requested, final QuiesceReply reply) throws Exception {
    synchronized (this) {
      if (reply == null || requested == null || !identity.same(requested.engine) || session != null ||
          !inTime(requested)) throw new IllegalStateException("quiesce session rejected");
      session = requested;
    }
    try {
      backend.quiesce(requested, requiredOwners, new QuiesceReply() {
        public void ready(Manifest cut) {
          String problem;
          synchronized (InfinityCheckpointEndpoint.this) {
            if (failed || manifest != null || !same(requested)) return;
            problem = inTime(requested) ?
                InfinityShutdownTransaction.validateManifest(requested, requiredOwners, cut) : "endpoint_deadline_exceeded";
            if (problem == null) manifest = cut; else failed = true;
          }
          if (problem == null) reply.ready(cut); else reply.failed(problem);
        }
        public void failed(String detail) {
          synchronized (InfinityCheckpointEndpoint.this) {
            if (failed || manifest != null || !same(requested)) return;
            failed = true;
          }
          reply.failed(detail);
        }
      });
    } catch (Exception problem) { synchronized (this) { failed = true; } throw problem; }
  }

  public void checkpoint(final Session requested, final Manifest cut, final CheckpointReply reply) throws Exception {
    synchronized (this) {
      if (failed || !same(requested) || manifest == null || !manifest.sameCut(cut) || checkpointRequested || !inTime(requested))
        throw new IllegalStateException("checkpoint session rejected");
      checkpointRequested = true;
    }
    reply.started();
    try {
      backend.checkpoint(requested, cut, new NativeCheckpointReply() {
        public void saved(Receipt saved) {
          String problem;
          synchronized (InfinityCheckpointEndpoint.this) {
            if (failed || receipt != null || !same(requested)) return;
            problem = inTime(requested) ?
                InfinityShutdownTransaction.validateReceipt(requested, requiredOwners, manifest, saved) : "endpoint_deadline_exceeded";
            if (problem == null) receipt = saved; else failed = true;
          }
          if (problem == null) reply.completed(saved); else reply.failed(problem);
        }
        public void failed(String detail) {
          synchronized (InfinityCheckpointEndpoint.this) {
            if (failed || receipt != null || !same(requested)) return;
            failed = true;
          }
          reply.failed(detail);
        }
      });
    } catch (Exception problem) { synchronized (this) { failed = true; } throw problem; }
  }

  public void terminate(TerminationAuthorization authorization) throws Exception {
    synchronized (this) {
      if (failed || terminationIssued || receipt == null || authorization == null ||
          !authorization.consume(identity, session, receipt, clock.elapsedMillis()))
        throw new IllegalStateException("termination authorization rejected");
      terminationIssued = true;
    }
    // The backend must perform the final atomic native generation/identity check itself.
    // No Java success, exception, lifecycle callback, or elapsed deadline can replace that check.
    backend.terminateCheckpointedProcess(session, manifest, receipt);
  }
  private boolean same(Session requested) { return session != null && session.same(requested); }
  private boolean inTime(Session requested) {
    long now = clock.elapsedMillis(); return now >= requested.startedAt && now < requested.deadline;
  }
}
