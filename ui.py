from __future__ import annotations

import importlib
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from pc_control.integrations.voice_engine import VoiceCommandMapper


class PCControlUI:
    """Professional desktop control center for non-technical users."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Camera Control Project • Professional Control Center")
        self.root.geometry("1180x760")
        self.root.minsize(1040, 700)
        self.root.configure(bg="#eef2ff")

        self.process: subprocess.Popen[str] | None = None
        self.voice_mapper = VoiceCommandMapper()

        self._build_style()
        self._build_layout()
        self._refresh_runtime_state()
        self._run_health_checks()

    def _build_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background="white")
        style.configure("Title.TLabel", background="white", foreground="#0f172a", font=("Segoe UI", 20, "bold"))
        style.configure("Body.TLabel", background="white", foreground="#334155", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="white", foreground="#1e293b", font=("Segoe UI", 13, "bold"))
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.configure("StatusOk.TLabel", background="white", foreground="#047857", font=("Segoe UI", 10, "bold"))
        style.configure("StatusWarn.TLabel", background="white", foreground="#b45309", font=("Segoe UI", 10, "bold"))

    def _build_layout(self) -> None:
        wrap = ttk.Frame(self.root, padding=16)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=3)
        wrap.columnconfigure(1, weight=2)
        wrap.rowconfigure(1, weight=1)

        self._build_header(wrap)
        self._build_left_panel(wrap)
        self._build_right_panel(wrap)

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Card.TFrame", padding=14)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Camera Control Professional Window", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Important: python main.py runs backend only. Use this window (python ui.py) for guided control.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.status_label = ttk.Label(header, text="Status: Idle", style="StatusWarn.TLabel")
        self.status_label.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_left_panel(self, parent: ttk.Frame) -> None:
        left = ttk.Frame(parent, style="Card.TFrame", padding=14)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(1, weight=1)
        left.rowconfigure(8, weight=1)

        ttk.Label(left, text="1) Run configuration", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(left, text="Config path", style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 6))
        self.config_var = tk.StringVar(value="config/app.json")
        ttk.Entry(left, textvariable=self.config_var).grid(row=1, column=1, sticky="ew", pady=(10, 6))

        self.dry_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Safe mode (dry run, no real mouse/keyboard action)", variable=self.dry_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=4
        )

        ttk.Label(left, text="Auto stop (seconds)", style="Body.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        self.duration_var = tk.StringVar(value="30")
        ttk.Entry(left, textvariable=self.duration_var).grid(row=3, column=1, sticky="ew", pady=4)

        control_row = ttk.Frame(left, style="Card.TFrame")
        control_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 8))
        self.start_btn = ttk.Button(control_row, text="Start App", style="Run.TButton", command=self.start_control)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(control_row, text="Stop App", command=self.stop_control, state="disabled")
        self.stop_btn.pack(side="left", padx=8)
        ttk.Button(control_row, text="Check Voice Setup", command=self._run_health_checks).pack(side="left", padx=8)

        ttk.Label(left, text="2) Environment checks", style="Header.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 4))
        self.health_text = tk.Text(left, height=7, bg="#f8fafc", fg="#0f172a", wrap="word")
        self.health_text.grid(row=6, column=0, columnspan=2, sticky="nsew")

        ttk.Label(left, text="3) Live app console", style="Header.TLabel").grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 4))
        self.console = tk.Text(left, height=13, bg="#0f172a", fg="#e2e8f0", insertbackground="white", wrap="word")
        self.console.grid(row=8, column=0, columnspan=2, sticky="nsew")
        self.console.configure(state="disabled")
        self._append_console("Welcome. Keep Safe mode ON for first run, then click Start App.")

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        right = ttk.Frame(parent, style="Card.TFrame", padding=14)
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        ttk.Label(right, text="Quick user guide", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        guide = (
            "1. Run this UI with: python ui.py\n"
            "2. Keep Safe mode checked for your first tests.\n"
            "3. Click Start App and wait for startup logs.\n"
            "4. Use gestures or the voice phrases listed below.\n"
            "5. Stop App before closing this window."
        )
        ttk.Label(right, text=guide, style="Body.TLabel", justify="left").grid(row=1, column=0, sticky="w", pady=(6, 10))

        ttk.Label(right, text="Voice phrases -> exact action", style="Header.TLabel").grid(row=2, column=0, sticky="nw")
        columns = ("phrase", "command", "action")
        self.voice_table = ttk.Treeview(right, columns=columns, show="headings", height=16)
        self.voice_table.heading("phrase", text="What you say")
        self.voice_table.heading("command", text="Internal command")
        self.voice_table.heading("action", text="What app will do")
        self.voice_table.column("phrase", width=150, anchor="w")
        self.voice_table.column("command", width=165, anchor="w")
        self.voice_table.column("action", width=190, anchor="w")
        self.voice_table.grid(row=3, column=0, sticky="nsew", pady=(8, 0))

        for phrase, command, action in self.voice_mapper.reference():
            self.voice_table.insert("", "end", values=(phrase, command, action))

    def _append_console(self, text: str) -> None:
        self.console.configure(state="normal")
        self.console.insert("end", f"{text}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def _set_health(self, lines: list[str]) -> None:
        self.health_text.configure(state="normal")
        self.health_text.delete("1.0", "end")
        self.health_text.insert("end", "\n".join(lines))
        self.health_text.configure(state="disabled")

    def _run_health_checks(self) -> None:
        lines: list[str] = []

        config_path = Path(self.config_var.get().strip()) if self.config_var.get().strip() else None
        if config_path and config_path.exists():
            lines.append(f"✅ Config file found: {config_path}")
        else:
            lines.append("⚠️ Config file not found. Fix path before start.")

        for module_name in ("speech_recognition", "pyaudio"):
            try:
                importlib.import_module(module_name)
                lines.append(f"✅ Python module installed: {module_name}")
            except Exception as exc:
                lines.append(f"❌ Missing module: {module_name} ({exc})")

        if any(line.startswith("❌ Missing module: pyaudio") for line in lines):
            lines.append("ℹ️ Voice will not work until PyAudio is installed.")
            lines.append("ℹ️ Windows tip: pip install pipwin && pipwin install pyaudio")

        lines.append("ℹ️ main.py does not show a window. Use ui.py for this control panel.")
        self._set_health(lines)

    def _build_command(self) -> list[str]:
        command = [sys.executable, "main.py"]

        config_path = self.config_var.get().strip()
        if config_path:
            command.extend(["--config", config_path])

        duration = self.duration_var.get().strip()
        if duration:
            if not duration.isdigit():
                raise ValueError("Auto stop must be a whole number.")
            command.extend(["--duration", duration])

        if self.dry_var.get():
            command.append("--dry-run")

        return command

    def start_control(self) -> None:
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Already running", "Application is already running.")
            return

        config_path = self.config_var.get().strip()
        if config_path and not Path(config_path).exists():
            messagebox.showerror("Config error", f"Config path not found: {config_path}")
            return

        try:
            command = self._build_command()
        except ValueError as exc:
            messagebox.showerror("Input error", str(exc))
            return

        self._append_console(f"Starting: {' '.join(command)}")
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        self._refresh_runtime_state()
        self.root.after(100, self._poll_process_output)

    def stop_control(self) -> None:
        if not self.process or self.process.poll() is not None:
            self._append_console("No active process to stop.")
            return
        self._append_console("Stopping application...")
        self.process.terminate()
        self.root.after(200, self._refresh_runtime_state)

    def _poll_process_output(self) -> None:
        if not self.process:
            return

        if self.process.stdout:
            line = self.process.stdout.readline()
            if line:
                self._append_console(line.rstrip())

        if self.process.poll() is None:
            self.root.after(120, self._poll_process_output)
        else:
            self._append_console(f"Application exited with code {self.process.returncode}.")
            self._refresh_runtime_state()

    def _refresh_runtime_state(self) -> None:
        running = bool(self.process and self.process.poll() is None)
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        if running:
            self.status_label.configure(text="Status: Running", style="StatusOk.TLabel")
        else:
            self.status_label.configure(text="Status: Idle", style="StatusWarn.TLabel")


if __name__ == "__main__":
    root = tk.Tk()
    app = PCControlUI(root)
    root.mainloop()
