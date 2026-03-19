import os
import sys
import time
import subprocess
import shutil
import humanfriendly
from modules.utils import get_video_duration, clean_empty_dirs

def process_file(filepath, task, state_manager, logger):
    """
    处理单个文件：执行 FFmpeg，移动文件，记录日志和状态
    """
    monitor_dir = task['monitor_dir']
    
    # 计算相对路径以保持目录结构
    rel_path = os.path.relpath(filepath, monitor_dir)
    
    # 在处理前检查文件大小是否稳定
    stable_duration = task.get('stable_duration', 0)
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

    output_dir = task['output_dir']
    processed_dir = task['processed_dir']
    
    rel_dir = os.path.dirname(rel_path)
    filename = os.path.basename(filepath)
    name, _ = os.path.splitext(filename)
    
    # 构造输出文件名：原文件名-后缀.格式
    out_filename = f"{name}-{task['suffix']}.{task['output_format']}"
    out_dir = os.path.join(output_dir, rel_dir)
    out_filepath = os.path.join(out_dir, out_filename)
    
    # 构造完成后的源文件移动路径
    done_dir = os.path.join(processed_dir, rel_dir)
    done_filepath = os.path.join(done_dir, filename)
    
    # 确保输出目录存在
    os.makedirs(out_dir, exist_ok=True)
    
    # 获取视频时长并格式化
    duration = humanfriendly.format_timespan(get_video_duration(filepath))
    
    # 检查是否需要使用 fallback 命令
    fallback_count = task.get('fallback_count', 0)
    ffmpeg_cmd_fallback = task.get('ffmpeg_cmd_fallback', '')
    
    use_fallback = False
    if fallback_count > 0 and ffmpeg_cmd_fallback:
        if state_manager.get_ffmpeg_failures(filepath) >= fallback_count:
            use_fallback = True

    if use_fallback:
        raw_cmd = ffmpeg_cmd_fallback.format(input=filepath, output=out_filepath)
        logger.info(f"使用 fallback 命令转码 {rel_path}，视频时长 {duration}。")
    else:
        raw_cmd = task['ffmpeg_cmd'].format(input=filepath, output=out_filepath)
        logger.info(f"开始转码 {rel_path}，视频时长 {duration}。")
        
    # 将多行命令合并为单行，替换换行符为空格，以支持在配置文件中换行提高可读性
    cmd = raw_cmd.replace('\n', ' ').replace('\r', ' ')
    
    start_time = time.time()
    try:
        # 执行命令，使用 Popen 实时读取输出
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
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
                    c = char.decode('utf-8', errors='ignore')
                except:
                    continue
                
                if c == '\r' or c == '\n':
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
            print() # 换行，避免后续日志覆盖
        
        process.wait()
        elapsed_time = time.time() - start_time
        
        if process.returncode == 0:
            out_rel_path = os.path.relpath(out_filepath, monitor_dir)
            logger.info(f"转码成功，耗时 {humanfriendly.format_timespan(elapsed_time)}。")
            if final_status:
                logger.info(f"FFmpeg 运行报告: {final_status}")
            
            # 确保目标目录存在
            os.makedirs(done_dir, exist_ok=True)
            
            # 移动源文件到 processed_dir
            shutil.move(filepath, done_filepath)
            
            # 重置失败记录
            state_manager.reset_failure(filepath)
            
            # 清理 monitor_dir 中的空文件夹
            clean_empty_dirs(monitor_dir)
        else:
            error_msg = "\n".join(error_output[-20:]) # 只取最后20行错误信息
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
            if os.path.exists(out_filepath):
                os.remove(out_filepath)
                
    except Exception as e:
        logger.error(f"其他失败，原因:\n{e}")
        state_manager.increment_failure(filepath)
