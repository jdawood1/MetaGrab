"""Owned subprocess groups and cooperative application shutdown."""

import os
import signal
import subprocess as _subprocess
import threading
import time
import weakref

closing = threading.Event()
_processes = weakref.WeakSet()
_lock = threading.RLock()


def __getattr__(name):
    return getattr(_subprocess, name)


class Popen(_subprocess.Popen):
    def __init__(self, *args, **kwargs):
        with _lock:
            if closing.is_set():
                raise RuntimeError("__CANCELLED__")
            self._group_root = os.name == "posix" and not os.environ.get("METAGRAB_HELPER")
            if self._group_root:
                kwargs["start_new_session"] = True
            super().__init__(*args, **kwargs)
            self._owned = True
            _processes.add(self)

    def terminate(self):
        self._signal(signal.SIGTERM)

    def kill(self):
        self._signal(signal.SIGKILL)

    def _signal(self, sig):
        if not getattr(self, "_owned", False):
            return
        try:
            if self._group_root:
                os.killpg(self.pid, sig)
            elif self.poll() is None:
                super().kill() if sig == signal.SIGKILL else super().terminate()
        except ProcessLookupError:
            pass
        except PermissionError:
            # Some macOS sandboxes report EPERM for an already vanished group.
            # Do not suppress a real denial while the process still exists.
            try:
                os.getpgid(self.pid)
            except ProcessLookupError:
                return
            raise

    def __exit__(self, exc_type, value, traceback):
        try:
            if exc_type is not None or closing.is_set():
                stop(self)
            result = super().__exit__(exc_type, value, traceback)
            self.kill()
            return result
        finally:
            self._owned = False
            with _lock:
                _processes.discard(self)


def stop(process, timeout=0.5):
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except _subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    # Descendants may outlive an exited parent; address its owned group too.
    if os.name == "posix":
        process.kill()
    process._owned = False
    with _lock:
        _processes.discard(process)


def cancel_all(force=False):
    with _lock:
        closing.set()
        processes = list(_processes)
    for process in processes:
        process.kill() if force else process.terminate()


def run(args, *, input=None, capture_output=False, timeout=None, check=False, **kwargs):
    if capture_output:
        kwargs.update(stdout=_subprocess.PIPE, stderr=_subprocess.PIPE)
    if input is not None:
        kwargs["stdin"] = _subprocess.PIPE
    with Popen(args, **kwargs) as process:
        started = time.monotonic()
        first = True
        try:
            while True:
                if closing.is_set():
                    raise RuntimeError("__CANCELLED__")
                if timeout is not None and time.monotonic() - started >= timeout:
                    raise _subprocess.TimeoutExpired(args, timeout)
                try:
                    stdout, stderr = process.communicate(
                        input=input if first else None, timeout=0.2
                    )
                    break
                except _subprocess.TimeoutExpired:
                    first = False
            result = _subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
            if check:
                result.check_returncode()
            return result
        except BaseException:
            stop(process)
            raise
