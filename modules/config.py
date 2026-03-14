import os
import toml

class Config:
    def __init__(self, config_path="config.toml"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return toml.load(f)

    @property
    def global_config(self):
        return self.data.get('global', {})

    @property
    def tasks(self):
        return self.data.get('tasks', [])

    def validate(self):
        if not self.tasks:
            raise ValueError("No tasks configured in config.toml")
        
        for i, task in enumerate(self.tasks):
            required_keys = ['monitor_dir', 'output_dir', 'processed_dir', 'ffmpeg_cmd', 'suffix', 'format']
            for key in required_keys:
                if key not in task:
                    raise ValueError(f"Task {i} is missing required key: {key}")
            
            # Set defaults for optional keys
            task.setdefault('scan_interval', 60)
            task.setdefault('file_mtime', 0)
            task.setdefault('stable_duration', 0)
            task.setdefault('max_retries', 3)
            task.setdefault('name', f"task_{i}")

        return True
