# Camera Control Project (Enterprise Edition)

This project has been upgraded from a quick prototype into an enterprise-structured application with:

- A layered architecture (core / services / integrations).
- Domain models and event-driven orchestration.
- Security allow-list and payload validation.
- Runtime metrics collection and periodic persistence.
- Config-driven behavior with environment-aware defaults.
- Dry-run mode for safe local validation.
- Unit tests for key logic paths.

---

## 1) High-Level Architecture

```text
main.py
  -> app.create_application()
      -> AppConfig loader
      -> logging setup
      -> AppOrchestrator
         -> Authentication phase
         -> Camera stream
         -> Gesture processing loop
         -> Voice recognition loop
         -> Command security validation
         -> Command execution adapter
         -> Event bus + metrics + heartbeat
```

### Layers

1. **Core**
   - `config.py`: typed configuration objects.
   - `models.py`: event and command schemas.
   - `logging_utils.py`: centralized logging setup.

2. **Services**
   - `orchestrator.py`: lifecycle + concurrency + coordination.
   - `security.py`: command allow-list and payload validation.
   - `command_executor.py`: maps domain commands to system actions.
   - `event_bus.py`: decoupled event pub/sub.
   - `metrics.py`: metrics collection and writer.

3. **Integrations**
   - `auth_engine.py`: face-recognition auth boundary.
   - `camera_stream.py`: threaded camera ingestion.
   - `gesture_engine.py`: gesture interpretation logic.
   - `voice_engine.py`: speech recognition listener + mapper.
   - `system_actions.py`: pyautogui/dry-run adapters.

4. **Tests**
   - `pc_control/tests/*`: unit tests for config, security, gesture, executor, event bus, and orchestrator command handling.

---

## 2) Why this is enterprise-oriented now

### a) Separation of concerns

The old version tightly coupled UI + camera + gestures + voice + auth in a single control flow.
Now each concern has explicit boundaries and can be tested independently.

### b) Config-driven runtime

All critical operational values (camera size, thresholds, voice options, auth tolerance, logging, metrics) are configurable.
This supports:

- environment-specific deployment,
- quick tuning,
- safer operations.

### c) Controlled command execution

Commands are now validated by `CommandGuard` before execution.
Only allow-listed commands can run.
Payloads are checked for shape and bounds.

### d) Observability by default

- Structured logs with rotation.
- Event stream for all major lifecycle and command decisions.
- Metrics snapshot persisted on interval.

### e) Testability and deterministic behavior

A dry-run system adapter enables logic verification without moving mouse or changing volume.
Pure-python gesture interpretation logic is unit-tested.

---

## 3) Running the app

### Basic

```bash
python3 main.py --dry-run --duration 10
```

### With explicit config

```bash
python3 main.py --config config/app.json --dry-run
```

### Stop behavior

- `Ctrl+C` triggers graceful shutdown.
- `SIGTERM` also triggers graceful shutdown.

---

## 4) Configuration

A sample config is auto-generated at `config/app.json` if missing.

Example keys:

```json
{
  "environment": "dev",
  "camera": {
    "device_index": 0,
    "width": 1280,
    "height": 720,
    "target_fps": 30,
    "mirrored": true
  },
  "gesture": {
    "hand_max_num": 1,
    "min_detection_confidence": 0.7,
    "min_tracking_confidence": 0.5,
    "click_distance_threshold": 0.045,
    "right_click_distance_threshold": 0.05,
    "double_click_cooldown_seconds": 0.8,
    "drag_hold_threshold_seconds": 0.6,
    "smoothing_alpha": 0.25,
    "deadzone_px": 4
  },
  "voice": {
    "enabled": true,
    "phrase_time_limit_seconds": 4,
    "ambient_noise_adjust_seconds": 1,
    "language": "en-US",
    "command_timeout_seconds": 5
  },
  "auth": {
    "enabled": true,
    "face_image_path": "user.png",
    "acceptance_tolerance": 0.45,
    "max_attempts": 2
  },
  "security": {
    "fail_closed": true,
    "redact_sensitive_logs": true,
    "allowed_commands": [
      "mouse.move",
      "mouse.click.left",
      "mouse.click.right",
      "mouse.double_click",
      "mouse.scroll.up",
      "mouse.scroll.down",
      "system.volume.up",
      "system.volume.down",
      "system.mute.toggle",
      "system.lock"
    ]
  },
  "metrics": {
    "enabled": true,
    "write_interval_seconds": 10,
    "output_path": "runtime/metrics.json"
  },
  "logging": {
    "level": "INFO",
    "path": "runtime/pc_control.log",
    "rotation_megabytes": 5,
    "backup_count": 5
  }
}
```

---

## 5) Operational model

### Startup sequence

1. Logging configured.
2. Event bus started.
3. Metrics writer started.
4. Authentication phase executed.
5. Camera and voice listeners started.
6. Worker loops begin:
   - Gesture loop
   - Voice loop
   - Heartbeat loop

### Shutdown sequence

1. Stop signal set.
2. Worker threads joined.
3. Camera and voice listeners stopped.
4. Shutdown event emitted.
5. Metrics flushed.
6. Event bus stopped.

---

## 6) Security model

- Allow-list based command admission.
- Payload schema-like validation for coordinates and scroll ranges.
- Fail-closed support for unknown actions.

This reduces accidental or malicious command execution.

---

## 7) Extensibility

### Add a new gesture command

1. Add gesture signal in `GestureInterpreter.process`.
2. Add command translation in `AppOrchestrator._commands_from_gesture`.
3. Add allow-list entry in config.
4. Add executor mapping in `CommandExecutor.execute`.
5. Add unit tests.

### Add a new voice phrase

1. Add mapping in `VoiceCommandMapper.map_table`.
2. Add command executor mapping if needed.
3. Add tests for mapping + execution.

---

## 8) Testing

Run all tests:

```bash
python3 -m unittest discover -s pc_control/tests -p 'test_*.py'
```

Syntax validation:

```bash
python3 -m compileall -q .
```

---

## 9) Suggested future hardening

- Add centralized dependency checks and startup diagnostics.
- Add role-based command policies per profile.
- Add encrypted config values for sensitive fields.
- Add telemetry exporters (Prometheus/OpenTelemetry).
- Add replay-safe event audit logs.
- Add resilient retries with exponential backoff for external API paths.
- Introduce plugin framework for gesture/voice providers.
- Add signed configuration bundles for production.

---

## 10) Development notes

- Prefer extending `services` and `integrations` modules rather than adding logic in `main.py`.
- Keep business logic in pure-python modules for easier testing.
- Use `DryRunAdapter` during development to avoid accidental OS interaction.

---

## 11) Migration summary from original prototype

- Moved from single-file workflow to package-based architecture.
- Added robust app lifecycle and coordinated graceful shutdown.
- Added explicit domain model classes.
- Added event bus and runtime metrics.
- Added security gate before system actions.
- Added dry-run mode.
- Added test suite with deterministic behavior.

---

## 12) FAQ

### Q: Does this still support real camera + gesture + voice control?
Yes. Use default adapters and ensure dependencies are installed.

### Q: Can I run this in CI?
Yes. Use `--dry-run` and run unit tests without camera/mic.

### Q: Is authentication mandatory?
No. Disable via config (`auth.enabled=false`) for non-production scenarios.

### Q: How do I tune gesture sensitivity?
Use `gesture.click_distance_threshold`, `gesture.right_click_distance_threshold`, and `gesture.smoothing_alpha`.

### Q: Why an event bus in a local app?
It decouples producers/consumers, simplifies observability, and supports future distributed integrations.

---

## 13) Project Structure

```text
.
├── main.py
├── README.md
├── config/
│   └── app.json (auto-generated)
└── pc_control/
    ├── __init__.py
    ├── app.py
    ├── core/
    │   ├── config.py
    │   ├── logging_utils.py
    │   └── models.py
    ├── integrations/
    │   ├── auth_engine.py
    │   ├── camera_stream.py
    │   ├── gesture_engine.py
    │   ├── system_actions.py
    │   └── voice_engine.py
    ├── services/
    │   ├── command_executor.py
    │   ├── event_bus.py
    │   ├── metrics.py
    │   ├── orchestrator.py
    │   └── security.py
    └── tests/
        ├── test_config_and_security.py
        ├── test_gesture_and_executor.py
        └── test_orchestrator_core.py
```

---

## 14) Dependency notes

Core runtime features depend on:

- `opencv-python`
- `mediapipe`
- `pyautogui`
- `speechrecognition`
- `face_recognition`

Tests avoid requiring those integrations by using pure logic and dry-run abstractions where possible.

---

## 15) Final statement

This upgrade transforms the project from a demo into a maintainable foundation suitable for enterprise-style engineering workflows: modular code, isolated integration boundaries, policy-driven execution, and testable business logic.

---


## 16) Professional desktop window (easy mode)

For non-technical users, launch the visual control center:

```bash
python3 ui.py
```

What you get in the window:

- **Run settings panel**: choose config file, safe mode, and optional auto-stop duration.
- **Start/Stop controls**: one-click lifecycle management for the app.
- **Live console**: see startup/auth/runtime messages in real time.
- **Quick start guide**: clear 5-step instructions for first-time users.
- **Feature overview**: highlights gesture, voice, security, and metrics features.

Recommended first run:

1. Keep **Safe mode (dry run)** enabled.
2. Use a small duration (for example 30 seconds).
3. Click **Start App** and confirm authentication + camera startup in the console.
4. When comfortable, uncheck safe mode for real control actions.


Voice troubleshooting:

- If voice thread fails with `Could not find PyAudio`, install dependencies:
  - `pip install SpeechRecognition pyaudio`
  - On Windows (if wheel build fails): `pip install pipwin && pipwin install pyaudio`
- Use `python3 ui.py` and click **Check Voice Setup** to verify modules.

New voice actions available in this release:

- Volume: up/down/mute
- Mouse clicks: left/right/double
- Scrolling: normal and fast up/down
- Cursor anchors: center, top-left, top-right, bottom-left, bottom-right
- System: lock computer

