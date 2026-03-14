import time
import sys
import os
from modules.config import Config
from modules.logger import setup_logger
from modules.state import StateManager
from modules.scanner import scan_directory
from modules.processor import process_file

# 尝试导入 fcntl，用于 Linux 文件锁
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

LOCK_FILE = "/tmp/video_watchdog.lock"

def acquire_lock():
    """
    使用 Linux 文件锁防止多个实例同时运行
    """
    if not HAS_FCNTL:
        print("Warning: fcntl module not found. File locking is only supported on Linux/Unix.")
        return None

    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except IOError:
        print("Another instance is already running. Exiting.")
        sys.exit(1)

def run_task(task, state_manager, logger):
    """
    执行单个任务的扫描和处理流程
    """
    logger.info(f"Running task: {task.get('name', 'unnamed')}")
    
    # 扫描目录获取符合条件的文件
    files = scan_directory(task, state_manager, logger)
    
    if not files:
        logger.info(f"No files to process for task: {task.get('name', 'unnamed')}")
        return

    # 逐个处理文件
    for filepath in files:
        process_file(filepath, task, state_manager, logger)

def main():
    # 尝试获取文件锁
    lock_fd = acquire_lock()
    
    try:
        # 加载配置
        config = Config("config.toml")
        config.validate()
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)
        
    global_cfg = config.global_config
    
    # 初始化日志
    logger = setup_logger(
        log_dir=global_cfg.get('log_dir', 'logs'), 
        max_log_files=global_cfg.get('max_log_files', 7)
    )
    
    # 初始化状态管理器
    state_manager = StateManager(global_cfg.get('state_file', 'state.json'))
    tasks = config.tasks
    
    logger.info("VideoWatchdog started.")
    
    # 检查是否所有任务都是一次性运行 (scan_interval == 0)
    all_once = all(t.get('scan_interval', 0) == 0 for t in tasks)
    
    if all_once:
        logger.info("All tasks are configured to run once (scan_interval = 0).")
        for task in tasks:
            run_task(task, state_manager, logger)
        logger.info("All tasks completed. Exiting.")
    else:
        # 记录每个任务上次运行的时间
        last_run = {i: 0 for i in range(len(tasks))}
        
        logger.info("Entering main loop for periodic tasks.")
        try:
            while True:
                current_time = time.time()
                for i, task in enumerate(tasks):
                    interval = task.get('scan_interval', 0)
                    
                    if interval == 0:
                        # 一次性任务只在第一次循环时运行
                        if last_run[i] == 0:
                            run_task(task, state_manager, logger)
                            last_run[i] = current_time
                    elif current_time - last_run[i] >= interval:
                        # 周期性任务达到间隔时间后运行
                        run_task(task, state_manager, logger)
                        last_run[i] = time.time()
                        
                # 避免 CPU 占用过高
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("VideoWatchdog stopped by user.")

if __name__ == "__main__":
    main()
