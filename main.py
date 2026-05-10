import argparse
import os
import sys
import time

from modules.config import Config
from modules.logger import setup_logger
from modules.processor import process_file
from modules.scanner import Scanner
from modules.state import StateManager

try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

LOCK_FILE = "/tmp/video_watchdog.lock"


def acquire_lock():
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


def cleanup_expired_files(expired_files, state_manager, logger):
    for filepath in expired_files:
        try:
            os.remove(filepath)
            logger.info(f"已删除过期源文件: {filepath}")
            state_manager.remove_record(filepath)
        except OSError as e:
            logger.error(f"删除过期源文件失败: {filepath}\n{e}")


def run_task(
    task_config, scanner, state_manager, logger, scan_interval, monitoring_logged
):
    report = scanner.scan(task_config, state_manager, logger)

    if report.expired_files:
        cleanup_expired_files(report.expired_files, state_manager, logger)

    task_name = task_config.name
    source_dir = task_config.source_dir

    if not report.entries:
        if task_name not in monitoring_logged:
            logger.info(
                f"【{task_name}】正在以 {scan_interval} 秒的间隔持续监听 {source_dir}"
            )
            monitoring_logged.add(task_name)
        return False

    monitoring_logged.discard(task_name)

    for entry in report.entries:
        process_file(entry, task_config, state_manager, logger)

    return True


def parse_args():
    parser = argparse.ArgumentParser(
        description="VideoWatchdog - 视频文件监听与转码工具"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config/config.toml",
        help="配置文件路径 (默认: config/config.toml)",
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help="日志目录 (覆盖配置文件)",
    )
    parser.add_argument(
        "--state-file",
        default="logs/state.json",
        help="状态文件路径 (默认: logs/state.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    lock_fd = acquire_lock()

    try:
        config = Config(args.config)
    except Exception as e:
        print(f"加载配置失败，原因:\n{e}")
        sys.exit(1)

    global_cfg = config.global_config

    log_dir = args.log_dir or global_cfg.get("log_dir", "logs")
    logger = setup_logger(
        log_dir=log_dir,
        max_log_files=global_cfg.get("max_log_files", 7),
    )

    state_manager = StateManager(args.state_file)
    scanner = Scanner()
    tasks = config.tasks

    logger.info("VideoWatchdog 已启动。")

    scan_interval = global_cfg.get("scan_interval", 0)
    monitoring_logged = set()

    if scan_interval == 0:
        logger.info("全局扫描间隔为 0，作为一次性任务执行。")
        for task_config in tasks:
            run_task(
                task_config,
                scanner,
                state_manager,
                logger,
                scan_interval,
                monitoring_logged,
            )
        logger.info("所有任务完成。")
    else:
        logger.info("VideoWatchdog 已进入监听模式。")
        try:
            while True:
                for task_config in tasks:
                    run_task(
                        task_config,
                        scanner,
                        state_manager,
                        logger,
                        scan_interval,
                        monitoring_logged,
                    )
                time.sleep(scan_interval)
        except KeyboardInterrupt:
            logger.info("VideoWatchdog 接收到退出信号，正在退出……")


if __name__ == "__main__":
    main()
