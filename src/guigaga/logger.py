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
        """
        Initializes a new instance of the CapturingStream class.

        Args:
          queue (mpQueue): The queue to put the captured lines in.
          *args: Variable length argument list.
          **kwargs: Arbitrary keyword arguments.

        Side Effects:
          Initializes the _queue attribute with the provided queue and the _current_line attribute to an empty string.
        """
        super().__init__(*args, **kwargs)
        self._queue = queue
        self._current_line = ""

    def write(self, s: str) -> int:
        """
        Writes a string to the stream and captures it line by line.

        Args:
          s (str): The string to write.

        Returns:
          int: The number of characters written.

        Side Effects:
          Writes the string to the stream and captures it line by line, putting each line in the queue.

        Notes:
          Normalizes newlines by replacing "\r" with "\\n".
        """
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
        """
        Flushes the stream and captures the current line.

        Side Effects:
          If there is a current line, puts it in the queue and resets the current line to an empty string. Then flushes the stream.
        """
        if self._current_line:
            self._queue.put(self._current_line)
            self._current_line = ""
        super().flush()


def wrap_for_process(fn: Callable, ctx) -> Callable:
    """Wrap the function to capture stdout, stderr, and errors in real-time."""
    stdout_queue = mpQueue()
    stderr_queue = mpQueue()
    error_queue = mpQueue()

    @wraps(fn)
    def _inner(*args, **kwargs):
        with redirect_stdout(CapturingStream(stdout_queue)), redirect_stderr(CapturingStream(stderr_queue)):
            try:
                if ctx:
                    # Use the context within the thread
                    with ctx:
                        fn(*args, **kwargs)
                else:
                    fn(*args, **kwargs)
            except Exception as error:
                msg = (
                    f"Error in '{fn.__name__}':\n" +
                    "\n".join(
                        line.strip("\n")
                        for line in traceback.format_tb(error.__traceback__)
                        if line.strip()
                    ) +
                    f"\n\n{error!s}"
                )
                error_queue.put(msg)

            # Flush final content from buffers
            sys.stdout.flush()
            sys.stderr.flush()

    return stdout_queue, stderr_queue, error_queue, _inner


class Logger:
    """
    A class for logging messages with different levels.

    Attributes:
      process: The process that the logger is logging for.
      exit_code: The exit code of the process.
    """
    def __init__(self):
        """
        Initializes a new instance of the Logger class.

        Side Effects:
          Initializes the process and exit_code attributes to None.
        """
        self.process = None
        self.exit_code = None

    def log(self, message: str, level: str = "INFO"):
        """
        Logs a message with a specified level.

        Args:
          message (str): The message to log.
          level (str, optional): The level of the log. Defaults to "INFO".

        Returns:
          dict: A dictionary containing the message and level.

        Examples:
          >>> logger = Logger()
          >>> logger.log("Hello, World!")
          {"message": "Hello, World!", "level": "INFO"}
        """
        return {"message": message, "level": level}

    def _log_from_queue(self, log_queue) -> Generator[str, None, None]:
        """Fetch logs from the queue and yield them as strings."""
        try:
            while True:
                log = log_queue.get_nowait()
                yield log
        except queue.Empty:
            pass

    def intercept_stdin_stdout(self, fn: Callable, ctx, *, catch_errors) -> Callable:
        """Wrap a function to intercept and yield stdout and stderr using threading."""

        def wrapped(*args, **kwargs) -> str:
            # Pass the context to wrap_for_process
            stdout_queue, stderr_queue, error_queue, wrapped_fn = wrap_for_process(fn, ctx)
            thread = threading.Thread(target=wrapped_fn, args=args, kwargs=kwargs)

            # Start the thread
            thread.start()

            # Collect logs while the thread is running
            logs = []
            while thread.is_alive():
                logs.extend(self._log_from_queue(stdout_queue))
                logs.extend(self._log_from_queue(stderr_queue))
                thread.join(timeout=0.1)

                # Yield logs
                yield "\n".join(logs)

            # After the thread completes, yield any remaining logs
            logs.extend(self._log_from_queue(stdout_queue))
            logs.extend(self._log_from_queue(stderr_queue))

            # Check for errors
            try:
                error_msg = error_queue.get_nowait()
                self.exit_code = 1
                if catch_errors:
                    logs.append(f"ERROR: {error_msg}")
                else:
                    raise Exception(error_msg)
            except queue.Empty:
                self.exit_code = 0

            # Return all logs as a string
            yield "\n".join(logs)

        return wrapped
