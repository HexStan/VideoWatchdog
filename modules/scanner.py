import os
import time


def scan_directory(task, state_manager, logger):
    """
    扫描目录，根据修改时间和大小变化筛选文件
    """
    monitor_dir = task["monitor_dir"]
    file_mtime = task.get("file_mtime", 0)
    failure_count = task.get("failure_count", 3)
    input_formats = task.get("input_formats", [".mp4"])

    valid_files = []
    if not os.path.exists(monitor_dir):
        # 只有在第一次运行时才输出警告，避免重复日志
        if not hasattr(scan_directory, "_warned_dirs"):
            scan_directory._warned_dirs = set()
        if monitor_dir not in scan_directory._warned_dirs:
            logger.warning(f"目录不存在: {monitor_dir}")
            scan_directory._warned_dirs.add(monitor_dir)
        return valid_files

    current_time = time.time()
    candidates = []

    # 第一遍扫描：筛选出满足修改时间和重试次数条件的文件
    for root, _, files in os.walk(monitor_dir):
        for file in files:
            # 检查文件扩展名
            _, ext = os.path.splitext(file)
            # 统一转换为小写进行比较（此时 ext 和 input_formats 都带有前导点）
            if ext.lower() not in [e.lower() for e in input_formats]:
                continue

            filepath = os.path.join(root, file)

            # 检查失败次数
            if state_manager.get_failures(filepath) >= failure_count:
                continue

            try:
                stat = os.stat(filepath)
                mtime = stat.st_mtime

                # 检查修改时间是否久于 file_mtime
                if file_mtime > 0 and (current_time - mtime) < file_mtime:
                    continue

                candidates.append((filepath, stat.st_size))
            except OSError as e:
                logger.error(f"读取文件失败: {filepath}\n{e}")

    task_name = task.get("name", "unnamed")
    if candidates:
        for filepath, _ in candidates:
            rel_path = os.path.relpath(filepath, monitor_dir)
            logger.info(f"【{task_name}】监测到新文件: {rel_path}")

    # 将所有候选文件视为有效
    valid_files = [c[0] for c in candidates]

    return valid_files
