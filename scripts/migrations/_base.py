import json
import os
import shutil


class Migration:
    name: str = ""
    from_version: int = 0
    to_version: int = 0

    def migrate_state(self, db_path, state_json_paths):
        raise NotImplementedError

    def migrate_config(self, config_path, config_dict):
        raise NotImplementedError

    def run(self, db_path, config_path, state_json_paths):
        self.migrate_state(db_path, state_json_paths)
        if config_path and os.path.exists(config_path):
            backup_file(config_path)
            try:
                config_dict = _read_config(config_path)
                migrated = self.migrate_config(config_path, config_dict)
                _write_config(config_path, migrated)
            except Exception:
                pass


def backup_file(filepath):
    bak = filepath + ".bak"
    shutil.copy2(filepath, bak)
    return bak


def _read_config(config_path):
    import toml

    with open(config_path, "r", encoding="utf-8") as f:
        return toml.load(f)


def _write_config(config_path, config_dict):
    import toml

    content = toml.dumps(config_dict)
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)


def read_state_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_state_json(path, data):
    backup_file(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
