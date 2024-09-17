import io
import queue
import sys
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout
from functools import wraps
from multiprocessing import Queue as mpQueue
from typing import Callable, Generator


class CapturingStream(io.StringIO):
    """Stream to capture stdout/stderr line by line and put them in a queue."""
    def __init__(self, queue: mpQueue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = queue
        self._current_line = ""

    def write(self, s: str) -> int:
        s = s.replace("\r", "\n")  # Normalize newlines
        if "\n" in s:
            lines = s.split("\n")
            for line in lines[:-1]:
                self._current_line += line
                self._queue.put(self._current_line)
                self._current_line = ""
            self._current_line += lines[-1]
        else:
            self._current_line += s
        return super().write(s)

    def flush(self):
        if self._current_line:
            self._queue.put(self._current_line)
            self._current_line = ""
        super().flush()


def wrap_for_process(fn: Callable) -> Callable:
    """Wrap the function to capture stdout, stderr, and errors in real-time."""
    stdout_queue = mpQueue()
    stderr_queue = mpQueue()
    error_queue = mpQueue()

    @wraps(fn)
    def _inner(*args, **kwargs):
        with redirect_stdout(CapturingStream(stdout_queue)), redirect_stderr(CapturingStream(stderr_queue)):
            try:
                fn(*args, **kwargs)
            except Exception as error:
                msg = (
                    f"Error in '{fn.__name__}':\n" +
                    "\n".join(line.strip("\n") for line in traceback.format_tb(error.__traceback__) if line.strip()) +
                    f"\n\n{error!s}"
                )
                error_queue.put(msg)

        # Flush final content from buffers
        sys.stdout.flush()
        sys.stderr.flush()

    return stdout_queue, stderr_queue, error_queue, _inner


class Logger:
    def __init__(self):
        self.process = None
        self.exit_code = None

    def log(self, message: str, level: str = "INFO"):
        return {"message": message, "level": level}

    def _log_from_queue(self, log_queue) -> Generator[str, None, None]:
        """Fetch logs from the queue and yield them as strings."""
        try:
            while True:
                log = log_queue.get_nowait()
                yield log
        except queue.Empty:
            pass

    def intercept_stdin_stdout(self, fn: Callable) -> Callable:
        """Wrap a function to intercept and yield stdout and stderr using threading."""
        def wrapped(*args, **kwargs) -> str:
            stdout_queue, stderr_queue, error_queue, wrapped_fn = wrap_for_process(fn)
            thread = threading.Thread(target=wrapped_fn, args=args, kwargs=kwargs)

            # Start the thread
            thread.start()

            # Collect logs while the thread is running
            logs = []
            while thread.is_alive():
                logs.extend(self._log_from_queue(stdout_queue))
                logs.extend(self._log_from_queue(stderr_queue))
                thread.join(timeout=0.1)

                # Concatenate the logs as one output (Gradio expects return)
                yield "\n".join(logs)

            # After the thread completes, yield any remaining logs
            logs.extend(self._log_from_queue(stdout_queue))
            logs.extend(self._log_from_queue(stderr_queue))

            # Check for errors
            try:
                error_msg = error_queue.get_nowait()
                self.exit_code = 1
                logs.append(f"ERROR: {error_msg}")
            except queue.Empty:
                self.exit_code = 0

            # Return all logs as a string for Gradio to display
            yield "\n".join(logs)

        return wrapped
