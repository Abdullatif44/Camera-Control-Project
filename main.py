from __future__ import annotations

import argparse
import signal
import sys
import time

from pc_control.app import bootstrap_default_files, create_application


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enterprise PC Control Orchestrator")
    parser.add_argument("--config", default=None, help="Path to JSON config file.")
    parser.add_argument("--dry-run", action="store_true", help="Do not perform real mouse/keyboard actions.")
    parser.add_argument("--duration", type=int, default=0, help="Optional auto-stop duration in seconds.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    bootstrap_default_files()
    app = create_application(config_path=args.config, dry_run=args.dry_run)

    stopping = False

    def _handle_signal(signum, _frame):
        nonlocal stopping
        if stopping:
            return
        stopping = True
        app.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    app.start()

    if args.duration > 0:
        end = time.time() + args.duration
        while time.time() < end and app.state.is_running:
            time.sleep(0.2)
        app.stop()
        return 0

    while app.state.is_running:
        time.sleep(0.2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
