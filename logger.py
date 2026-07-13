import os
from datetime import datetime


class MoveLogger:
    """Writes every move (or error) to a plain-text log."""

    def __init__(self, log_file="organizer.log"):
        self.log_file = log_file
        # make sure the file exists
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"--- Log started {self._now()} ---\n")

    @staticmethod
    def _now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_move(self, source, destination):
        line = f"[{self._now()}] MOVED: {source} -> {destination}\n"
        self._write(line)
        return line

    def log_error(self, source, message):
        line = f"[{self._now()}] ERROR: {source} | {message}\n"
        self._write(line)
        return line

    def log_info(self, message):
        line = f"[{self._now()}] INFO: {message}\n"
        self._write(line)
        return line

    def log_undo(self, destination, source):
        line = f"[{self._now()}] UNDO: {destination} -> {source}\n"
        self._write(line)
        return line

    def _write(self, line):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line)

    def read_all(self):
        with open(self.log_file, "r", encoding="utf-8") as f:
            return f.read()
