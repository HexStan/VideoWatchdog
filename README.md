# VideoWatchdog

[English](README_EN.md) | 中文

**VideoWatchdog** 是一个基于 Python 的轻量级自动化工具，用于监听指定目录中的音视频文件，并在文件写入完成后自动调用 FFmpeg 进行处理。它非常适合需要自动化音视频转码、压缩或格式转换的场景。

## 💡 启发与背景

该项目受到 [jlesage/docker-handbrake](https://github.com/jlesage/docker-handbrake) 项目中的 `autovideoconverter` 功能的启发，借鉴了其核心逻辑。由于 HandBrake 对于 Linux 上 VAAPI 和 AMD GPU 私有驱动的支持不佳，所以我开发了此项目。

## ✨ 特性

- **目录监听**：支持持续监听目录或作为一次性脚本运行。
- **多任务支持**：可以在单个配置文件中定义多个独立的监听和处理任务。
- **文件稳定性检测**：通过检测文件修改时间和大小变化，确保只处理已完全写入的文件，避免处理正在下载或复制中的不完整文件。
- **自定义 FFmpeg 命令**：支持完全自定义的 FFmpeg 处理命令，灵活应对各种音视频处理需求。
- **状态管理**：自动记录已处理的文件，防止重复处理。
- **自动归档**：处理完成后，自动将源文件移动到指定的归档目录。
- **Docker 支持**：提供 Dockerfile 和 docker-compose.yml，支持快速容器化部署。

## 🛠️ 依赖要求

- **Python 3.x**
- **FFmpeg**：必须安装并配置在系统的环境变量（PATH）中。

## 🚀 安装与运行

### 方式一：直接运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/VideoWatchdog.git
   cd VideoWatchdog
   ```
2. **安装 Python 依赖**
   ```bash
   pip install -r requirements.txt
   ```
3. **准备配置文件**
   将示例配置文件复制为正式配置文件，并根据需要进行修改：
   ```bash
   cp config/config.toml.example config/config.toml
   ```
4. **运行程序**
   ```bash
   python main.py
   ```

### 方式二：使用 Docker

1. **准备配置文件**
   ```bash
   cp config/config.toml.example config/config.toml
   ```
2. **使用 Docker Compose 启动**
   ```bash
   docker-compose up -d
   ```

## ⚙️ 配置说明

项目使用 TOML 格式进行配置，核心配置文件为 `config/config.toml`。以下是主要配置项说明：

```toml
[global]
scan_interval = 0      # 扫描间隔（秒），设为 0 则作为一次性任务运行
max_log_files = 7      # 最多保留的日志文件数
log_dir = "logs"       # 日志保存目录

[[tasks]]
name = "Task 1"                  # 任务名称
source_dir = "./source"          # 监听目录（待处理文件所在目录）
dest_dir = "./dest"              # 处理后的文件输出目录
backup_dir = "./backup"          # 处理完成后，源文件的移动目录（当不配置 remove_source 时必填）
remove_source = false            # 如果为 true，则忽略 backup_dir，在处理完音视频后直接删除源文件
source_expired_minutes = 0       # 仅在 remove_source = true 时可用。如果非0，则将源文件留在 source_dir 超过指定分钟后再删除
input_formats = ["mp4", "mkv"]   # 监听的文件格式
direct_move_formats = ["txt", "log"] # 对应格式的文件不会留在 source_dir，而是直接移动到 dest_dir（不能与 input_formats 重复）
file_mtime = 300                 # 文件修改时间阈值（秒），确保文件已停止修改
stable_duration = 5              # 文件大小稳定检测时间（秒）
failure_count = 3                # 失败重试次数
fallback_count = 3               # FFmpeg 错误回落次数，达到该次数后将使用 ffmpeg_cmd_fallback

# 自定义 FFmpeg 命令，{input} 和 {output} 会被自动替换
ffmpeg_cmd = """
ffmpeg -y \
  -i "{input}" \
  -c:v libx264 \
  -preset fast \
  -crf 23 \
  "{output}"
"""

# 备用 FFmpeg 命令，当 ffmpeg_cmd 失败次数达到 fallback_count 时执行
ffmpeg_cmd_fallback = """
ffmpeg -y \
  -i "{input}" \
  -c:v libx264 \
  -preset medium \
  -crf 28 \
  "{output}"
"""

output_suffix = "-encoded"               # 输出文件名的追加后缀
output_format = "mp4"            # 输出文件格式
```

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。
