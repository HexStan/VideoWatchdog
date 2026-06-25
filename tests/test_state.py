import os
import time

from modules.state import StateManager


class TestStateManagerInit:
    def test_default_path_creates_dir(self, temp_dir):
        state_file = os.path.join(temp_dir, "test_state.json")
        sm = StateManager(state_file)
        sm._save()
        assert os.path.exists(state_file)

    def test_loads_existing_file(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.state["failures"]["/test/file1.mp4"] == 2

    def test_empty_file_creates_empty_state(self, temp_dir):
        state_file = os.path.join(temp_dir, "empty.json")
        with open(state_file, "w", encoding="utf-8") as f:
            f.write("")
        sm = StateManager(state_file)
        assert sm.state == StateManager._empty_state()

    def test_invalid_json_creates_empty_state(self, temp_dir):
        state_file = os.path.join(temp_dir, "invalid.json")
        with open(state_file, "w", encoding="utf-8") as f:
            f.write("{invalid json")
        sm = StateManager(state_file)
        assert sm.state == StateManager._empty_state()

    def test_creates_parent_dirs(self, temp_dir):
        deep_path = os.path.join(temp_dir, "deep", "nested", "state.json")
        sm = StateManager(deep_path)
        sm._save()
        assert os.path.exists(deep_path)


class TestStateManagerGetFailureCount:
    def test_new_file_returns_zero(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_failure_count("/new/file.mp4") == 0

    def test_existing_file_returns_count(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_failure_count("/test/file1.mp4") == 2

    def test_missing_category_returns_zero(self, sample_state_file):
        sm = StateManager(sample_state_file)
        assert sm.get_failure_count("/test/file.mp4") == 0


class TestStateManagerGetFfmpegFailureCount:
    def test_new_file_returns_zero(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_ffmpeg_failure_count("/new/file.mp4") == 0

    def test_existing_file_returns_count(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_ffmpeg_failure_count("/test/file1.mp4") == 1


class TestStateManagerIncrementFailure:
    def test_first_failure_increments(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.increment_failure("/test/file.mp4")
        assert sm.get_failure_count("/test/file.mp4") == 1

    def test_subsequent_failures_increment(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.increment_failure("/test/file1.mp4")
        assert sm.get_failure_count("/test/file1.mp4") == 3

    def test_persists_to_disk(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.increment_failure("/test/file.mp4")
        sm2 = StateManager(sample_state_file)
        assert sm2.get_failure_count("/test/file.mp4") == 1


class TestStateManagerIncrementFfmpegFailure:
    def test_first_ffmpeg_failure(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.increment_ffmpeg_failure("/test/file.mp4")
        assert sm.get_ffmpeg_failure_count("/test/file.mp4") == 1

    def test_subsequent_ffmpeg_failures(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.increment_ffmpeg_failure("/test/file1.mp4")
        assert sm.get_ffmpeg_failure_count("/test/file1.mp4") == 2


class TestStateManagerMarkSuccess:
    def test_sets_success_time(self, sample_state_file):
        sm = StateManager(sample_state_file)
        ts = time.time()
        sm.mark_success("/test/file.mp4", ts)
        assert sm.get_success_time("/test/file.mp4") == ts

    def test_clears_failures(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.mark_success("/test/file1.mp4", 999.0)
        assert sm.get_failure_count("/test/file1.mp4") == 0
        assert sm.get_ffmpeg_failure_count("/test/file1.mp4") == 0

    def test_persists_mark(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.mark_success("/test/file.mp4", 1234567890.0)
        sm2 = StateManager(sample_state_file)
        assert sm2.get_success_time("/test/file.mp4") == 1234567890.0


class TestStateManagerGetSuccessTime:
    def test_new_file_returns_none(self, sample_state_file):
        sm = StateManager(sample_state_file)
        assert sm.get_success_time("/new/file.mp4") is None

    def test_after_mark_returns_time(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.mark_success("/test/file.mp4", 999.0)
        assert sm.get_success_time("/test/file.mp4") == 999.0

    def test_file_in_failures_only_returns_none(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_success_time("/test/file1.mp4") is None


class TestStateManagerDeleteRecord:
    def test_deletes_existing_record(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.delete_record("/test/file1.mp4")
        assert sm.get_failure_count("/test/file1.mp4") == 0
        assert sm.get_ffmpeg_failure_count("/test/file1.mp4") == 0

    def test_delete_nonexistent_no_error(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.delete_record("/nonexistent/file.mp4")

    def test_persists_deletion(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.delete_record("/test/file1.mp4")
        sm2 = StateManager(sample_state_file_with_data)
        assert sm2.get_failure_count("/test/file1.mp4") == 0


class TestStateManagerPruneEmpty:
    def test_prune_removes_zero_values(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.increment_failure("/test/file.mp4")
        assert sm.get_failure_count("/test/file.mp4") == 1

        sm.state["failures"]["/test/file.mp4"] = 0
        sm._prune_empty()
        assert "/test/file.mp4" not in sm.state["failures"]

    def test_prune_does_not_affect_success_time(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.mark_success("/test/file.mp4", 1234567890.0)
        sm._prune_empty()
        assert sm.get_success_time("/test/file.mp4") == 1234567890.0
