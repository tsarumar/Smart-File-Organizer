"""
Smart File Organizer
Author: Omar Zid
Entry point. Launches the tkinter GUI.
"""
import tkinter as tk

from gui import OrganizerGUI


def main():
    root = tk.Tk()
    app = OrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
