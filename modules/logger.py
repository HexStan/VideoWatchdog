import logging
import os
import glob
from datetime import datetime

def setup_logger(log_dir="logs", max_log_files=7):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志以日期命名
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"videowatchdog_{date_str}.log")

    logger = logging.getLogger("VideoWatchdog")
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if not logger.handlers:
        # 文件输出
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # 控制台输出
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 格式化
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    # 清理旧日志文件
    _cleanup_old_logs(log_dir, max_log_files)

    return logger

def _cleanup_old_logs(log_dir, max_log_files):
    try:
        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        # 按修改时间排序，最旧的在前面
        log_files.sort(key=os.path.getmtime)
        
        while len(log_files) > max_log_files:
            oldest_file = log_files.pop(0)
            try:
                os.remove(oldest_file)
            except OSError:
                pass
    except Exception:
        pass
