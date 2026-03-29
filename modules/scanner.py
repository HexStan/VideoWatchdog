import os
import time


def scan_directory(task, state_manager, logger):
    """
    扫描目录，根据修改时间和大小变化筛选文件
    """
    source_dir = task["source_dir"]
    file_mtime = task.get("file_mtime", 0)
    failure_count = task.get("failure_count", 3)
    input_formats = task.get("input_formats", [".mp4"])
    remove_source = task.get("remove_source", False)
    source_expired_minutes = task.get("source_expired_minutes", 0)

    valid_files = []
    if not os.path.exists(source_dir):
        # 只有在第一次运行时才输出警告，避免重复日志
        if not hasattr(scan_directory, "_warned_dirs"):
            scan_directory._warned_dirs = set()
        if source_dir not in scan_directory._warned_dirs:
            logger.warning(f"目录不存在: {source_dir}")
            scan_directory._warned_dirs.add(source_dir)
        return valid_files

    current_time = time.time()
    candidates = []

    # 第一遍扫描：筛选出满足修改时间和重试次数条件的文件
    for root, _, files in os.walk(source_dir):
        for file in files:
            # 检查文件扩展名
            _, ext = os.path.splitext(file)
            # 统一转换为小写进行比较（此时 ext 和 input_formats 都带有前导点）
            if ext.lower() not in [e.lower() for e in input_formats]:
                continue

            filepath = os.path.join(root, file)

            # 检查是否已成功处理过
            success_time = state_manager.get_success_time(filepath)
            if success_time is not None:
                if remove_source and source_expired_minutes > 0:
                    if current_time - success_time >= source_expired_minutes * 60:
                        try:
                            os.remove(filepath)
                            rel_path = os.path.relpath(filepath, source_dir)
                            logger.info(f"已删除过期源文件: {rel_path}")
                            state_manager.remove_record(filepath)
                        except OSError as e:
                            logger.error(f"删除过期源文件失败: {filepath}\n{e}")
                continue

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
            rel_path = os.path.relpath(filepath, source_dir)
            logger.info(f"【{task_name}】监测到新文件: {rel_path}")

    # 将所有候选文件视为有效
    valid_files = [c[0] for c in candidates]

    return valid_files
