from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


class PCControlUI:
    """Desktop control center for launching and guiding users through the app."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Camera Control Project • Control Center")
        self.root.geometry("1024x700")
        self.root.minsize(900, 620)
        self.root.configure(bg="#f3f6fb")

        self.process: subprocess.Popen[str] | None = None

        self._build_style()
        self._build_layout()
        self._update_runtime_status()

    def _build_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("Heading.TLabel", background="white", font=("Segoe UI", 18, "bold"), foreground="#1f2937")
        style.configure("SubHeading.TLabel", background="white", font=("Segoe UI", 11), foreground="#4b5563")
        style.configure("StatusOk.TLabel", background="white", font=("Segoe UI", 11, "bold"), foreground="#047857")
        style.configure("StatusWarn.TLabel", background="white", font=("Segoe UI", 11, "bold"), foreground="#b45309")
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=(12, 8))

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(1, weight=1)

        self._build_header(container)
        self._build_control_panel(container)
        self._build_guide_panel(container)

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Card.TFrame", padding=16)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Camera Control Professional Window",
            style="Heading.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Start, monitor, and learn the app from one dashboard. No technical background required.",
            style="SubHeading.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.status_pill = ttk.Label(header, text="Status: Idle", style="StatusWarn.TLabel")
        self.status_pill.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_control_panel(self, parent: ttk.Frame) -> None:
        left = ttk.Frame(parent, style="Card.TFrame", padding=16)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(1, weight=1)
        left.rowconfigure(8, weight=1)

        ttk.Label(left, text="Run settings", style="Heading.TLabel", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )

        ttk.Label(left, text="Config file:", style="SubHeading.TLabel").grid(row=1, column=0, sticky="w", pady=(14, 6))
        self.config_path_var = tk.StringVar(value="config/app.json")
        ttk.Entry(left, textvariable=self.config_path_var).grid(row=1, column=1, sticky="ew", pady=(14, 6))

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Safe mode (dry run)", variable=self.dry_run_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(6, 6)
        )

        ttk.Label(left, text="Auto-stop (seconds, optional):", style="SubHeading.TLabel").grid(
            row=3, column=0, sticky="w", pady=(6, 6)
        )
        self.duration_var = tk.StringVar(value="30")
        ttk.Entry(left, textvariable=self.duration_var).grid(row=3, column=1, sticky="ew", pady=(6, 6))

        button_row = ttk.Frame(left, style="Card.TFrame")
        button_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 10))

        self.start_button = ttk.Button(button_row, text="Start App", style="Primary.TButton", command=self.start_control)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(button_row, text="Stop App", command=self.stop_control, state="disabled")
        self.stop_button.pack(side="left", padx=8)

        ttk.Label(left, text="Live console", style="SubHeading.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 6))
        self.console = tk.Text(left, height=14, bg="#0f172a", fg="#e2e8f0", insertbackground="white", wrap="word")
        self.console.grid(row=6, column=0, columnspan=2, sticky="nsew")
        self.console.configure(state="disabled")

        self._append_console("Welcome! Configure options and click 'Start App'.")

    def _build_guide_panel(self, parent: ttk.Frame) -> None:
        right = ttk.Frame(parent, style="Card.TFrame", padding=16)
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Quick start guide", style="Heading.TLabel", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        guide_steps = [
            "1) Verify camera and microphone permissions on your computer.",
            "2) Leave Safe mode checked for your first run.",
            "3) Click Start App and watch the live console for progress.",
            "4) Use hand gestures or voice commands once authentication completes.",
            "5) Press Stop App before closing this window.",
        ]

        for i, step in enumerate(guide_steps, start=1):
            ttk.Label(right, text=step, style="SubHeading.TLabel", wraplength=320, justify="left").grid(
                row=i, column=0, sticky="w", pady=(8 if i == 1 else 6, 0)
            )

        ttk.Separator(right).grid(row=7, column=0, sticky="ew", pady=16)

        ttk.Label(right, text="Feature overview", style="Heading.TLabel", font=("Segoe UI", 14, "bold")).grid(
            row=8, column=0, sticky="w"
        )
        feature_text = (
            "• Gesture control: move cursor, click, scroll, drag\n"
            "• Voice control: volume, mute, lock commands\n"
            "• Security: allow-list command validation\n"
            "• Metrics and logs: runtime observability"
        )
        ttk.Label(right, text=feature_text, style="SubHeading.TLabel", justify="left").grid(
            row=9, column=0, sticky="w", pady=(8, 0)
        )

    def _append_console(self, text: str) -> None:
        self.console.configure(state="normal")
        self.console.insert("end", f"{text}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def _build_command(self) -> list[str]:
        command = [sys.executable, "main.py"]
        config_path = self.config_path_var.get().strip()
        if config_path:
            command.extend(["--config", config_path])

        duration = self.duration_var.get().strip()
        if duration:
            if not duration.isdigit():
                raise ValueError("Auto-stop must be a whole number (seconds).")
            command.extend(["--duration", duration])

        if self.dry_run_var.get():
            command.append("--dry-run")

        return command

    def start_control(self) -> None:
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Already running", "The app is already running.")
            return

        config_path = self.config_path_var.get().strip()
        if config_path and not Path(config_path).exists():
            messagebox.showerror("Config file missing", f"Could not find config file: {config_path}")
            return

        try:
            command = self._build_command()
        except ValueError as err:
            messagebox.showerror("Invalid setting", str(err))
            return

        self._append_console(f"Starting command: {' '.join(command)}")

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._set_status(running=True)
        self.root.after(150, self._read_process_output)

    def stop_control(self) -> None:
        if not self.process or self.process.poll() is not None:
            self._append_console("No running process to stop.")
            return

        self._append_console("Stopping application...")
        self.process.terminate()
        self.root.after(300, self._update_runtime_status)

    def _read_process_output(self) -> None:
        if not self.process:
            return

        if self.process.stdout:
            line = self.process.stdout.readline()
            if line:
                self._append_console(line.rstrip())

        if self.process.poll() is None:
            self.root.after(150, self._read_process_output)
        else:
            self._append_console(f"Application exited with code {self.process.returncode}.")
            self._update_runtime_status()

    def _set_status(self, running: bool) -> None:
        if running:
            self.status_pill.configure(text="Status: Running", style="StatusOk.TLabel")
        else:
            self.status_pill.configure(text="Status: Idle", style="StatusWarn.TLabel")

    def _update_runtime_status(self) -> None:
        is_running = bool(self.process and self.process.poll() is None)
        self.start_button.configure(state="disabled" if is_running else "normal")
        self.stop_button.configure(state="normal" if is_running else "disabled")
        self._set_status(is_running)


if __name__ == "__main__":
    root = tk.Tk()
    app = PCControlUI(root)
    root.mainloop()
