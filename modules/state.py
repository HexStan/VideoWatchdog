import json
import os

class StateManager:
    def __init__(self, state_file="state.json"):
        self.state_file = state_file
        self.state = self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save state: {e}")

    def get_failures(self, filepath):
        """获取指定文件的失败次数"""
        return self.state.get(filepath, 0)

    def increment_failure(self, filepath):
        """增加指定文件的失败次数并持久化"""
        self.state[filepath] = self.state.get(filepath, 0) + 1
        self._save()

    def reset_failure(self, filepath):
        """重置（删除）指定文件的失败记录"""
        if filepath in self.state:
            del self.state[filepath]
            self._save()
