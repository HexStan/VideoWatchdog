import os

import toml


class Config:
    def __init__(self, config_path="config/config.toml"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"在 {self.config_path} 中找不到配置文件。")

        with open(self.config_path, "r", encoding="utf-8") as f:
            return toml.load(f)

    @property
    def global_config(self):
        return self.data.get("global", {})

    @property
    def tasks(self):
        return self.data.get("tasks", [])

    def validate(self):
        if "global" not in self.data:
            raise ValueError("配置文件中缺失必要的 [global] 块。")

        if not self.tasks:
            raise ValueError("配置文件中没有任何任务。")

        for i, task in enumerate(self.tasks):
            required_keys = ["monitor_dir", "output_dir", "processed_dir", "ffmpeg_cmd"]
            for key in required_keys:
                if key not in task:
                    raise ValueError(f"任务 {i} 中缺失了必要项: {key}")

            # Set defaults for optional keys
            task.setdefault("file_mtime", 0)
            task.setdefault("stable_duration", 0)
            task.setdefault("failure_count", 3)
            task.setdefault("fallback_count", 0)
            task.setdefault("ffmpeg_cmd_fallback", "")
            task.setdefault("name", f"Task {i}")
            task.setdefault("input_formats", ["mp4"])
            task.setdefault("output_format", "mp4")
            task.setdefault("suffix", "")

            # 确保 input_formats 具有前导点
            task["input_formats"] = [
                ext if ext.startswith(".") else f".{ext}"
                for ext in task["input_formats"]
            ]

        return True
