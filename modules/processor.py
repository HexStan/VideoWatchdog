import os
import shutil
import subprocess
import sys
import time

import humanfriendly

from modules.utils import get_media_duration, clean_empty_dirs


def process_file(filepath, task, state_manager, logger):
    """
    处理单个文件：执行 FFmpeg，移动文件，记录日志和状态
    """
    source_dir = task["source_dir"]

    # 计算相对路径以保持目录结构
    rel_path = os.path.relpath(filepath, source_dir)

    # 在处理前检查文件大小是否稳定
    stable_duration = task.get("stable_duration", 0)
    if stable_duration > 0:
        try:
            old_size = os.path.getsize(filepath)
        except OSError:
            logger.warning(f"文件 {rel_path} 已不存在，跳过处理。")
            return

        logger.info(f"正在检查 {rel_path} 在 {stable_duration} 秒内的一致性……")
        time.sleep(stable_duration)

        try:
            new_size = os.path.getsize(filepath)
            if new_size != old_size:
                logger.info(f"文件 {rel_path} 正在变化，跳过本次处理。")
                return
        except OSError:
            logger.warning(f"文件 {rel_path} 已不存在，跳过处理。")
            return
    else:
        if not os.path.exists(filepath):
            logger.warning(f"文件 {rel_path} 已不存在，跳过处理。")
            return

    dest_dir = task["dest_dir"]
    remove_source = task.get("remove_source", False)
    source_expired_minutes = task.get("source_expired_minutes", 0)
    backup_dir = task.get("backup_dir", "")

    rel_dir = os.path.dirname(rel_path)
    filename = os.path.basename(filepath)
    name, _ = os.path.splitext(filename)

    # 构造输出文件名：原文件名-后缀.格式
    dst_filename = f"{name}-{task['output_suffix']}.{task['output_format']}"
    dst_dir = os.path.join(dest_dir, rel_dir)
    dst_filepath = os.path.join(dst_dir, dst_filename)

    # 构造完成后的源文件移动路径
    if not remove_source:
        bak_dir = os.path.join(backup_dir, rel_dir)
        bak_filepath = os.path.join(bak_dir, filename)

    # 确保输出目录存在
    os.makedirs(dst_dir, exist_ok=True)

    # 获取音视频时长并格式化
    duration = humanfriendly.format_timespan(get_media_duration(filepath))

    # 检查是否需要使用 fallback 命令
    fallback_count = task.get("fallback_count", 0)
    ffmpeg_cmd_fallback = task.get("ffmpeg_cmd_fallback", "")

    use_fallback = False
    if fallback_count > 0 and ffmpeg_cmd_fallback:
        if state_manager.get_ffmpeg_failures(filepath) >= fallback_count:
            use_fallback = True

    if use_fallback:
        raw_cmd = ffmpeg_cmd_fallback.format(input=filepath, output=dst_filepath)
        logger.info(f"使用 fallback 命令转码 {rel_path}，媒体时长 {duration}。")
    else:
        raw_cmd = task["ffmpeg_cmd"].format(input=filepath, output=dst_filepath)
        logger.info(f"开始转码 {rel_path}，媒体时长 {duration}。")

    # 将多行命令合并为单行，替换换行符为空格，以支持在配置文件中换行提高可读性
    cmd = raw_cmd.replace("\n", " ").replace("\r", " ")

    start_time = time.time()
    try:
        # 执行命令，使用 Popen 实时读取输出
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        last_status_line = ""
        error_output = []
        final_status = ""
        last_print_time = 0
        is_tty = sys.stdout.isatty()

        # 实时读取 stderr
        while True:
            char = process.stderr.read(1)
            if not char and process.poll() is not None:
                break

            if char:
                try:
                    c = char.decode("utf-8", errors="ignore")
                except:
                    continue

                if c == "\r" or c == "\n":
                    line = last_status_line.strip()
                    if line:
                        error_output.append(line)
                        # 只打印包含进度信息的行
                        if "time=" in line or "speed=" in line:
                            current_time = time.time()
                            if is_tty:
                                # TTY 环境下使用 \r 覆盖当前行
                                print(f"\r{line.ljust(100)}", end="", flush=True)
                            else:
                                # 非 TTY 环境（如 Docker 默认日志），每 5 秒打印一次并换行，避免日志缓冲不显示和刷屏
                                if current_time - last_print_time >= 5.0:
                                    print(line, flush=True)
                                    last_print_time = current_time
                            final_status = line
                    last_status_line = ""
                else:
                    last_status_line += c

        # 确保最后一行也被处理
        line = last_status_line.strip()
        if line:
            error_output.append(line)
            if "time=" in line or "speed=" in line:
                if is_tty:
                    print(f"\r{line.ljust(100)}", end="", flush=True)
                else:
                    print(line, flush=True)
                final_status = line

        if final_status and is_tty:
            print()  # 换行，避免后续日志覆盖

        process.wait()
        elapsed_time = time.time() - start_time

        if process.returncode == 0:
            # dst_rel_path = os.path.relpath(dst_filepath, source_dir)
            logger.info(
                f"转码成功，耗时 {humanfriendly.format_timespan(elapsed_time)}。"
            )
            if final_status:
                logger.info(f"FFmpeg 运行报告: {final_status}")

            if remove_source:
                if source_expired_minutes == 0:
                    try:
                        os.remove(filepath)
                        logger.info(f"已删除源文件: {rel_path}")
                    except OSError as e:
                        logger.error(f"删除源文件失败: {rel_path}\n{e}")
                    state_manager.reset_failure(filepath)
                else:
                    state_manager.mark_success(filepath, time.time())
                    logger.info(
                        f"源文件 {rel_path} 将在 {source_expired_minutes} 分钟后删除。"
                    )
            else:
                # 确保目标目录存在
                os.makedirs(bak_dir, exist_ok=True)

                # 移动源文件到 backup_dir
                shutil.move(filepath, bak_filepath)

                # 重置失败记录
                state_manager.reset_failure(filepath)

            # 清理 source_dir 中的空文件夹
            clean_empty_dirs(source_dir)
        else:
            error_msg = "\n".join(error_output[-20:])  # 只取最后20行错误信息
            logger.error(f"转码失败，原因:\n{error_msg}")

            # 增加失败次数
            if use_fallback:
                state_manager.increment_failure(filepath)
            else:
                if fallback_count > 0 and ffmpeg_cmd_fallback:
                    state_manager.increment_ffmpeg_failure(filepath)
                else:
                    state_manager.increment_failure(filepath)

            # 如果生成了不完整的输出文件，将其删除
            if os.path.exists(dst_filepath):
                os.remove(dst_filepath)

    except Exception as e:
        logger.error(f"其他失败，原因:\n{e}")
        state_manager.increment_failure(filepath)
