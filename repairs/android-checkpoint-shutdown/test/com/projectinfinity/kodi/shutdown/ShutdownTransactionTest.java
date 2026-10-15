/* SPDX-License-Identifier: GPL-2.0-or-later */
package com.projectinfinity.kodi.shutdown;

import java.lang.reflect.Constructor;
import java.lang.reflect.Modifier;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;
import com.projectinfinity.kodi.shutdown.InfinityShutdownTransaction.*;

/** Executable host protocol tests. These do not claim that a native persistence implementation exists. */
public final class ShutdownTransactionTest {
  static int passed;
  static final Set<String> OWNERS = new LinkedHashSet<String>(Arrays.asList("settings", "resume_hub"));
  static final class FakeClock implements Clock {
    volatile long now = 100;
    public long elapsedMillis() { return now; }
  }
  static EngineIdentity identity() { return new EngineIdentity(UUID.randomUUID(), 420, UUID.randomUUID()); }
  static final class Channel implements EngineChannel {
    final EngineIdentity identity = ShutdownTransactionTest.identity();
    QuiesceReply quiesce;
    CheckpointReply checkpoint;
    TerminationAuthorization authorization;
    int quiesces, checkpoints, terminationRequests;
    boolean throwOnTerminate;
    public EngineIdentity identity() { return identity; }
    public void quiesce(Session session, QuiesceReply reply) { quiesces++; quiesce = reply; }
    public void checkpoint(Session session, Manifest manifest, CheckpointReply reply) { checkpoints++; checkpoint = reply; }
    public void terminate(TerminationAuthorization permit) {
      terminationRequests++; authorization = permit;
      if (throwOnTerminate) throw new IllegalStateException("transport rejected before delivery");
    }
  }
  static final class Fixture {
    final FakeClock clock = new FakeClock();
    final Channel engine = new Channel();
    final InfinityShutdownTransaction core = new InfinityShutdownTransaction(clock, 1000, OWNERS);
    final Session session = core.close(engine);
    final Manifest cut = cut(session);
    void persist() { engine.quiesce.ready(cut); engine.checkpoint.started(); }
    void ack() { engine.checkpoint.completed(receipt(session)); }
  }
  static Manifest cut(Session session) {
    return new Manifest(SCHEMA, session, 77, true, Arrays.asList(
        new OwnerCut("settings", 3, false), new OwnerCut("resume_hub", 8, true)));
  }
  static final int SCHEMA = InfinityShutdownTransaction.SCHEMA;
  static Receipt receipt(Session session) {
    return new Receipt(SCHEMA, session, UUID.randomUUID(), 77, true, Arrays.asList(
        new OwnerResult("settings", SaveResult.ALREADY_DURABLE, 3, 3, true),
        new OwnerResult("resume_hub", SaveResult.COMMITTED, 8, 8, true)));
  }
  static void check(boolean truth, String message) { if (!truth) throw new AssertionError(message); }
  static void phase(Fixture f, Phase phase) { check(f.core.snapshot().phase == phase, "Expected " + phase + " got " + f.core.snapshot().phase); }
  static void rejects(Runnable task) {
    boolean rejected = false;
    try { task.run(); } catch (IllegalArgumentException | IllegalStateException expected) { rejected = true; }
    check(rejected, "Expected rejection");
  }
  static void run(String name, Runnable test) { test.run(); passed++; System.out.println("PASS " + name); }

  static void happyAndIdempotent() {
    Fixture f = new Fixture(); phase(f, Phase.QUIESCE);
    check(f.core.close(f.engine) == f.session, "Duplicate close created new session");
    check(f.engine.quiesces == 1, "Duplicate quiesce");
    f.engine.quiesce.ready(f.cut); phase(f, Phase.CHECKPOINT_REQUESTED);
    f.engine.checkpoint.started(); phase(f, Phase.PERSISTING);
    Receipt saved = receipt(f.session); f.engine.checkpoint.completed(saved);
    phase(f, Phase.ENGINE_TERMINATING);
    check(f.engine.terminationRequests == 1 && f.core.snapshot().receipt == saved, "No matched permit");
    f.engine.checkpoint.completed(saved); f.engine.checkpoint.failed("late duplicate");
    check(f.engine.terminationRequests == 1, "Duplicate termination");
    phase(f, Phase.ENGINE_TERMINATING);
    f.core.engineDied(f.engine, f.session); phase(f, Phase.COMPLETE);
    check(f.core.close(new Channel()) == f.session, "Completed transaction reused for different engine");
  }
  static void missingAndExtraOwners() {
    Fixture f = new Fixture();
    f.engine.quiesce.ready(new Manifest(SCHEMA, f.session, 77, true,
        Collections.singletonList(new OwnerCut("settings", 3, false))));
    phase(f, Phase.CHECKPOINT_FAILED); check(f.engine.checkpoints == 0, "Missing owner advanced");
    Fixture second = new Fixture(); second.persist();
    second.engine.checkpoint.completed(new Receipt(SCHEMA, second.session, UUID.randomUUID(), 77, true,
        Collections.singletonList(new OwnerResult("settings", SaveResult.ALREADY_DURABLE, 3, 3, true))));
    phase(second, Phase.CHECKPOINT_FAILED); check(second.engine.terminationRequests == 0, "Incomplete ack terminated");
  }
  static void corruptReceipts() {
    for (int variant = 0; variant < 9; variant++) {
      Fixture f = new Fixture(); f.persist();
      OwnerResult resume = new OwnerResult("resume_hub", SaveResult.COMMITTED,
          variant == 0 ? 9 : 8, variant == 1 ? 7 : 8, variant != 2);
      if (variant == 3) resume = new OwnerResult("resume_hub", SaveResult.FAILED, 8, 8, true);
      if (variant == 4) resume = new OwnerResult("resume_hub", SaveResult.ALREADY_DURABLE, 8, 8, true);
      List<OwnerResult> results = Arrays.asList(
          new OwnerResult("settings", SaveResult.ALREADY_DURABLE, 3, 3, true), resume);
      if (variant == 5) results = Arrays.asList(resume, resume);
      f.engine.checkpoint.completed(new Receipt(variant == 6 ? 2 : SCHEMA, f.session,
          UUID.randomUUID(), variant == 7 ? 78 : 77, variant != 8, results));
      phase(f, Phase.CHECKPOINT_FAILED); check(f.engine.terminationRequests == 0, "Bad ack variant " + variant + " terminated");
    }
  }
  static void staleSessionAndOwner() {
    Fixture f = new Fixture(); Fixture old = new Fixture(); f.persist();
    f.engine.checkpoint.completed(receipt(old.session)); phase(f, Phase.CHECKPOINT_FAILED);
    check(f.engine.terminationRequests == 0, "Old session terminated");
    Fixture second = new Fixture(); second.persist(); second.ack();
    second.core.engineDied(new Channel(), second.session); phase(second, Phase.ENGINE_TERMINATING);
    second.core.engineDied(second.engine, old.session); phase(second, Phase.ENGINE_TERMINATING);
    second.core.engineDied(second.engine, second.session); phase(second, Phase.COMPLETE);
  }
  static void timeoutRejectsLateAck() {
    Fixture f = new Fixture(); f.persist(); f.clock.now = f.session.deadline;
    f.ack(); phase(f, Phase.CHECKPOINT_FAILED); check(f.engine.terminationRequests == 0, "Late ack authorized");
    f.clock.now = 101; f.ack(); phase(f, Phase.CHECKPOINT_FAILED);
    check(f.engine.terminationRequests == 0, "Failed transaction resurrected");
  }
  static void failuresAndDeathNeverSave() {
    Fixture f = new Fixture(); f.persist(); f.engine.checkpoint.failed("disk full");
    phase(f, Phase.CHECKPOINT_FAILED); f.ack(); check(f.engine.terminationRequests == 0, "Save failure authorized");
    Fixture dead = new Fixture(); dead.core.engineDied(dead.engine, dead.session);
    phase(dead, Phase.CHECKPOINT_FAILED); check(dead.core.snapshot().receipt == null, "Death forged receipt");
    Fixture lost = new Fixture(); lost.persist(); lost.core.transportLost(lost.engine, lost.session);
    lost.ack(); phase(lost, Phase.CHECKPOINT_FAILED); check(lost.engine.terminationRequests == 0, "Lost binding authorized");
  }
  static void outOfOrderCannotSave() {
    Fixture f = new Fixture(); f.engine.quiesce.ready(f.cut); f.ack();
    phase(f, Phase.CHECKPOINT_FAILED); check(f.engine.terminationRequests == 0, "Ack before persistence started");
  }
  static void permitReplayRevocationAndDeadline() {
    Fixture f = new Fixture(); f.persist(); f.ack(); Receipt saved = f.core.snapshot().receipt;
    TerminationAuthorization permit = f.engine.authorization;
    check(!permit.consume(identity(), f.session, saved, f.clock.now), "Wrong bound endpoint accepted");
    Receipt decoded = new Receipt(saved.schema, new Session(f.session.id,
        new EngineIdentity(f.session.engine.owner, f.session.engine.pid, f.session.engine.binding),
        f.session.startedAt, f.session.deadline), saved.checkpoint, saved.generation, saved.admissionSealed, saved.owners);
    check(permit.consume(f.engine.identity(), f.session, decoded, f.clock.now), "Semantic IPC receipt rejected");
    check(!permit.consume(f.engine.identity(), f.session, decoded, f.clock.now), "Permit replay accepted");
    Fixture revoked = new Fixture(); revoked.persist(); revoked.ack();
    revoked.core.transportLost(revoked.engine, revoked.session); phase(revoked, Phase.CHECKPOINT_FAILED);
    check(!revoked.engine.authorization.consume(revoked.engine.identity(), revoked.session,
        revoked.core.snapshot().receipt, revoked.clock.now), "Failure left a consumable permit");
    Fixture timed = new Fixture(); timed.persist(); timed.ack(); timed.clock.now = timed.session.deadline;
    timed.core.checkDeadline(); phase(timed, Phase.CHECKPOINT_FAILED);
    check(!timed.engine.authorization.consume(timed.engine.identity(), timed.session,
        timed.core.snapshot().receipt, timed.clock.now), "Expired permit consumed");
  }
  static void dispatchFailureRevokesPermit() {
    Fixture f = new Fixture(); f.persist(); f.engine.throwOnTerminate = true; f.ack();
    phase(f, Phase.CHECKPOINT_FAILED);
    check(!f.engine.authorization.consume(f.engine.identity(), f.session, f.core.snapshot().receipt,
        f.clock.now), "Failed dispatch delivered a live delayed permit");
  }
  static void consumedPermitNeedsDeath() {
    Fixture f = new Fixture(); f.persist(); f.ack();
    check(f.engine.authorization.consume(f.engine.identity(), f.session, f.core.snapshot().receipt, f.clock.now), "Consume failed");
    f.core.transportLost(f.engine, f.session); phase(f, Phase.ENGINE_TERMINATING);
    check(f.core.snapshot().failure.startsWith("termination_confirmation_pending:"), "Lost dispatch uncertainty hidden");
    f.clock.now = f.session.deadline + 50; f.core.checkDeadline(); phase(f, Phase.ENGINE_TERMINATING);
    f.core.engineDied(f.engine, f.session); phase(f, Phase.COMPLETE);
  }
  static void noObserverAuthorization() {
    for (Constructor<?> constructor : TerminationAuthorization.class.getDeclaredConstructors())
      if (!constructor.isSynthetic()) check(Modifier.isPrivate(constructor.getModifiers()), "Public authorization constructor");
    rejects(() -> new InfinityShutdownTransaction(new FakeClock(), 100, Collections.<String>emptySet()));
    Fixture f = new Fixture(); Snapshot observed = f.core.snapshot();
    check(observed.receipt == null && f.engine.authorization == null, "Observer manufactured proof");
  }
  static void racingFailureAndConsume() {
    for (int iteration = 0; iteration < 100; iteration++) {
      final Fixture f = new Fixture(); f.persist(); f.ack();
      final CountDownLatch start = new CountDownLatch(1);
      final AtomicReference<Boolean> consumed = new AtomicReference<Boolean>();
      Thread consumer = new Thread(() -> {
        try { start.await(); consumed.set(f.engine.authorization.consume(f.engine.identity(), f.session,
            f.core.snapshot().receipt, f.clock.now)); } catch (InterruptedException error) { throw new AssertionError(error); }
      });
      Thread failure = new Thread(() -> {
        try { start.await(); f.core.transportLost(f.engine, f.session); }
        catch (InterruptedException error) { throw new AssertionError(error); }
      });
      consumer.start(); failure.start(); start.countDown();
      try { consumer.join(); failure.join(); } catch (InterruptedException error) { throw new AssertionError(error); }
      check(consumed.get() != null, "Consumer did not run");
      check(!(consumed.get() && f.core.snapshot().phase == Phase.CHECKPOINT_FAILED), "Failed transaction retained consumed capability");
      if (!consumed.get()) phase(f, Phase.CHECKPOINT_FAILED);
    }
  }
  static final class Backend implements InfinityCheckpointEndpoint.NativeBackend {
    QuiesceReply quiesce;
    InfinityCheckpointEndpoint.NativeCheckpointReply checkpoint;
    Session session;
    int terminations;
    public void quiesce(Session requested, Set<String> owners, QuiesceReply reply) { session = requested; quiesce = reply; }
    public void checkpoint(Session requested, Manifest cut, InfinityCheckpointEndpoint.NativeCheckpointReply reply) { checkpoint = reply; }
    public void terminateCheckpointedProcess(Session requested, Manifest cut, Receipt saved) {
      check(session.same(requested), "Native session changed"); terminations++;
    }
  }
  static void endpointRequiresNativeProof() {
    FakeClock clock = new FakeClock(); Backend backend = new Backend();
    InfinityCheckpointEndpoint engine = new InfinityCheckpointEndpoint(identity(), clock, backend, OWNERS);
    InfinityShutdownTransaction core = new InfinityShutdownTransaction(clock, 1000, OWNERS);
    Session session = core.close(engine);
    rejects(() -> { try { engine.terminate(null); } catch (RuntimeException e) { throw e; } catch (Exception e) { throw new AssertionError(e); } });
    backend.quiesce.ready(cut(session)); check(backend.terminations == 0, "Quiesce terminated");
    backend.checkpoint.saved(receipt(session));
    check(backend.terminations == 1 && core.snapshot().phase == Phase.ENGINE_TERMINATING, "Native receipt did not authorize");
    backend.checkpoint.saved(receipt(session)); check(backend.terminations == 1, "Duplicate native ack terminated twice");
    core.engineDied(engine, session); check(core.snapshot().phase == Phase.COMPLETE, "Death not recorded");
  }
  static void endpointRejectsFailedNativeProof() {
    FakeClock clock = new FakeClock(); Backend backend = new Backend();
    InfinityCheckpointEndpoint engine = new InfinityCheckpointEndpoint(identity(), clock, backend, OWNERS);
    InfinityShutdownTransaction core = new InfinityShutdownTransaction(clock, 1000, OWNERS);
    Session session = core.close(engine); backend.quiesce.ready(cut(session));
    backend.checkpoint.saved(new Receipt(SCHEMA, session, UUID.randomUUID(), 77, false, receipt(session).owners));
    check(backend.terminations == 0 && core.snapshot().phase == Phase.CHECKPOINT_FAILED, "Unsealed native proof terminated");
    backend.checkpoint.saved(receipt(session)); check(backend.terminations == 0, "Failed endpoint resurrected");
  }
  public static void main(String[] args) {
    run("happy path, duplicate close and ack", ShutdownTransactionTest::happyAndIdempotent);
    run("required owners cannot disappear", ShutdownTransactionTest::missingAndExtraOwners);
    run("dirty, uncommitted, duplicate and schema failures", ShutdownTransactionTest::corruptReceipts);
    run("stale session, PID owner and bound channel", ShutdownTransactionTest::staleSessionAndOwner);
    run("timeout rejects late acknowledgement", ShutdownTransactionTest::timeoutRejectsLateAck);
    run("failure, death and lost transport cannot certify save", ShutdownTransactionTest::failuresAndDeathNeverSave);
    run("out of order acknowledgement", ShutdownTransactionTest::outOfOrderCannotSave);
    run("one shot, semantic IPC proof, revocation and expiry", ShutdownTransactionTest::permitReplayRevocationAndDeadline);
    run("failed dispatch revokes delayed capability", ShutdownTransactionTest::dispatchFailureRevokesPermit);
    run("consumed capability needs matching process death", ShutdownTransactionTest::consumedPermitNeedsDeath);
    run("observers cannot construct authorization", ShutdownTransactionTest::noObserverAuthorization);
    run("100 concurrent revoke/consume races", ShutdownTransactionTest::racingFailureAndConsume);
    run("endpoint requires exact native save proof", ShutdownTransactionTest::endpointRequiresNativeProof);
    run("endpoint rejects failed native proof", ShutdownTransactionTest::endpointRejectsFailedNativeProof);
    System.out.println("PASS " + passed + " protocol test groups; no native persistence implementation or device claim");
  }
}
