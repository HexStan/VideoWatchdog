from dataclasses import dataclass

from modules.filter import FileFilter


@dataclass
class TaskConfig:
    name: str
    source_dir: str
    dest_dir: str
    backup_dir: str
    remove_source: bool
    source_expired_minutes: int
    stable_duration: int
    failure_count: int
    fallback_count: int
    ffmpeg_cmd: str
    ffmpeg_cmd_fallback: str
    filter: FileFilter

    @classmethod
    def from_dict(cls, task_dict: dict, index: int = 0):
        task_dict.setdefault("remove_source", False)
        task_dict.setdefault("source_expired_minutes", 0)

        required_keys = ["source_dir", "dest_dir", "ffmpeg_cmd"]

        for key in required_keys:
            if key not in task_dict:
                raise ValueError(f"任务 {index} 中缺失了必要项: {key}")

        task_dict.setdefault("filter", {})
        f_config = task_dict["filter"]

        f_config.setdefault("file_mtime", 0)
        f_config.setdefault("input_formats", ["mp4"])
        f_config.setdefault("direct_move_formats", [])

        task_dict.setdefault("stable_duration", 0)
        task_dict.setdefault("failure_count", 3)
        task_dict.setdefault("fallback_count", 0)
        task_dict.setdefault("ffmpeg_cmd_fallback", "")
        task_dict.setdefault("name", f"Task {index}")

        f_config["input_formats"] = [
            ext if ext.startswith(".") else f".{ext}"
            for ext in f_config["input_formats"]
        ]
        f_config["direct_move_formats"] = [
            ext if ext.startswith(".") else f".{ext}"
            for ext in f_config["direct_move_formats"]
        ]

        overlap = set(f_config["input_formats"]) & set(f_config["direct_move_formats"])
        if overlap:
            raise ValueError(
                f"任务 {index} 中 input_formats 和 direct_move_formats 不能有重复的格式: {', '.join(overlap)}"
            )

        return cls(
            name=task_dict["name"],
            source_dir=task_dict["source_dir"],
            dest_dir=task_dict["dest_dir"],
            backup_dir=task_dict.get("backup_dir", ""),
            remove_source=task_dict["remove_source"],
            source_expired_minutes=task_dict["source_expired_minutes"],
            stable_duration=task_dict["stable_duration"],
            failure_count=task_dict["failure_count"],
            fallback_count=task_dict["fallback_count"],
            ffmpeg_cmd=task_dict["ffmpeg_cmd"],
            ffmpeg_cmd_fallback=task_dict["ffmpeg_cmd_fallback"],
            filter=FileFilter(f_config),
        )
