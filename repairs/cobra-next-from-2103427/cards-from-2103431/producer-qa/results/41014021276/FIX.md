Run41014021276 failed before owner compilation or behavioral tests while resolving `androidx.tracing:tracing:jar:1.1.0`. The two direct Monitor/Espresso AAR bootstrap declarations exposed Monitor's transitive tracing dependency as an unavailable JAR.

The fix removes only those two redundant entries from `bootstrap_pom()`. The existing pinned Robolectric4.14.1 dependency still supplies Monitor1.7.2 and Espresso idling resource3.6.1 as AARs, with the upstream wildcard transitive exclusions. The cached official Robolectric POM was inspected and both exact coordinates/types/exclusions were asserted read-only. No dependency version, production source, selected test, Android behavior or signing route changed.

Python syntax parsed. No behavioral tests or producer dispatch ran for this fix. A new source-bound producer remains root-owned after review; the failed run and official archive digest remain recorded.
