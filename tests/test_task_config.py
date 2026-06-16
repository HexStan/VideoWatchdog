import pytest

from modules.task_config import TaskConfig


class TestTaskConfigFromDict:
    def test_minimal_valid_config(self):
        task_dict = {
            "source_dir": "./source",
            "dest_dir": "./dest",
            "backup_dir": "./backup",
            "ffmpeg_cmd": "ffmpeg -i {input} {output}.mp4",
        }
        tc = TaskConfig.from_dict(task_dict, 0)
        assert tc.name == "Task 0"
        assert tc.source_dir == "./source"
        assert tc.dest_dir == "./dest"
        assert tc.backup_dir == "./backup"
        assert tc.ffmpeg_cmd == "ffmpeg -i {input} {output}.mp4"
        assert tc.remove_source is False
        assert tc.source_expired_minutes == 0
        assert tc.stable_duration == 0
        assert tc.failure_count == 3
        assert tc.fallback_count == 0
        assert tc.ffmpeg_cmd_fallback == ""

    def test_missing_source_dir_raises_error(self):
        with pytest.raises(ValueError, match="缺失了必要项: source_dir"):
            TaskConfig.from_dict(
                {
                    "dest_dir": "./dest",
                    "backup_dir": "./backup",
                    "ffmpeg_cmd": "ffmpeg",
                }
            )

    def test_missing_dest_dir_raises_error(self):
        with pytest.raises(ValueError, match="缺失了必要项: dest_dir"):
            TaskConfig.from_dict(
                {
                    "source_dir": "./source",
                    "backup_dir": "./backup",
                    "ffmpeg_cmd": "ffmpeg",
                }
            )

    def test_missing_ffmpeg_cmd_raises_error(self):
        with pytest.raises(ValueError, match="缺失了必要项: ffmpeg_cmd"):
            TaskConfig.from_dict(
                {
                    "source_dir": "./source",
                    "dest_dir": "./dest",
                    "backup_dir": "./backup",
                }
            )

    def test_remove_source_true_without_backup_dir(self):
        task_dict = {
            "source_dir": "./source",
            "dest_dir": "./dest",
            "ffmpeg_cmd": "ffmpeg",
            "remove_source": True,
        }
        tc = TaskConfig.from_dict(task_dict)
        assert tc.remove_source is True
        assert tc.backup_dir == ""

    def test_remove_source_false_without_backup_dir_is_valid(self):
        task_dict = {
            "source_dir": "./source",
            "dest_dir": "./dest",
            "ffmpeg_cmd": "ffmpeg",
        }
        tc = TaskConfig.from_dict(task_dict)
        assert tc.remove_source is False
        assert tc.backup_dir == ""

    def test_overlapping_formats_raises_error(self):
        task_dict = {
            "source_dir": "./source",
            "dest_dir": "./dest",
            "backup_dir": "./backup",
            "ffmpeg_cmd": "ffmpeg",
            "filter": {
                "input_formats": [".mp4", ".mkv"],
                "direct_move_formats": [".mp4"],
            },
        }
        with pytest.raises(ValueError, match="不能有重复的格式"):
            TaskConfig.from_dict(task_dict)

    def test_extension_dot_normalization(self):
        task_dict = {
            "source_dir": "./source",
            "dest_dir": "./dest",
            "backup_dir": "./backup",
            "ffmpeg_cmd": "ffmpeg",
            "filter": {
                "input_formats": ["mp4", ".mkv"],
                "direct_move_formats": ["txt"],
            },
        }
        tc = TaskConfig.from_dict(task_dict)
        assert tc.filter.input_formats == [".mp4", ".mkv"]
        assert tc.filter.direct_move_formats == [".txt"]

    def test_all_fields_specified(self):
        task_dict = {
            "name": "Custom Task",
            "source_dir": "/src",
            "dest_dir": "/dst",
            "backup_dir": "/bak",
            "remove_source": False,
            "source_expired_minutes": 60,
            "ffmpeg_cmd": "ffmpeg -i {input} {output}.mp4",
            "ffmpeg_cmd_fallback": "ffmpeg -i {input} {output}_fallback.mp4",
            "stable_duration": 10,
            "failure_count": 5,
            "fallback_count": 3,
            "filter": {
                "file_mtime": 600,
                "input_formats": [".mp4", ".avi"],
                "size": {"min": "100MB"},
            },
        }
        tc = TaskConfig.from_dict(task_dict)
        assert tc.name == "Custom Task"
        assert tc.source_expired_minutes == 60
        assert tc.stable_duration == 10
        assert tc.failure_count == 5
        assert tc.fallback_count == 3
        assert tc.ffmpeg_cmd_fallback == "ffmpeg -i {input} {output}_fallback.mp4"
        assert tc.filter.file_mtime == 600

    def test_default_name_with_index(self):
        task_dict = {
            "source_dir": "./source",
            "dest_dir": "./dest",
            "backup_dir": "./backup",
            "ffmpeg_cmd": "ffmpeg",
        }
        tc = TaskConfig.from_dict(task_dict, index=5)
        assert tc.name == "Task 5"

    def test_multi_line_ffmpeg_cmd_preserved(self):
        task_dict = {
            "source_dir": "./source",
            "dest_dir": "./dest",
            "backup_dir": "./backup",
            "ffmpeg_cmd": 'ffmpeg -y \\\n  -i "{input}" \\\n  "{output}.mp4"',
        }
        tc = TaskConfig.from_dict(task_dict)
        assert "{input}" in tc.ffmpeg_cmd
        assert "{output}" in tc.ffmpeg_cmd
