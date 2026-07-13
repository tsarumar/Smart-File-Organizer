import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from organizer import FileOrganizer


class OrganizerGUI:
    """Tkinter front-end for the FileOrganizer."""

    def __init__(self, root):
        self.root = root
        self.root.title("Smart File Organizer")
        self.root.geometry("720x520")
        self.root.minsize(600, 450)

        self.organizer = FileOrganizer()
        self.worker_thread = None

        self._build_widgets()
        self._refresh_history_count()

    # --- widget setup -----------------------------------------------------

    def _build_widgets(self):
        pad = {"padx": 10, "pady": 6}

        # top: folder selection
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", **pad)

        tk.Label(top_frame, text="Folder:").pack(side="left")
        self.folder_var = tk.StringVar()
        self.folder_entry = tk.Entry(top_frame, textvariable=self.folder_var)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=6)

        self.browse_btn = tk.Button(top_frame, text="Browse...", command=self.choose_folder)
        self.browse_btn.pack(side="left")

        # middle: control buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", **pad)

        self.start_btn = tk.Button(
            btn_frame, text="Start", width=12,
            bg="#4CAF50", fg="white", command=self.start_organizing
        )
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = tk.Button(
            btn_frame, text="Stop", width=12, state="disabled",
            bg="#f44336", fg="white", command=self.stop_organizing
        )
        self.stop_btn.pack(side="left", padx=4)

        self.undo_btn = tk.Button(
            btn_frame, text="Undo last", width=12, command=self.undo_last
        )
        self.undo_btn.pack(side="left", padx=4)

        self.undo_all_btn = tk.Button(
            btn_frame, text="Undo all", width=12, command=self.undo_all
        )
        self.undo_all_btn.pack(side="left", padx=4)

        self.clear_log_btn = tk.Button(
            btn_frame, text="Clear log view", width=14, command=self.clear_log_view
        )
        self.clear_log_btn.pack(side="right", padx=4)

        # progress bar
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", **pad)

        # log area
        log_label = tk.Label(self.root, text="Activity:")
        log_label.pack(anchor="w", padx=10)

        self.log_area = scrolledtext.ScrolledText(self.root, height=15, wrap="word")
        self.log_area.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.log_area.configure(state="disabled")

        # status bar
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            anchor="w", bd=1, relief="sunken"
        )
        status_bar.pack(fill="x", side="bottom")

    # --- actions ----------------------------------------------------------

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder to organize")
        if folder:
            self.folder_var.set(folder)
            self._log_line(f"Selected folder: {folder}")

    def start_organizing(self):
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning("No folder", "Please choose a folder first.")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("Invalid folder", "The selected path is not a folder.")
            return

        # confirm before touching real files
        confirm = messagebox.askyesno(
            "Confirm",
            f"Organize all files inside:\n{folder}\n\nContinue?"
        )
        if not confirm:
            return

        try:
            self.organizer.set_folder(folder)
        except NotADirectoryError as e:
            messagebox.showerror("Error", str(e))
            return

        self._set_running(True)
        self.status_var.set("Working...")
        self._log_line(f"--- Started organizing {folder} ---")

        self.worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self.worker_thread.start()

    def stop_organizing(self):
        self.organizer.request_stop()
        self.status_var.set("Stopping...")
        self._log_line("Stop requested.")

    def undo_last(self):
        try:
            record = self.organizer.undo_last()
            if record is None:
                messagebox.showinfo("Undo", "Nothing to undo.")
                return
            self._log_line(f"Undo: {record.destination} -> {record.source}")
            self._refresh_history_count()
        except (FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Undo failed", str(e))
            self._refresh_history_count()

    def undo_all(self):
        if self.organizer.history.count() == 0:
            messagebox.showinfo("Undo all", "Nothing to undo.")
            return

        confirm = messagebox.askyesno(
            "Undo all",
            f"This will reverse {self.organizer.history.count()} moves. Continue?"
        )
        if not confirm:
            return

        undone = self.organizer.undo_all()
        self._log_line(f"Undo all: reversed {len(undone)} moves.")
        self._refresh_history_count()

    def clear_log_view(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

    # --- worker thread ----------------------------------------------------

    def _run_worker(self):
        try:
            summary = self.organizer.organize(
                on_move=self._on_move_callback,
                on_error=self._on_error_callback,
            )
            self.root.after(0, self._on_done, summary)
        except (ValueError, NotADirectoryError) as e:
            self.root.after(0, self._on_error_popup, str(e))

    def _on_move_callback(self, source, dest):
        # tkinter isn't thread-safe, marshal to main thread
        self.root.after(0, self._log_line, f"MOVED: {os.path.basename(source)} -> {dest}")

    def _on_error_callback(self, source, message):
        self.root.after(0, self._log_line, f"ERROR: {source} | {message}")

    def _on_done(self, summary):
        self._set_running(False)
        self.status_var.set(
            f"Done. Moved {summary['moved']}, "
            f"skipped {summary['skipped']}, errors {summary['errors']}."
        )
        self._log_line(
            f"--- Finished. moved={summary['moved']} "
            f"skipped={summary['skipped']} errors={summary['errors']} ---"
        )
        self._refresh_history_count()

    def _on_error_popup(self, message):
        self._set_running(False)
        self.status_var.set("Error.")
        messagebox.showerror("Error", message)

    # --- helpers ----------------------------------------------------------

    def _set_running(self, running):
        if running:
            self.start_btn.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.undo_btn.configure(state="disabled")
            self.undo_all_btn.configure(state="disabled")
            self.progress.start(10)
        else:
            self.start_btn.configure(state="normal")
            self.browse_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.undo_btn.configure(state="normal")
            self.undo_all_btn.configure(state="normal")
            self.progress.stop()

    def _log_line(self, line):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", line + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def _refresh_history_count(self):
        count = self.organizer.history.count()
        current = self.status_var.get()
        # keep status text but append count
        if " | History:" in current:
            current = current.split(" | History:")[0]
        self.status_var.set(f"{current} | History: {count} move(s)")
