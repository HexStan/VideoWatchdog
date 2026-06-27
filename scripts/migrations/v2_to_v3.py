import os

from scripts.migrations._base import Migration, read_state_json, write_state_json


MIGRATION_COMMENT = (
    "# MIGRATION: 字段已自动重命名（monitor_dir→source_dir, output_dir→dest_dir, "
    "processed_dir→backup_dir）\n"
    "# MIGRATION: scan_interval 已从任务级移至全局；suffix/output_format 已内联至 ffmpeg_cmd\n"
    "# MIGRATION: 请人工确认 ffmpeg_cmd 中的 {output} 路径是否正确\n"
)


class V2ToV3Migration(Migration):
    name = "v2_to_v3"
    from_version = 2
    to_version = 3

    def migrate_state(self, db_path, state_json_paths):
        for path in state_json_paths:
            if not os.path.exists(path):
                continue
            data = read_state_json(path)
            if not data:
                continue

            for filepath, val in data.items():
                if isinstance(val, dict) and "success_time" not in val:
                    val["success_time"] = None
                elif isinstance(val, int):
                    data[filepath] = {
                        "failures": val,
                        "ffmpeg_failures": 0,
                        "success_time": None,
                    }

            write_state_json(path, data)

    def migrate_config(self, config_path, config_dict):
        global_cfg = config_dict.setdefault("global", {})
        tasks = config_dict.get("tasks", [])
        if not tasks:
            return config_dict

        scan_intervals = []
        for task in tasks:
            if "monitor_dir" in task:
                task["source_dir"] = task.pop("monitor_dir")
            if "output_dir" in task:
                task["dest_dir"] = task.pop("output_dir")
            if "processed_dir" in task:
                task["backup_dir"] = task.pop("processed_dir")

            if "scan_interval" in task:
                scan_intervals.append(task.pop("scan_interval"))

            suffix = task.pop("suffix", "")
            output_format = task.pop("output_format", "")
            if suffix or output_format:
                if suffix and output_format:
                    ext = f"-{suffix}.{output_format}"
                elif output_format:
                    ext = f".{output_format}"
                else:
                    ext = f"-{suffix}"

                ffmpeg_cmd = task.get("ffmpeg_cmd", "")
                task["ffmpeg_cmd"] = ffmpeg_cmd.replace("{output}", "{output}" + ext)

            if "remove_source" not in task:
                task["remove_source"] = False
            if "source_expired_minutes" not in task:
                task["source_expired_minutes"] = 0

        if scan_intervals and "scan_interval" not in global_cfg:
            global_cfg["scan_interval"] = scan_intervals[0]

        if "log_level" not in global_cfg:
            global_cfg["log_level"] = "INFO"

        return config_dict
