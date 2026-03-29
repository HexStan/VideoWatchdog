import sys
import time

from modules.config import Config
from modules.logger import setup_logger
from modules.processor import process_file
from modules.scanner import scan_directory
from modules.state import StateManager

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
        print(
            "Warning: fcntl module not found. File locking is only supported on Linux/Unix."
        )
        return None

    try:
        lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except IOError:
        print("另一个实例正在运行，已退出。")
        sys.exit(1)


def run_task(task, state_manager, logger, scan_interval):
    """
    执行单个任务的扫描和处理流程
    """
    # 扫描目录获取符合条件的文件
    files = scan_directory(task, state_manager, logger)

    task_name = task.get("name", "unnamed")
    source_dir = task.get("source_dir", "unknown")

    if not files:
        if not task.get("is_monitoring", False):
            logger.info(
                f"【{task_name}】正在以 {scan_interval} 秒的间隔持续监听 {source_dir}"
            )
            task["is_monitoring"] = True
        return False

    task["is_monitoring"] = False

    # 逐个处理文件
    for filepath in files:
        process_file(filepath, task, state_manager, logger)

    return True


def main():
    # 尝试获取文件锁
    lock_fd = acquire_lock()

    try:
        # 加载配置，示例配置文件为 config/config.toml.example
        config = Config("config/config.toml")
        config.validate()
    except Exception as e:
        print(f"加载配置失败，原因:\n{e}")
        sys.exit(1)

    global_cfg = config.global_config

    # 初始化日志
    logger = setup_logger(
        log_dir=global_cfg.get("log_dir", "logs"),
        max_log_files=global_cfg.get("max_log_files", 7),
    )

    # 初始化状态管理器
    state_manager = StateManager("logs/state.json")
    tasks = config.tasks

    logger.info("VideoWatchdog 已启动。")

    scan_interval = global_cfg.get("scan_interval", 0)

    if scan_interval == 0:
        logger.info("全局扫描间隔为 0，作为一次性任务执行。")
        for task in tasks:
            run_task(task, state_manager, logger, scan_interval)
        logger.info("所有任务完成。")
    else:
        logger.info("VideoWatchdog 已进入监听模式。")
        try:
            while True:
                for task in tasks:
                    run_task(task, state_manager, logger, scan_interval)

                # 每次执行完所有任务后，固定等待 scan_interval 秒
                time.sleep(scan_interval)
        except KeyboardInterrupt:
            logger.info("VideoWatchdog 接收到退出信号，正在退出……")


if __name__ == "__main__":
    main()
