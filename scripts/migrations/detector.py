import json
import os
import sqlite3

from scripts.migrations.v1_to_v2 import V1ToV2Migration
from scripts.migrations.v2_to_v3 import V2ToV3Migration
from scripts.migrations.v3_to_v4 import V3ToV4Migration
from scripts.migrations.v4_to_v5 import V4ToV5Migration


MIGRATIONS = {
    1: V1ToV2Migration(),
    2: V2ToV3Migration(),
    3: V3ToV4Migration(),
    4: V4ToV5Migration(),
}

DEFAULT_STATE_JSON_PATHS = [
    "logs/state.json",
]

DEFAULT_CONFIG_PATHS = [
    "config/config.toml",
    "config.toml",
]


def _get_project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_version_major():
    version_path = os.path.join(_get_project_root(), "VERSION")
    with open(version_path, "r", encoding="utf-8") as f:
        version_str = f.read().strip()
    return int(version_str.split(".")[0])


def _resolve_existing_paths(candidates):
    return [p for p in candidates if os.path.exists(p)]


def detect_version(db_path):
    features = set()

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT COUNT(*) FROM file_state").fetchone()
            if row and row[0] > 0:
                features.add("sqlite_has_data")
            conn.close()
        except Exception:
            pass

    for path in _resolve_existing_paths(DEFAULT_STATE_JSON_PATHS):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if not data:
            continue

        first_val = next(iter(data.values()))
        first_key = next(iter(data.keys()))

        if set(data.keys()) & {"failures", "ffmpeg_failures", "success_time"}:
            features.add("state_categorized")
        if isinstance(first_val, int):
            features.add("state_flat_int")
        if isinstance(first_val, dict):
            if "success_time" in first_val:
                features.add("state_flat_with_success_time")
            if "ffmpeg_failures" in first_val:
                features.add("state_flat_with_ffmpeg_failures")
            if "failures" in first_val:
                features.add("state_flat_with_failures")

    for path in _resolve_existing_paths(DEFAULT_CONFIG_PATHS):
        try:
            import toml

            config_data = toml.load(path)
        except Exception:
            continue

        tasks = config_data.get("tasks", [])
        global_cfg = config_data.get("global", {})
        first_task = tasks[0] if tasks else {}

        if "source_dir" in first_task:
            features.add("config_has_source_dir")
        if "monitor_dir" in first_task:
            features.add("config_has_monitor_dir")
        if "max_retries" in first_task:
            features.add("config_has_max_retries")
        if "suffix" in first_task or "output_format" in first_task:
            features.add("config_has_suffix_format")
        if any(t.get("filter") for t in tasks):
            features.add("config_has_filter")
        if "log_level" in global_cfg:
            features.add("config_has_log_level")
        if "scan_interval" in global_cfg:
            features.add("config_scan_global")

    if "sqlite_has_data" in features:
        return 5

    if "state_categorized" in features:
        return 4

    if "state_flat_with_success_time" in features:
        return 3

    if "state_flat_with_ffmpeg_failures" in features:
        return 2

    if "state_flat_int" in features:
        return 1

    if "state_flat_with_failures" in features:
        return 2

    if "config_has_source_dir" in features:
        return 3

    if "config_has_monitor_dir" in features:
        if "config_has_max_retries" in features:
            return 1
        return 2

    if features:
        return 1

    return read_version_major()


def check_and_migrate(db_path, current_version):
    version_major = read_version_major()

    existing_config_paths = _resolve_existing_paths(DEFAULT_CONFIG_PATHS)
    existing_state_paths = _resolve_existing_paths(DEFAULT_STATE_JSON_PATHS)

    while current_version < version_major:
        next_version = current_version + 1
        migration = MIGRATIONS.get(current_version)
        if migration is None:
            break

        config_path = existing_config_paths[0] if existing_config_paths else None
        migration.run(db_path, config_path, existing_state_paths)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE meta SET value = ? WHERE key = 'user_data_version'",
            (str(next_version),),
        )
        conn.commit()
        conn.close()

        current_version = next_version
