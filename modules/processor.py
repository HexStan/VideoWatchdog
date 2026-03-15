import os
import time
import subprocess
import shutil
from modules.utils import get_video_duration, clean_empty_dirs

def process_file(filepath, task, state_manager, logger):
    """
    处理单个文件：执行 FFmpeg，移动文件，记录日志和状态
    """
    monitor_dir = task['monitor_dir']
    output_dir = task['output_dir']
    processed_dir = task['processed_dir']
    
    # 计算相对路径以保持目录结构
    rel_path = os.path.relpath(filepath, monitor_dir)
    rel_dir = os.path.dirname(rel_path)
    filename = os.path.basename(filepath)
    name, _ = os.path.splitext(filename)
    
    # 构造输出文件名：原文件名-后缀.格式
    out_filename = f"{name}-{task['suffix']}.{task['format']}"
    out_dir = os.path.join(output_dir, rel_dir)
    out_filepath = os.path.join(out_dir, out_filename)
    
    # 构造完成后的源文件移动路径
    done_dir = os.path.join(processed_dir, rel_dir)
    done_filepath = os.path.join(done_dir, filename)
    
    # 确保输出和完成目录存在
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(done_dir, exist_ok=True)
    
    # 获取视频时长
    duration = get_video_duration(filepath)
    
    # 构造 FFmpeg 命令
    raw_cmd = task['ffmpeg_cmd'].format(input=filepath, output=out_filepath)
    # 将多行命令合并为单行，替换换行符为空格，以支持在配置文件中换行提高可读性
    cmd = raw_cmd.replace('\n', ' ').replace('\r', ' ')
    logger.info(f"开始转码: {filepath}")
    
    start_time = time.time()
    try:
        # 执行命令
        process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elapsed_time = time.time() - start_time
        
        if process.returncode == 0:
            # 计算转码速度
            speed = duration / elapsed_time if elapsed_time > 0 else 0
            logger.info(f"转码成功: {filepath} -> {out_filepath}")
            logger.info(f"视频时长: {duration:.2f}s，转码耗时: {elapsed_time:.2f}s，转码速度: {speed:.2f}X。")
            
            # 移动源文件到目录 C
            shutil.move(filepath, done_filepath)
            
            # 重置失败记录
            state_manager.reset_failure(filepath)
            
            # 清理目录 A 中的空文件夹
            clean_empty_dirs(monitor_dir)
        else:
            error_msg = process.stderr.decode('utf-8', errors='ignore')
            logger.error(f"转码失败: {filepath}\n错误内容: {error_msg}")
            
            # 增加失败次数
            state_manager.increment_failure(filepath)
            
            # 如果生成了不完整的输出文件，将其删除
            if os.path.exists(out_filepath):
                os.remove(out_filepath)
                
    except Exception as e:
        logger.error(f"未知失败: {filepath}: {e}")
        state_manager.increment_failure(filepath)
