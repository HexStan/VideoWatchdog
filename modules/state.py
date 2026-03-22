import json
import os


class StateManager:
    def __init__(self, state_file="logs/state.json"):
        self.state_file = state_file

        # 确保状态文件所在的目录存在
        state_dir = os.path.dirname(self.state_file)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)

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
            print(f"保存状态失败，原因:\n{e}")

    def get_failures(self, filepath):
        """获取指定文件的失败次数"""
        val = self.state.get(filepath, {})
        if isinstance(val, int):
            return val
        return val.get("failures", 0)

    def get_ffmpeg_failures(self, filepath):
        """获取指定文件的 FFmpeg 失败次数"""
        val = self.state.get(filepath, {})
        if isinstance(val, int):
            return 0
        return val.get("ffmpeg_failures", 0)

    def increment_failure(self, filepath):
        """增加指定文件的失败次数并持久化"""
        val = self.state.get(filepath, {})
        if isinstance(val, int):
            val = {"failures": val, "ffmpeg_failures": 0}
        val["failures"] = val.get("failures", 0) + 1
        self.state[filepath] = val
        self._save()

    def increment_ffmpeg_failure(self, filepath):
        """增加指定文件的 FFmpeg 失败次数并持久化"""
        val = self.state.get(filepath, {})
        if isinstance(val, int):
            val = {"failures": val, "ffmpeg_failures": 0}
        val["ffmpeg_failures"] = val.get("ffmpeg_failures", 0) + 1
        self.state[filepath] = val
        self._save()

    def reset_failure(self, filepath):
        """重置（删除）指定文件的失败记录"""
        if filepath in self.state:
            del self.state[filepath]
            self._save()
