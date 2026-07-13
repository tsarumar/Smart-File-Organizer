import os
import shutil
import json
from datetime import datetime


class MoveRecord:
    """One file move. Stored so we can undo it later."""

    def __init__(self, source, destination, timestamp=None):
        self.source = source
        self.destination = destination
        self.timestamp = timestamp if timestamp else datetime.now().isoformat()

    def to_dict(self):
        return {
            "source": self.source,
            "destination": self.destination,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["source"], data["destination"], data["timestamp"])


class HistoryManager:
    """Keeps track of moves and can undo them one by one or all at once."""

    def __init__(self, history_file="history.json"):
        self.history_file = history_file
        self.records = []
        self._load()

    def _load(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = [MoveRecord.from_dict(d) for d in data]
            except (json.JSONDecodeError, KeyError):
                # corrupted history, start fresh
                self.records = []

    def _save(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.records], f, indent=2)

    def add(self, source, destination):
        record = MoveRecord(source, destination)
        self.records.append(record)
        self._save()

    def undo_last(self):
        """Move the most recently moved file back where it came from."""
        if not self.records:
            return None

        record = self.records[-1]

        # if the destination doesn't exist anymore we still pop it
        if not os.path.exists(record.destination):
            self.records.pop()
            self._save()
            raise FileNotFoundError(
                f"Cannot undo: {record.destination} no longer exists."
            )

        # make sure the original folder is still there
        os.makedirs(os.path.dirname(record.source), exist_ok=True)

        # don't overwrite something at the source
        target = record.source
        if os.path.exists(target):
            target = self._resolve_conflict(target)

        shutil.move(record.destination, target)
        self.records.pop()
        self._save()
        return record

    def undo_all(self):
        """Undo everything from newest to oldest. Returns list of undone records."""
        undone = []
        while self.records:
            try:
                rec = self.undo_last()
                if rec:
                    undone.append(rec)
            except (FileNotFoundError, PermissionError, shutil.Error):
                # skip broken ones but keep going
                continue
        return undone

    def clear(self):
        self.records = []
        self._save()

    def count(self):
        return len(self.records)

    @staticmethod
    def _resolve_conflict(path):
        base, ext = os.path.splitext(path)
        counter = 1
        new_path = f"{base}_{counter}{ext}"
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_{counter}{ext}"
        return new_path
