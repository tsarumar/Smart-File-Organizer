import os
import shutil
import threading

from classifier import FileClassifier
from history import HistoryManager
from logger import MoveLogger


class FileOrganizer:
    """
    Core class. Walks through a folder, classifies each file,
    moves it into the right subfolder, and logs everything.
    Supports a stop flag so the GUI can interrupt long runs.
    """

    def __init__(self, folder=None, classifier=None, logger=None, history=None):
        self.folder = folder
        self.classifier = classifier if classifier else FileClassifier()
        self.logger = logger if logger else MoveLogger()
        self.history = history if history else HistoryManager()
        self._stop_flag = threading.Event()

    # --- controls ---------------------------------------------------------

    def set_folder(self, folder):
        if not os.path.isdir(folder):
            raise NotADirectoryError(f"{folder} is not a valid folder")
        self.folder = folder

    def request_stop(self):
        self._stop_flag.set()

    def reset_stop(self):
        self._stop_flag.clear()

    # --- main work --------------------------------------------------------

    def organize(self, on_move=None, on_error=None):
        """
        Sort all files in self.folder into subfolders.
        Optional callbacks report progress back to the GUI.
        Returns a summary dict.
        """
        if not self.folder:
            raise ValueError("No folder selected.")

        if not os.path.isdir(self.folder):
            raise NotADirectoryError(f"{self.folder} is not a valid folder")

        self.reset_stop()
        moved = 0
        skipped = 0
        errors = 0

        entries = os.listdir(self.folder)
        self.logger.log_info(
            f"Started organizing '{self.folder}' ({len(entries)} entries)"
        )

        for name in entries:
            if self._stop_flag.is_set():
                self.logger.log_info("Stop requested by user.")
                break

            source = os.path.join(self.folder, name)

            # skip folders and hidden system stuff
            if os.path.isdir(source):
                skipped += 1
                continue
            if name.startswith("."):
                skipped += 1
                continue

            try:
                category = self.classifier.classify(name)
                dest_dir = os.path.join(self.folder, category)
                os.makedirs(dest_dir, exist_ok=True)

                dest_path = os.path.join(dest_dir, name)
                dest_path = self._handle_conflict(dest_path)

                shutil.move(source, dest_path)
                self.history.add(source, dest_path)
                self.logger.log_move(source, dest_path)

                if on_move:
                    on_move(source, dest_path)
                moved += 1

            except PermissionError as e:
                errors += 1
                self.logger.log_error(source, f"Permission denied: {e}")
                if on_error:
                    on_error(source, str(e))
            except (shutil.Error, OSError) as e:
                errors += 1
                self.logger.log_error(source, str(e))
                if on_error:
                    on_error(source, str(e))

        summary = {"moved": moved, "skipped": skipped, "errors": errors}
        self.logger.log_info(f"Finished. Summary: {summary}")
        return summary

    # --- undo -------------------------------------------------------------

    def undo_last(self):
        record = self.history.undo_last()
        if record:
            self.logger.log_undo(record.destination, record.source)
        return record

    def undo_all(self):
        undone = self.history.undo_all()
        for rec in undone:
            self.logger.log_undo(rec.destination, rec.source)
        return undone

    # --- helpers ----------------------------------------------------------

    @staticmethod
    def _handle_conflict(path):
        """If a file with this name already exists, rename with _1, _2, ..."""
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        counter = 1
        new_path = f"{base}_{counter}{ext}"
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_{counter}{ext}"
        return new_path
