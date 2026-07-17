import os
import sqlite3

from scripts.migrations._base import Migration, backup_file, read_state_json


class V4ToV5Migration(Migration):
    name = "v4_to_v5"
    from_version = 4
    to_version = 5

    def migrate_state(self, db_path, state_json_paths):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS file_state ("
            "    filepath              TEXT PRIMARY KEY,"
            "    success_time          REAL,"
            "    failure_count         INTEGER NOT NULL DEFAULT 0,"
            "    ffmpeg_failure_count  INTEGER NOT NULL DEFAULT 0"
            ")"
        )
        conn.commit()

        for path in state_json_paths:
            if not os.path.exists(path):
                continue
            backup_file(path)
            try:
                data = read_state_json(path)
            except Exception:
                continue

            if not data:
                continue

            if not isinstance(data, dict):
                continue

            if not (set(data.keys()) & {"failures", "ffmpeg_failures", "success_time"}):
                continue

            all_filepaths = set()
            for category in ("failures", "ffmpeg_failures", "success_time"):
                all_filepaths.update(data.get(category, {}).keys())

            for filepath in all_filepaths:
                count = data.get("failures", {}).get(filepath, 0)
                ff_count = data.get("ffmpeg_failures", {}).get(filepath, 0)
                st = data.get("success_time", {}).get(filepath)
                conn.execute(
                    "INSERT OR IGNORE INTO file_state"
                    " (filepath, success_time, failure_count, ffmpeg_failure_count)"
                    " VALUES (?, ?, ?, ?)",
                    (filepath, st, count, ff_count),
                )

        conn.commit()
        conn.close()

    def migrate_config(self, config_path, config_dict):
        tasks = config_dict.get("tasks", [])
        for task in tasks:
            filter_cfg = task.get("filter", {})
            if not isinstance(filter_cfg, dict):
                continue

            old_input = filter_cfg.pop("input_formats", None)
            if old_input and isinstance(old_input, list):
                existing = filter_cfg.get("include_patterns", [])
                new_patterns = _extensions_to_patterns(old_input)
                filter_cfg["include_patterns"] = list(dict.fromkeys(existing + new_patterns))

            old_direct = filter_cfg.pop("direct_move_formats", None)
            if old_direct and isinstance(old_direct, list):
                existing = filter_cfg.get("passthrough_patterns", [])
                new_patterns = _extensions_to_patterns(old_direct)
                filter_cfg["passthrough_patterns"] = list(dict.fromkeys(existing + new_patterns))

            filter_cfg.setdefault("include_patterns", [])
            filter_cfg.setdefault("exclude_patterns", [])
            filter_cfg.setdefault("passthrough_patterns", [])

        return config_dict


def _extensions_to_patterns(formats):
    patterns = []
    for fmt in formats:
        if not isinstance(fmt, str) or not fmt.strip():
            continue
        fmt = fmt.strip().lower()
        if fmt.startswith("."):
            patterns.append(f"*{fmt}")
        else:
            patterns.append(f"*.{fmt}")
    return patterns
