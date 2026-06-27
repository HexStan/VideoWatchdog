import os

from scripts.migrations._base import Migration, read_state_json, write_state_json


class V3ToV4Migration(Migration):
    name = "v3_to_v4"
    from_version = 3
    to_version = 4

    def migrate_state(self, db_path, state_json_paths):
        for path in state_json_paths:
            if not os.path.exists(path):
                continue
            try:
                data = read_state_json(path)
            except Exception:
                continue
            if not data or not isinstance(data, dict):
                continue

            top_keys = set(data.keys())
            if top_keys & {"failures", "ffmpeg_failures", "success_time"}:
                continue

            new_state = {
                "failures": {},
                "ffmpeg_failures": {},
                "success_time": {},
            }
            for filepath, val in data.items():
                if isinstance(val, dict):
                    new_state["failures"][filepath] = val.get("failures", 0)
                    new_state["ffmpeg_failures"][filepath] = val.get(
                        "ffmpeg_failures", 0
                    )
                    st = val.get("success_time")
                    if st is not None:
                        new_state["success_time"][filepath] = st
                elif isinstance(val, int):
                    new_state["failures"][filepath] = val

            write_state_json(path, new_state)

    def migrate_config(self, config_path, config_dict):
        return config_dict
