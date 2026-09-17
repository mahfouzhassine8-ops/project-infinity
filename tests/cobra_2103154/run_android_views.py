#!/usr/bin/env python3
"""Run the production Android layout gate and capture JVM stacks before a hang is killed."""
from pathlib import Path
import argparse
import os
import shutil
import signal
import subprocess
import threading
import time


def dump_workers(out: Path, label: str) -> None:
    """Only inspect test workers; never print environment variables or signing material."""
    try:
        listing = subprocess.check_output(['jps', '-l'], text=True, timeout=10)
        for line in listing.splitlines():
            parts = line.split(maxsplit=1)
            if len(parts) != 2 or 'GradleWorkerMain' not in parts[1]:
                continue
            pid = parts[0]
            dump = subprocess.run(['jcmd', pid, 'Thread.print', '-l'], capture_output=True,
                                  text=True, timeout=15)
            text = dump.stdout + dump.stderr
            (out / ('threads-' + label + '-' + pid + '.txt')).write_text(text)
            print('::group::Cobra test worker thread dump ' + label, flush=True)
            print(text, flush=True)
            print('::endgroup::', flush=True)
    except (OSError, subprocess.SubprocessError) as error:
        print('Thread diagnostic unavailable: ' + type(error).__name__, flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    build, out = args.build.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    app = build / 'xbmc'
    test = app / 'src/test/java/com/projectinfinity/kodi'
    test.mkdir(parents=True, exist_ok=True)
    text = Path(__file__).with_name('CobraModesUiTest.java').read_text()
    # Host-only boundary traces: all production code and all assertions remain unchanged.
    text = text.replace('return m.invoke(owner,args);',
        'System.out.println("ENTER " + name + " thread=" + Thread.currentThread().getName());'
        'Object result=m.invoke(owner,args);System.out.println("EXIT " + name);return result;')
    text = text.replace('a.finish();',
        'System.out.println("ENTER fixture finish");a.finish();System.out.println("EXIT fixture finish");')
    text = text.replace('RuntimeEnvironment.setQualifiers(',
        'System.out.println("ENTER setQualifiers");RuntimeEnvironment.setQualifiers(')
    text = text.replace('InfinityLiveActivity a=fixture(',
        'System.out.println("ENTER fixture");InfinityLiveActivity a=fixture(')
    (test / 'CobraModesUiTest.java').write_text(text)
    with (app / 'build.gradle').open('a') as stream:
        stream.write('''
// Host-only acceptance tests; no production dependency is changed.
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
  maxHeapSize = "3g"
  maxParallelForks = 1
  systemProperty "cobra.layoutEvidence", System.getenv("COBRA_LAYOUT_EVIDENCE")
  testLogging {
    events "started", "passed", "failed", "skipped"
    showStandardStreams = true
    exceptionFormat = "full"
  }
}
dependencies {
  testImplementation 'junit:junit:4.13.2'
  testImplementation 'org.robolectric:robolectric:4.14.1'
}
''')
    env = dict(os.environ)
    env.update(COBRA_LAYOUT_EVIDENCE=str(out / 'layout-evidence'),
               KODI_ANDROID_KEY_ALIAS='androiddebugkey', KODI_ANDROID_KEY_PASSWORD='android',
               KODI_ANDROID_STORE_PASSWORD='android',
               KODI_ANDROID_STORE_FILE=str(Path.home() / '.android/debug.keystore'))
    command = ['./gradlew', '--no-daemon', '--console=plain', ':xbmc:testReleaseUnitTest',
               '--tests', 'com.projectinfinity.kodi.CobraModesUiTest', '--stacktrace']
    process = subprocess.Popen(command, cwd=build, env=env, start_new_session=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    def tee() -> None:
        with (out / 'gradle-layout.log').open('w') as log:
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end='', flush=True)
    reader = threading.Thread(target=tee, daemon=True)
    reader.start()
    started = time.monotonic()
    snapshots = set()
    try:
        while process.poll() is None:
            elapsed = time.monotonic() - started
            for boundary in (60, 120):
                if elapsed >= boundary and boundary not in snapshots:
                    snapshots.add(boundary)
                    dump_workers(out, str(boundary) + 's')
            if elapsed >= 180:
                dump_workers(out, 'timeout')
                raise TimeoutError('Android acceptance did not finish; inspect saved worker stacks')
            time.sleep(1)
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, command)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=8)
        reader.join(timeout=5)
        for rel in ('build/test-results/testReleaseUnitTest', 'build/reports/tests/testReleaseUnitTest'):
            source = app / rel
            if source.exists():
                shutil.copytree(source, out / source.parent.name, dirs_exist_ok=True)


if __name__ == '__main__':
    main()
