"""Tkinter GUI for KMZ to Shapefile converter."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from typing import List, Optional

from kmz2shapefile.converter import KMZConverter
from kmz2shapefile.exceptions import ConversionError


class KMZ2ShapefileApp:
    """Main GUI application for KMZ to Shapefile conversion."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KMZ to Shapefile Converter")
        self.root.geometry("550x320")
        self.root.minsize(450, 280)

        # State
        self.input_path: Optional[Path] = None
        self.output_path: Optional[Path] = None
        self.conversion_thread: Optional[threading.Thread] = None
        self.is_converting = False
        self.result: Optional[List[Path]] = None
        self.conversion_error: Optional[Exception] = None

        # Tkinter variables
        self.skip_null_var = tk.BooleanVar(value=True)
        self.verbose_var = tk.BooleanVar(value=False)

        self._create_widgets()
        self._configure_grid()

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Input file row
        ttk.Label(main_frame, text="Input File:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.input_entry = ttk.Entry(main_frame, state="readonly", width=50)
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.input_btn = ttk.Button(
            main_frame, text="Browse...", command=self._browse_input
        )
        self.input_btn.grid(row=0, column=2, pady=5)

        # Output file row
        ttk.Label(main_frame, text="Output Base:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.output_entry = ttk.Entry(main_frame, state="readonly", width=50)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.output_btn = ttk.Button(
            main_frame, text="Browse...", command=self._browse_output
        )
        self.output_btn.grid(row=1, column=2, pady=5)

        # Output note
        note_label = ttk.Label(
            main_frame,
            text="Note: Output will be split by geometry type (e.g., output_point.shp, output_line.shp)",
            foreground="gray"
        )
        note_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 5))

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        self.skip_null_check = ttk.Checkbutton(
            options_frame, text="Skip null geometries", variable=self.skip_null_var
        )
        self.skip_null_check.grid(row=0, column=0, sticky="w", padx=10)

        self.verbose_check = ttk.Checkbutton(
            options_frame, text="Verbose mode", variable=self.verbose_var
        )
        self.verbose_check.grid(row=0, column=1, sticky="w", padx=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame, mode="indeterminate", length=300
        )
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky="ew", pady=5)

        # Status label
        self.status_label = ttk.Label(main_frame, text="Status: Ready")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=5)

        # Convert button
        self.convert_btn = ttk.Button(
            main_frame, text="Convert", command=self._start_conversion
        )
        self.convert_btn.grid(row=6, column=0, columnspan=3, pady=15)

        # Configure column weights
        main_frame.columnconfigure(1, weight=1)

    def _configure_grid(self):
        """Configure grid weights for responsive resizing."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _browse_input(self):
        """Open file dialog for input file selection."""
        filepath = filedialog.askopenfilename(
            title="Select KMZ or KML file",
            filetypes=[
                ("KMZ/KML files", "*.kmz *.kml"),
                ("KMZ files", "*.kmz"),
                ("KML files", "*.kml"),
                ("All files", "*.*"),
            ],
        )
        if filepath:
            self.input_path = Path(filepath)
            self.input_entry.config(state="normal")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filepath)
            self.input_entry.config(state="readonly")

            # Auto-suggest output base name
            if not self.output_path:
                suggested = self.input_path.with_suffix('')
                self._set_output_path(suggested)

    def _browse_output(self):
        """Open file dialog for output base selection."""
        initial_name = "output"
        initial_dir = None
        if self.input_path:
            initial_name = self.input_path.stem
            initial_dir = str(self.input_path.parent)

        filepath = filedialog.asksaveasfilename(
            title="Select output base name",
            initialfile=initial_name,
            initialdir=initial_dir,
        )
        if filepath:
            # Remove any extension the user might have added
            output_base = Path(filepath)
            if output_base.suffix:
                output_base = output_base.with_suffix('')
            self._set_output_path(output_base)

    def _set_output_path(self, path: Path):
        """Set the output path and update display."""
        self.output_path = path
        self.output_entry.config(state="normal")
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, str(path))
        self.output_entry.config(state="readonly")

    def _set_ui_converting(self, converting: bool):
        """Enable or disable UI elements during conversion."""
        state = "disabled" if converting else "normal"
        self.input_btn.config(state=state)
        self.output_btn.config(state=state)
        self.convert_btn.config(state=state)
        self.skip_null_check.config(state=state)
        self.verbose_check.config(state=state)

    def _start_conversion(self):
        """Start conversion in background thread."""
        if self.is_converting:
            return

        if not self.input_path:
            messagebox.showerror("Error", "Please select an input file")
            return

        if not self.output_path:
            messagebox.showerror("Error", "Please select an output location")
            return

        self.is_converting = True
        self._set_ui_converting(True)
        self.status_label.config(text="Status: Converting...")
        self.progress_bar.start(10)

        # Reset result
        self.result = None
        self.conversion_error = None

        # Create and start worker thread
        self.conversion_thread = threading.Thread(
            target=self._conversion_worker, daemon=True
        )
        self.conversion_thread.start()

        # Start polling for completion
        self._poll_conversion()

    def _conversion_worker(self):
        """Worker thread that performs the actual conversion."""
        try:
            converter = KMZConverter()

            if self.verbose_var.get():
                print(f"Converting: {self.input_path}")
                print(f"Output base: {self.output_path}")
                print(f"Skip null: {self.skip_null_var.get()}")

            self.result = converter.convert(
                input_path=self.input_path,
                output_path=self.output_path,
                verbose=self.verbose_var.get(),
                skip_null_geometry=self.skip_null_var.get(),
            )

            if self.verbose_var.get():
                print(f"Created {len(self.result)} Shapefile(s)")

        except ConversionError as e:
            self.conversion_error = e
        except Exception as e:
            self.conversion_error = Exception(f"Unexpected error: {e}")

    def _poll_conversion(self):
        """Poll for conversion thread completion using after()."""
        if self.conversion_thread and self.conversion_thread.is_alive():
            # Check again in 100ms
            self.root.after(100, self._poll_conversion)
        else:
            # Conversion finished
            self._on_conversion_complete()

    def _on_conversion_complete(self):
        """Handle conversion completion on main thread."""
        self.is_converting = False
        self._set_ui_converting(False)
        self.progress_bar.stop()

        if self.conversion_error:
            messagebox.showerror("Conversion Error", str(self.conversion_error))
            self.status_label.config(text="Status: Error")
        else:
            file_count = len(self.result) if self.result else 0
            file_list = "\n".join(str(f) for f in self.result) if self.result else ""
            messagebox.showinfo(
                "Success",
                f"Created {file_count} Shapefile(s):\n\n{file_list}"
            )
            self.status_label.config(text=f"Status: Created {file_count} Shapefile(s)")


def main():
    """Main entry point for GUI application."""
    # Enable DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    # Set window icon (removes default Tk icon on Windows)
    try:
        root.iconbitmap(default="")
    except tk.TclError:
        pass

    KMZ2ShapefileApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
