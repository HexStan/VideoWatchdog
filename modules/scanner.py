import os
import time

def scan_directory(task, state_manager, logger):
    """
    扫描目录，根据修改时间和大小变化筛选文件
    """
    monitor_dir = task['monitor_dir']
    mod_time_y = task.get('mod_time_y', 0)
    size_check_z = task.get('size_check_z', 0)
    max_retries_w = task.get('max_retries_w', 3)

    valid_files = []
    if not os.path.exists(monitor_dir):
        logger.warning(f"Directory does not exist: {monitor_dir}")
        return valid_files

    current_time = time.time()
    candidates = []

    # 第一遍扫描：筛选出满足修改时间和重试次数条件的文件
    for root, _, files in os.walk(monitor_dir):
        for file in files:
            filepath = os.path.join(root, file)
            
            # 检查失败次数
            if state_manager.get_failures(filepath) >= max_retries_w:
                continue
                
            try:
                stat = os.stat(filepath)
                mtime = stat.st_mtime
                
                # 检查修改时间是否久于 Y 秒
                if mod_time_y > 0 and (current_time - mtime) < mod_time_y:
                    continue
                    
                candidates.append((filepath, stat.st_size))
            except OSError as e:
                logger.error(f"Error accessing file {filepath}: {e}")

    # 第二遍扫描：如果 Z > 0，等待 Z 秒后检查文件大小是否变化
    if size_check_z > 0 and candidates:
        logger.info(f"Waiting {size_check_z} seconds to check size stability for {len(candidates)} files in {monitor_dir}...")
        time.sleep(size_check_z)
        
        for filepath, old_size in candidates:
            try:
                new_size = os.path.getsize(filepath)
                if new_size == old_size:
                    valid_files.append(filepath)
            except OSError:
                pass
    else:
        # 如果 Z == 0，直接将所有候选文件视为有效
        valid_files = [c[0] for c in candidates]

    return valid_files
