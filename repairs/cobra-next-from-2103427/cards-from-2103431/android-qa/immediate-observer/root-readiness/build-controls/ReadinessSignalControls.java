package qa;

import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/** Direct host JVM controls of the actual compiled pure-Java signal class. */
public final class ReadinessSignalControls {
  private static void require(boolean value, String reason) {
    if (!value) throw new AssertionError(reason);
  }

  private static void beforeWait() throws Exception {
    CobraImmediateHierarchy.ReadinessSignal signal = new CobraImmediateHierarchy.ReadinessSignal();
    long observed = signal.generation();
    signal.pulse(32, 7, "com.projectinfinity.kodi", 100, 100);
    require(signal.awaitAfter(observed, 0), "Event between query and wait was lost");
    require(signal.generation() == observed + 1, "Arrival generation did not advance");
  }

  private static void asynchronousWake() throws Exception {
    CobraImmediateHierarchy.ReadinessSignal signal = new CobraImmediateHierarchy.ReadinessSignal();
    CountDownLatch started = new CountDownLatch(1), finished = new CountDownLatch(1);
    AtomicReference<Throwable> failure = new AtomicReference<>();
    Thread waiter = new Thread(() -> {
      try {
        long observed = signal.generation();
        started.countDown();
        require(signal.awaitAfter(observed, 1500), "New asynchronous event did not wake waiter");
      } catch (Throwable error) {
        failure.set(error);
      } finally {
        finished.countDown();
      }
    }, "ReadinessSignalHostControl");
    waiter.start();
    require(started.await(1, TimeUnit.SECONDS), "Host waiter did not start");
    long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(1);
    while (waiter.getState() != Thread.State.TIMED_WAITING && System.nanoTime() < deadline)
      Thread.yield();
    require(waiter.getState() == Thread.State.TIMED_WAITING, "Control did not observe condition waiting");
    signal.pulse(32, 7, "com.projectinfinity.kodi", 200, 200);
    require(finished.await(1, TimeUnit.SECONDS), "Signaled waiter remained blocked");
    waiter.join(1000);
    require(!waiter.isAlive() && failure.get() == null, "Asynchronous signal failed: " + failure.get());
  }

  private static void zeroBudget() throws Exception {
    CobraImmediateHierarchy.ReadinessSignal signal = new CobraImmediateHierarchy.ReadinessSignal();
    require(!signal.awaitAfter(signal.generation(), 0), "Zero-budget request incorrectly waited/succeeded");
  }

  private static void boundedPrimitiveQueue() throws Exception {
    CobraImmediateHierarchy.ReadinessSignal signal = new CobraImmediateHierarchy.ReadinessSignal();
    for (int i = 0; i < 24; i++) signal.pulse(32, i, "com.projectinfinity.kodi", i, i);
    List<Object[]> pulses = signal.drain();
    require(pulses.size() == 16 && signal.dropped() == 8, "Queue bound/drop count changed");
    require(signal.generation() == 24, "Dropped diagnostic pulses must still advance arrival generation");
    for (int i = 0; i < pulses.size(); i++) {
      Object[] pulse = pulses.get(i);
      require(pulse.length == 6 && pulse[0].equals((long) i + 1) && pulse[1] instanceof Integer
          && pulse[2] instanceof Integer && pulse[3] instanceof String
          && pulse[4] instanceof Long && pulse[5] instanceof Long, "Nonprimitive/framework metadata retained");
    }
    require(signal.drain().isEmpty(), "Drain left diagnostic event objects retained");
  }

  private static void timestampOrderIsNotArrivalOrder() throws Exception {
    CobraImmediateHierarchy.ReadinessSignal signal = new CobraImmediateHierarchy.ReadinessSignal();
    signal.pulse(32, 7, "com.projectinfinity.kodi", 1000, 9000);
    long observed = signal.generation();
    signal.pulse(32, 7, "com.projectinfinity.kodi", 1001, 100);
    require(signal.awaitAfter(observed, 0), "Older source timestamp suppressed a new arrival");
    List<Object[]> pulses = signal.drain();
    require(pulses.get(0)[0].equals(1L) && pulses.get(1)[0].equals(2L)
        && pulses.get(0)[5].equals(9000L) && pulses.get(1)[5].equals(100L), "Events reordered by source timestamp");
  }

  public static void main(String[] args) throws Exception {
    beforeWait(); asynchronousWake(); zeroBudget(); boundedPrimitiveQueue(); timestampOrderIsNotArrivalOrder();
    System.out.println("PASS5_ACTUAL_COMPILED_READINESS_SIGNAL_CONTROLS_NO_ANDROID_RUNTIME");
  }
}
