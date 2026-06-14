import json
import os
import time

import pytest

from modules.state import StateManager


class TestStateManagerInit:
    def test_default_path_creates_dir(self, temp_dir):
        state_file = os.path.join(temp_dir, "test_state.json")
        sm = StateManager(state_file)
        sm._save()
        assert os.path.exists(state_file)

    def test_loads_existing_file(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert "/test/file1.mp4" in sm.state
        assert sm.state["/test/file1.mp4"]["failures"] == 2

    def test_empty_file_creates_empty_state(self, temp_dir):
        state_file = os.path.join(temp_dir, "empty.json")
        with open(state_file, "w", encoding="utf-8") as f:
            f.write("")
        sm = StateManager(state_file)
        assert sm.state == {}

    def test_invalid_json_creates_empty_state(self, temp_dir):
        state_file = os.path.join(temp_dir, "invalid.json")
        with open(state_file, "w", encoding="utf-8") as f:
            f.write("{invalid json")
        sm = StateManager(state_file)
        assert sm.state == {}

    def test_creates_parent_dirs(self, temp_dir):
        deep_path = os.path.join(temp_dir, "deep", "nested", "state.json")
        sm = StateManager(deep_path)
        sm._save()
        assert os.path.exists(deep_path)


class TestStateManagerGetFailures:
    def test_new_file_returns_zero(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_failures("/new/file.mp4") == 0

    def test_existing_file_returns_count(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_failures("/test/file1.mp4") == 2

    def test_legacy_int_value(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_failures("/test/file3.mp4") == 3


class TestStateManagerGetFfmpegFailures:
    def test_new_file_returns_zero(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_ffmpeg_failures("/new/file.mp4") == 0

    def test_existing_file_returns_count(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_ffmpeg_failures("/test/file1.mp4") == 1

    def test_legacy_int_value_returns_zero(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_ffmpeg_failures("/test/file3.mp4") == 0


class TestStateManagerIncrementFailure:
    def test_first_failure_increments(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.increment_failure("/test/file.mp4")
        assert sm.get_failures("/test/file.mp4") == 1

    def test_subsequent_failures_increment(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.increment_failure("/test/file1.mp4")
        assert sm.get_failures("/test/file1.mp4") == 3

    def test_persists_to_disk(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.increment_failure("/test/file.mp4")
        sm2 = StateManager(sample_state_file)
        assert sm2.get_failures("/test/file.mp4") == 1

    def test_legacy_int_upgrade(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.increment_failure("/test/file3.mp4")
        assert sm.get_failures("/test/file3.mp4") == 4
        assert sm.get_ffmpeg_failures("/test/file3.mp4") == 0


class TestStateManagerIncrementFfmpegFailure:
    def test_first_ffmpeg_failure(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.increment_ffmpeg_failure("/test/file.mp4")
        assert sm.get_ffmpeg_failures("/test/file.mp4") == 1

    def test_subsequent_ffmpeg_failures(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.increment_ffmpeg_failure("/test/file1.mp4")
        assert sm.get_ffmpeg_failures("/test/file1.mp4") == 2

    def test_legacy_int_upgrade(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.increment_ffmpeg_failure("/test/file3.mp4")
        assert sm.get_failures("/test/file3.mp4") == 3
        assert sm.get_ffmpeg_failures("/test/file3.mp4") == 1


class TestStateManagerResetFailure:
    def test_resets_existing_entry(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.reset_failure("/test/file1.mp4")
        assert "/test/file1.mp4" not in sm.state

    def test_reset_nonexistent_no_error(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.reset_failure("/nonexistent/file.mp4")

    def test_persists_reset(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.reset_failure("/test/file1.mp4")
        sm2 = StateManager(sample_state_file_with_data)
        assert "/test/file1.mp4" not in sm2.state


class TestStateManagerMarkSuccess:
    def test_sets_success_time(self, sample_state_file):
        sm = StateManager(sample_state_file)
        ts = time.time()
        sm.mark_success("/test/file.mp4", ts)
        assert sm.get_success_time("/test/file.mp4") == ts

    def test_resets_failures(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.mark_success("/test/file1.mp4", 999.0)
        assert sm.get_failures("/test/file1.mp4") == 0
        assert sm.get_ffmpeg_failures("/test/file1.mp4") == 0

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

    def test_legacy_int_value_returns_none(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        assert sm.get_success_time("/test/file3.mp4") is None


class TestStateManagerRemoveRecord:
    def test_removes_existing_record(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.remove_record("/test/file1.mp4")
        assert "/test/file1.mp4" not in sm.state

    def test_remove_nonexistent_no_error(self, sample_state_file):
        sm = StateManager(sample_state_file)
        sm.remove_record("/nonexistent/file.mp4")

    def test_persists_removal(self, sample_state_file_with_data):
        sm = StateManager(sample_state_file_with_data)
        sm.remove_record("/test/file1.mp4")
        sm2 = StateManager(sample_state_file_with_data)
        assert "/test/file1.mp4" not in sm2.state
