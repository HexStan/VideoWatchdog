import glob
import logging
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置自定义的命名函数
        self.namer = self._custom_namer

    def _custom_namer(self, default_name):
        # 将默认的 videowatchdog.log.20231024 转换为 videowatchdog-20231024.log
        if ".log." in default_name:
            name_part, date_part = default_name.rsplit(".log.", 1)
            return f"{name_part}-{date_part}.log"
        return default_name

    def getFilesToDelete(self):
        # 重写获取待删除文件的方法，以匹配自定义的文件名格式
        dir_name = os.path.dirname(self.baseFilename)
        base_name = os.path.basename(self.baseFilename)
        
        if base_name.endswith(".log"):
            prefix = base_name[:-4] + "-"
        else:
            prefix = base_name + "-"
            
        file_names = os.listdir(dir_name)
        result = []
        for file_name in file_names:
            if file_name.startswith(prefix) and file_name.endswith(".log"):
                # 提取日期部分并验证
                date_str = file_name[len(prefix):-4]
                if len(date_str) == 8 and date_str.isdigit():
                    result.append(os.path.join(dir_name, file_name))
                    
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result


def setup_logger(log_dir="logs", max_log_files=7):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("VideoWatchdog")
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if not logger.handlers:
        # 使用自定义的 TimedRotatingFileHandler 实现每天午夜自动轮转日志
        # 当前正在写入的日志文件名为 videowatchdog.log
        log_file = os.path.join(log_dir, "videowatchdog.log")
        
        fh = CustomTimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=max_log_files,
            encoding='utf-8'
        )
        # 轮转后的历史日志文件后缀，例如 videowatchdog-20231024.log
        fh.suffix = "%Y%m%d"
        fh.setLevel(logging.INFO)

        # 控制台输出
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 格式化
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    # 清理旧格式的日志文件（兼容以前的 videowatchdog-YYYYMMDD.log 格式）
    _cleanup_old_logs(log_dir, max_log_files)

    return logger


def _cleanup_old_logs(log_dir, max_log_files):
    try:
        log_files = glob.glob(os.path.join(log_dir, "videowatchdog-*.log"))

        # 提取文件名中的日期并排序
        def get_date_from_filename(filepath):
            filename = os.path.basename(filepath)
            # 假设文件名格式为 videowatchdog-YYYYMMDD.log
            try:
                date_str = filename.replace("videowatchdog-", "").replace(".log", "")
                return datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                # 如果解析失败，返回一个很早的时间
                return datetime.min

        now = datetime.now()
        for filepath in log_files:
            file_date = get_date_from_filename(filepath)
            # 如果旧格式日志的日期距离今天超过 max_log_files 天，则删除
            if (now - file_date).days > max_log_files:
                try:
                    os.remove(filepath)
                except OSError:
                    pass
    except Exception:
        pass
