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
        print("另一个实例正在运行，已退出。")
        sys.exit(1)

def run_task(task, state_manager, logger):
    """
    执行单个任务的扫描和处理流程
    """
    logger.info(f"正在执行任务: {task.get('name', 'unnamed')}")
    
    # 扫描目录获取符合条件的文件
    files = scan_directory(task, state_manager, logger)
    
    if not files:
        logger.info(f"任务中没有待处理的文件: {task.get('name', 'unnamed')}")
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
        print(f"加载配置失败: {e}")
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
    
    logger.info("VideoWatchdog 已启动。")
    
    # 检查是否所有任务都是一次性运行 (scan_interval == 0)
    all_once = all(t.get('scan_interval', 0) == 0 for t in tasks)
    
    if all_once:
        logger.info("由于扫描间隔为 0，作为一次性任务执行。")
        for task in tasks:
            run_task(task, state_manager, logger)
        logger.info("所有任务完成，退出中……")
    else:
        # 记录每个任务上次运行的时间
        last_run = {i: 0 for i in range(len(tasks))}
        
        logger.info("VideoWatchdog 已进入监控状态。")
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
            logger.info("VideoWatchdog 接收到退出信号，正在退出……")

if __name__ == "__main__":
    main()
