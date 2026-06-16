import json
import os


class StateManager:
    def __init__(self, state_file="logs/state.json"):
        self.state_file = state_file

        state_dir = os.path.dirname(self.state_file)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)

        self.state = self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._empty_state()
        return self._empty_state()

    @staticmethod
    def _empty_state():
        return {"failures": {}, "ffmpeg_failures": {}, "success_time": {}}

    def _save(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"保存状态失败，原因:\n{e}")

    def _prune_empty(self):
        for key in ("failures", "ffmpeg_failures"):
            d = self.state.get(key, {})
            empty_keys = [k for k, v in d.items() if v == 0]
            for k in empty_keys:
                del d[k]

    def get_failure_count(self, filepath):
        return self.state.get("failures", {}).get(filepath, 0)

    def get_ffmpeg_failure_count(self, filepath):
        return self.state.get("ffmpeg_failures", {}).get(filepath, 0)

    def increment_failure(self, filepath):
        d = self.state.setdefault("failures", {})
        d[filepath] = d.get(filepath, 0) + 1
        self._prune_empty()
        self._save()

    def increment_ffmpeg_failure(self, filepath):
        d = self.state.setdefault("ffmpeg_failures", {})
        d[filepath] = d.get(filepath, 0) + 1
        self._prune_empty()
        self._save()

    def mark_success(self, filepath, timestamp):
        self.state.setdefault("success_time", {})[filepath] = timestamp
        self.state.get("failures", {}).pop(filepath, None)
        self.state.get("ffmpeg_failures", {}).pop(filepath, None)
        self._save()

    def get_success_time(self, filepath):
        return self.state.get("success_time", {}).get(filepath)

    def delete_record(self, filepath):
        for key in ("failures", "ffmpeg_failures", "success_time"):
            if key in self.state:
                self.state[key].pop(filepath, None)
        self._save()
