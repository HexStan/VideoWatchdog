import os
import time
from dataclasses import dataclass, field

from modules.utils import get_media_info


@dataclass
class ScanEntry:
    filepath: str
    action: str
    size: int
    media_info: dict | None = None


@dataclass
class ScanReport:
    entries: list = field(default_factory=list)
    expired_files: list = field(default_factory=list)


class Scanner:
    def __init__(self):
        self._warned_dirs = set()

    def scan(self, task_config, state_manager, logger):
        source_dir = task_config.source_dir
        file_filter = task_config.filter
        failure_count = task_config.failure_count
        remove_source = task_config.remove_source
        source_expired_minutes = task_config.source_expired_minutes

        report = ScanReport()

        if not os.path.exists(source_dir):
            if source_dir not in self._warned_dirs:
                logger.warning(f"目录不存在: {source_dir}")
                self._warned_dirs.add(source_dir)
            return report

        current_time = time.time()
        task_name = task_config.name

        for root, _, files in os.walk(source_dir):
            for file in files:
                _, ext = os.path.splitext(file)

                classification = file_filter.classify_extension(ext)
                if classification == "reject":
                    continue

                filepath = os.path.join(root, file)

                success_time = state_manager.get_success_time(filepath)
                if success_time is not None:
                    if remove_source and source_expired_minutes > 0:
                        if current_time - success_time >= source_expired_minutes * 60:
                            report.expired_files.append(filepath)
                    continue

                if state_manager.get_failures(filepath) >= failure_count:
                    continue

                try:
                    stat = os.stat(filepath)
                    file_mtime = stat.st_mtime

                    if not file_filter.check_mtime(file_mtime, current_time):
                        continue

                    skipped_mtime = state_manager.get_filter_skipped_mtime(filepath)
                    if skipped_mtime is not None and skipped_mtime == file_mtime:
                        continue

                    media_info = None

                    if file_filter.requires_media_info():
                        media_info = get_media_info(filepath)
                        media_info["size"] = stat.st_size
                    else:
                        media_info = {"size": stat.st_size}

                    if not file_filter.match(media_info):
                        state_manager.mark_filter_skipped(filepath, file_mtime)
                        continue

                    entry = ScanEntry(
                        filepath=filepath,
                        action=classification,
                        size=stat.st_size,
                        media_info=media_info,
                    )
                    report.entries.append(entry)
                except OSError as e:
                    logger.error(f"读取文件失败: {filepath}\n{e}")

        if report.entries:
            for entry in report.entries:
                rel_path = os.path.relpath(entry.filepath, source_dir)
                logger.info(
                    f"【{task_name}】在 {source_dir} 中监测到新文件: {rel_path}"
                )

        return report
