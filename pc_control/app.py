from __future__ import annotations

from pathlib import Path

from pc_control.core.config import AppConfig, load_first_available_config
from pc_control.core.logging_utils import configure_logging
from pc_control.services.orchestrator import AppOrchestrator


def create_application(config_path: str | None = None, dry_run: bool = False) -> AppOrchestrator:
    if config_path:
        config = AppConfig.from_file(config_path)
    else:
        config = load_first_available_config()

    configure_logging(
        level=config.logging.level,
        path=config.logging.path,
        rotation_megabytes=config.logging.rotation_megabytes,
        backup_count=config.logging.backup_count,
    )
    return AppOrchestrator(config, dry_run=dry_run)


def bootstrap_default_files() -> None:
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    sample_path = config_dir / "app.json"
    if sample_path.exists():
        return
    default = AppConfig().to_dict()
    import json

    sample_path.write_text(json.dumps(default, indent=2), encoding="utf-8")
