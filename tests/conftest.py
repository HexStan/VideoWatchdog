import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.fixture
def sample_toml_path(temp_dir):
    content = """[global]
scan_interval = 30
log_dir = "test_logs"
max_log_files = 5
log_level = "DEBUG"

[[tasks]]
name = "Test Task"
source_dir = "./source"
dest_dir = "./dest"
backup_dir = "./backup"
ffmpeg_cmd = "ffmpeg -i {input} {output}.mp4"
ffmpeg_cmd_fallback = "ffmpeg -i {input} {output}_fallback.mp4"
stable_duration = 5
failure_count = 5
fallback_count = 3

[tasks.filter]
input_formats = ["mp4", "mkv"]
direct_move_formats = ["txt"]
file_mtime = 300
size = { min = "1MB", max = "10GB" }
duration = { min = "5s", max = "3600s" }
video_bitrate = { min = "500Kbps" }
audio_bitrate = { max = "320Kbps" }
total_bitrate = { min = "1Mbps", max = "30Mbps" }
framerate = { min = 24, max = 60 }
short_side = { min = 720, max = 1080 }
exclude_video_codecs = ["hevc", "av1"]
exclude_audio_codecs = ["opus"]
"""
    path = os.path.join(temp_dir, "config.toml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


@pytest.fixture
def minimal_toml_path(temp_dir):
    content = """[global]
scan_interval = 0

[[tasks]]
source_dir = "./source"
dest_dir = "./dest"
backup_dir = "./backup"
ffmpeg_cmd = "ffmpeg -i {input} {output}.mp4"
"""
    path = os.path.join(temp_dir, "config.toml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


@pytest.fixture
def sample_state_file(temp_dir):
    path = os.path.join(temp_dir, "state.json")
    return path


@pytest.fixture
def sample_state_file_with_data(temp_dir):
    path = os.path.join(temp_dir, "state.json")
    data = {
        "/test/file1.mp4": {"failures": 2, "ffmpeg_failures": 1, "success_time": None},
        "/test/file2.mp4": {"failures": 0, "ffmpeg_failures": 0, "success_time": 1234567890.0},
        "/test/file3.mp4": 3,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def basic_media_info():
    return {
        "duration": 120.5,
        "size": 52428800,
        "total_bitrate": 5000000,
        "video_bitrate": 3000000,
        "audio_bitrate": 192000,
        "framerate": 30.0,
        "short_side": 1080,
        "video_codec": "h264",
        "audio_codec": "aac",
    }


@pytest.fixture
def basic_filter_config():
    return {
        "input_formats": [".mp4", ".mkv"],
        "direct_move_formats": [".txt"],
        "file_mtime": 300,
        "size": {"min": "1MB", "max": "10GB"},
        "duration": {"min": "5s", "max": "3600s"},
        "video_bitrate": {"min": "500Kbps"},
        "audio_bitrate": {"max": "320Kbps"},
        "total_bitrate": {"min": "1Mbps", "max": "30Mbps"},
        "framerate": {"min": 24, "max": 60},
        "short_side": {"min": 720, "max": 1080},
        "exclude_video_codecs": ["hevc", "av1"],
        "exclude_audio_codecs": ["opus"],
    }
