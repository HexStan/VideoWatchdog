import os
import subprocess


def get_media_duration(filepath):
    """
    使用 ffprobe 获取音视频时长（秒）
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        filepath,
    ]
    try:
        # 设定超时时间，防止卡死
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0.0
    except Exception:
        return 0.0


def clean_empty_dirs(directory):
    """
    递归删除指定目录下的所有空文件夹
    """
    if not os.path.exists(directory):
        return

    # topdown=False 保证先处理子目录，再处理父目录
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        # 不要删除根目录本身
        if os.path.abspath(dirpath) == os.path.abspath(directory):
            continue

        # 如果目录为空（没有文件也没有子目录）
        if not os.listdir(dirpath):
            try:
                os.rmdir(dirpath)
            except OSError:
                pass
