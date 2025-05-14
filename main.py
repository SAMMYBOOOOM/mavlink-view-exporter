import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
from xmlExporter import open_xml_exporter

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class MavlinkLauncherGUI:
    def __init__(self, master):
        self.master = master
        master.title("MAVLink Data Plotter (version 1.2)")
        master.geometry("350x200")
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # Control Panel
        self.control_frame = ttk.Frame(master, padding=20)
        self.control_frame.grid(row=0, column=0, sticky='nsew')

        # Developer info and logo
        try:
            icon_path = resource_path("dev.png")
            self.dev_icon = tk.PhotoImage(file=icon_path)
            self.dev_icon = self.dev_icon.subsample(
                max(1, self.dev_icon.width() // 80),
                max(1, self.dev_icon.height() // 80)
            )
            self.dev_label = ttk.Label(self.control_frame, image=self.dev_icon)
            self.dev_label.grid(row=0, column=0, padx=(0, 5), sticky='w')
            ttk.Label(self.control_frame, text="Developed by Sam", font=('Arial', 8, 'italic')).grid(row=0, column=1, sticky='w')
        except Exception as e:
            print(f"Error loading icon: {e}")

        # Buttons
        self.open_button = ttk.Button(
            self.control_frame, 
            text="Open Plotter", 
            command=self.open_plotter
        )
        self.open_button.grid(row=1, column=0, columnspan=2, pady=10, sticky='ew')

        self.export_button = ttk.Button(
        self.control_frame, 
        text="Export XML", 
        command=open_xml_exporter  # Changed from show_export_warning
        )
        self.export_button.grid(row=2, column=0, columnspan=2, pady=5, sticky='ew')

        # Configure grid weights
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=3)

    def open_plotter(self):
        try:
            if getattr(sys, 'frozen', False):
                # If running as compiled executable
                subprocess.Popen([sys.executable, "--plotter"])
            else:
                # If running as .py script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                plotter_script = os.path.join(script_dir, "mavlinkPlotter.py")
                subprocess.Popen([sys.executable, plotter_script])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open plotter:\n{str(e)}")

    def show_export_warning(self):
        messagebox.showinfo(
            "Export Information",
            "Please use the Export button within the plotter window\nto export XML data for specific messages."
        )

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--plotter":
        # Run the plotter directly
        from mavlinkPlotter import run_plotter
        run_plotter()
    else:
        # Run the launcher
        root = tk.Tk()
        app = MavlinkLauncherGUI(root)
        root.mainloop()