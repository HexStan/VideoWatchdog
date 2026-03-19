# VideoWatchdog

English | [中文](README.md)

**VideoWatchdog** is a lightweight, Python-based automation tool designed to monitor specified directories for video files and automatically process them using FFmpeg once they are fully written. It is ideal for scenarios requiring automated video transcoding, compression, or format conversion.

## 💡 Inspiration & Background

This project is inspired by the `autovideoconverter` feature in the [jlesage/docker-handbrake](https://github.com/jlesage/docker-handbrake) project, borrowing its core logic. I developed this project because HandBrake has poor support for VAAPI and AMD GPU proprietary drivers on Linux.

## ✨ Features

- **Directory Monitoring**: Supports continuous directory monitoring or running as a one-off script.
- **Multi-Task Support**: Define multiple independent monitoring and processing tasks within a single configuration file.
- **File Stability Detection**: Ensures only fully written files are processed by checking file modification times and size changes, preventing incomplete files from being processed during download or copying.
- **Custom FFmpeg Commands**: Fully customizable FFmpeg processing commands to meet various audio and video processing needs.
- **State Management**: Automatically records processed files to prevent duplicate processing.
- **Auto Archiving**: Automatically moves source files to a specified archive directory after processing is complete.
- **Docker Support**: Includes a Dockerfile and docker-compose.yml for quick containerized deployment.

## 🛠️ Requirements

- **Python 3.x**
- **FFmpeg**: Must be installed and configured in the system's environment variables (PATH).

## 🚀 Installation & Usage

### Method 1: Run Directly

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/VideoWatchdog.git
   cd VideoWatchdog
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Configuration File**
   Copy the example configuration file and modify it as needed:
   ```bash
   cp config.toml.example config.toml
   ```

4. **Run the Program**
   ```bash
   python main.py
   ```

### Method 2: Use Docker

1. **Prepare Configuration File**
   ```bash
   cp config.toml.example config.toml
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## ⚙️ Configuration Guide

The project uses the TOML format for configuration, with the core configuration file being `config.toml`. Below are the main configuration options:

```toml
[global]
max_log_files = 7      # Maximum number of log files to keep
log_dir = "logs"       # Directory to save logs

[[tasks]]
name = "Task 1"                  # Task name
monitor_dir = "./input"          # Directory to monitor (where files to be processed are located)
output_dir = "./output"          # Directory for processed output files
processed_dir = "./processed"    # Directory to move source files after processing
input_formats = ["mp4", "mkv"]   # File formats to monitor
scan_interval = 60               # Scan interval in seconds (set to 0 to run as a one-off task)
file_mtime = 300                 # File modification time threshold in seconds (ensures file has stopped modifying)
stable_duration = 5              # File size stability detection time in seconds
failure_count = 3                # Maximum number of retries on failure
fallback_count = 3               # Number of FFmpeg errors before falling back to ffmpeg_cmd_fallback

# Custom FFmpeg command, {input} and {output} will be automatically replaced
ffmpeg_cmd = """
ffmpeg -y \
  -i "{input}" \
  -c:v libx264 \
  -preset fast \
  -crf 23 \
  "{output}"
"""

# Fallback FFmpeg command, executed when ffmpeg_cmd fails fallback_count times
ffmpeg_cmd_fallback = """
ffmpeg -y \
  -i "{input}" \
  -c:v libx264 \
  -preset medium \
  -crf 28 \
  "{output}"
"""

suffix = "encoded"               # Suffix appended to the output filename
output_format = "mp4"            # Output file format
```

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).
