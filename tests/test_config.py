import os
from unittest.mock import patch

import pytest

from modules.config import Config


class TestConfigInit:
    def test_load_valid_config(self, sample_toml_path):
        config = Config(sample_toml_path)
        assert config.data is not None
        assert "global" in config.data
        assert "tasks" in config.data
        assert len(config.data["tasks"]) == 1

    def test_file_not_found_raises_error(self):
        with pytest.raises(FileNotFoundError):
            Config("nonexistent/config.toml")

    def test_missing_global_block_raises_error(self, temp_dir):
        path = os.path.join(temp_dir, "config.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[[tasks]]\nsource_dir = './src'\ndest_dir = './dst'\nbackup_dir = './bak'\nffmpeg_cmd = 'ffmpeg'\n")
        with pytest.raises(ValueError, match="缺失必要的 \\[global\\] 块"):
            Config(path)

    def test_missing_tasks_raises_error(self, temp_dir):
        path = os.path.join(temp_dir, "config.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[global]\nscan_interval = 0\n")
        with pytest.raises(ValueError, match="没有任何任务"):
            Config(path)

    def test_invalid_tasks_raises_error(self, temp_dir):
        path = os.path.join(temp_dir, "config.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[global]\nscan_interval = 0\n[[tasks]]\nname = 'Bad Task'\n")
        with pytest.raises(ValueError, match="缺失了必要项"):
            Config(path)


class TestConfigProperties:
    def test_global_config(self, sample_toml_path):
        config = Config(sample_toml_path)
        gc = config.global_config
        assert gc["scan_interval"] == 30
        assert gc["log_dir"] == "test_logs"
        assert gc["max_log_files"] == 5
        assert gc["log_level"] == "DEBUG"

    def test_global_config_defaults_when_empty(self, temp_dir):
        path = os.path.join(temp_dir, "config.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[global]\n[[tasks]]\nsource_dir = './src'\ndest_dir = './dst'\nbackup_dir = './bak'\nffmpeg_cmd = 'ffmpeg'\n")
        config = Config(path)
        assert config.global_config == {}

    def test_tasks_property(self, sample_toml_path):
        config = Config(sample_toml_path)
        tasks = config.tasks
        assert len(tasks) == 1
        assert tasks[0].name == "Test Task"

    def test_multiple_tasks(self, temp_dir):
        path = os.path.join(temp_dir, "config.toml")
        content = """[global]
scan_interval = 0

[[tasks]]
source_dir = "./src1"
dest_dir = "./dst1"
backup_dir = "./bak1"
ffmpeg_cmd = "ffmpeg1"

[[tasks]]
source_dir = "./src2"
dest_dir = "./dst2"
backup_dir = "./bak2"
ffmpeg_cmd = "ffmpeg2"
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        config = Config(path)
        assert len(config.tasks) == 2
        assert config.tasks[0].source_dir == "./src1"
        assert config.tasks[1].source_dir == "./src2"


class TestEnvOverrides:
    def test_global_env_overrides(self, minimal_toml_path):
        env_vars = {
            "VIDEOWATCHDOG_SCAN_INTERVAL": "60",
            "VIDEOWATCHDOG_LOG_DIR": "/custom/logs",
            "VIDEOWATCHDOG_MAX_LOG_FILES": "10",
            "VIDEOWATCHDOG_LOG_LEVEL": "WARNING",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config(minimal_toml_path)
            gc = config.global_config
            assert gc["scan_interval"] == 60
            assert gc["log_dir"] == "/custom/logs"
            assert gc["max_log_files"] == 10
            assert gc["log_level"] == "WARNING"

    def test_global_scan_interval_non_int_fallback(self, minimal_toml_path):
        with patch.dict(os.environ, {"VIDEOWATCHDOG_SCAN_INTERVAL": "invalid"}, clear=False):
            config = Config(minimal_toml_path)
            assert config.global_config["scan_interval"] == "invalid"

    def test_task_env_overrides(self, minimal_toml_path):
        env_vars = {
            "VIDEOWATCHDOG_SOURCE_DIR": "/custom/source",
            "VIDEOWATCHDOG_DEST_DIR": "/custom/dest",
            "VIDEOWATCHDOG_BACKUP_DIR": "/custom/backup",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config(minimal_toml_path)
            task = config.tasks[0]
            assert task.source_dir == "/custom/source"
            assert task.dest_dir == "/custom/dest"
            assert task.backup_dir == "/custom/backup"

    def test_env_override_only_applies_when_set(self, minimal_toml_path):
        config = Config(minimal_toml_path)
        task = config.tasks[0]
        assert task.source_dir == "./source"
        assert task.dest_dir == "./dest"

    def test_env_override_setdefault_creates_global_dict(self, temp_dir):
        path = os.path.join(temp_dir, "config.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[[tasks]]\nsource_dir = './src'\ndest_dir = './dst'\nbackup_dir = './bak'\nffmpeg_cmd = 'ffmpeg'\n")
        with patch.dict(os.environ, {"VIDEOWATCHDOG_SCAN_INTERVAL": "42"}, clear=False):
            config = Config(path)
            assert config.global_config["scan_interval"] == 42
