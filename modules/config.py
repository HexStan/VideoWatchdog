import os

import toml

from modules.task_config import TaskConfig


class Config:
    def __init__(self, config_path="config/config.toml"):
        self.config_path = config_path
        self.data = self._load_config()
        self._apply_env_overrides()
        self._validate()

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
        return [
            TaskConfig.from_dict(t, i) for i, t in enumerate(self.data.get("tasks", []))
        ]

    def _validate(self):
        if "global" not in self.data:
            raise ValueError("配置文件中缺失必要的 [global] 块。")

        if not self.data.get("tasks"):
            raise ValueError("配置文件中没有任何任务。")

        tasks = self.tasks
        if not tasks:
            raise ValueError("配置文件中没有任何有效任务。")

    def _apply_env_overrides(self):
        overrides = {
            "global": {
                "scan_interval": "VIDEOWATCHDOG_SCAN_INTERVAL",
                "log_dir": "VIDEOWATCHDOG_LOG_DIR",
                "max_log_files": "VIDEOWATCHDOG_MAX_LOG_FILES",
            },
            "task": {
                "source_dir": "VIDEOWATCHDOG_SOURCE_DIR",
                "dest_dir": "VIDEOWATCHDOG_DEST_DIR",
                "backup_dir": "VIDEOWATCHDOG_BACKUP_DIR",
            },
        }

        for key, env_var in overrides["global"].items():
            val = os.environ.get(env_var)
            if val is not None:
                try:
                    self.data.setdefault("global", {})[key] = int(val)
                except ValueError:
                    self.data.setdefault("global", {})[key] = val

        for task in self.data.get("tasks", []):
            for key, env_var in overrides["task"].items():
                val = os.environ.get(env_var)
                if val is not None:
                    task[key] = val
