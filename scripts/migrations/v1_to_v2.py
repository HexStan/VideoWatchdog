import os

from scripts.migrations._base import Migration, read_state_json, write_state_json


MIGRATION_COMMENT = (
    "# MIGRATION: 已自动添加 fallback_count 和 ffmpeg_cmd_fallback 字段\n"
)


class V1ToV2Migration(Migration):
    name = "v1_to_v2"
    from_version = 1
    to_version = 2

    def migrate_state(self, db_path, state_json_paths):
        for path in state_json_paths:
            if not os.path.exists(path):
                continue
            data = read_state_json(path)
            if not data:
                continue

            first_val = next(iter(data.values()), None)
            if not isinstance(first_val, int):
                continue

            new_state = {}
            for filepath, val in data.items():
                if isinstance(val, int):
                    new_state[filepath] = {
                        "failures": val,
                        "ffmpeg_failures": 0,
                    }
                else:
                    new_state[filepath] = val

            write_state_json(path, new_state)

    def migrate_config(self, config_path, config_dict):
        global_cfg = config_dict.setdefault("global", {})
        tasks = config_dict.get("tasks", [])
        if not tasks:
            return config_dict

        for task in tasks:
            if "max_retries" in task:
                task["failure_count"] = task.pop("max_retries")
            if "failure_count" not in task:
                task["failure_count"] = 3
            if "fallback_count" not in task:
                task["fallback_count"] = 0
            if "ffmpeg_cmd_fallback" not in task:
                task["ffmpeg_cmd_fallback"] = ""

        return config_dict
