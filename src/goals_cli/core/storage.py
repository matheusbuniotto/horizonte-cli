import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import Goal, Config, CheckIn

APP_DIR = Path.home() / ".road-to-35"
GOALS_FILE = APP_DIR / "goals.json"
CONFIG_FILE = APP_DIR / "config.json"
CHECKINS_DIR = APP_DIR / "checkins"

BACKUPS_DIR = APP_DIR / "backups"

def ensure_app_dir():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CHECKINS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

def cleanup_old_backups(original_file_name: str, keep: int = 20):
    """Keep only the 'keep' most recent backups for a given file name."""
    if not BACKUPS_DIR.exists():
        return
        
    # Pattern: filename.YYYYMMDDHHMMSS.bak
    glob_pattern = f"{original_file_name}.*.bak"
    backups = sorted(BACKUPS_DIR.glob(glob_pattern), key=os.path.getmtime, reverse=True)
    
    for backup in backups[keep:]:
        try:
            backup.unlink()
        except OSError:
            pass

def atomic_write(file_path: Path, content: str, make_backup: bool = True):
    """
    Writes content to a file atomically.
    Optionally creates a backup of the existing file in the backups directory.
    """
    # Ensure correct directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if file_path.exists() and make_backup:
        ensure_app_dir() # Ensure backup dir exists
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.bak"
        backup_path = BACKUPS_DIR / backup_name
        shutil.copy2(file_path, backup_path)
        
        # Cleanup old backups
        cleanup_old_backups(file_path.name)

    # Write to a temporary file first (unchanged logic)
    fd, temp_path = tempfile.mkstemp(dir=file_path.parent, text=True)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        # Rename temporary file to target file (atomic on POSIX)
        os.replace(temp_path, file_path)
    except Exception as e:
        os.remove(temp_path)
        raise e

class GoalsRepository:
    def __init__(self, file_path: Path = GOALS_FILE):
        self.file_path = file_path

    def load(self) -> List[Goal]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return [Goal(**g) for g in data]
        except json.JSONDecodeError:
            return []

    def save(self, goals: List[Goal]):
        data = [g.model_dump(mode='json') for g in goals]
        content = json.dumps(data, indent=2, ensure_ascii=False)
        atomic_write(self.file_path, content)

    def add(self, goal: Goal):
        goals = self.load()
        goals.append(goal)
        self.save(goals)

    def update(self, goal: Goal):
        goals = self.load()
        for i, g in enumerate(goals):
            if g.id == goal.id:
                goals[i] = goal
                break
        self.save(goals)

class ConfigRepository:
    def __init__(self, file_path: Path = CONFIG_FILE):
        self.file_path = file_path

    def load(self) -> Config:
        if not self.file_path.exists():
            return Config()
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return Config(**data)
        except json.JSONDecodeError:
            return Config()

    def save(self, config: Config):
        data = config.model_dump(mode='json')
        content = json.dumps(data, indent=2, ensure_ascii=False)
        atomic_write(self.file_path, content)

class CheckinRepository:
    def __init__(self, dir_path: Path = CHECKINS_DIR):
        self.dir_path = dir_path

    def save(self, checkin: CheckIn, content: str):
        ensure_app_dir()
        base_name = f"{checkin.date.strftime('%Y-%m-%d')}-{checkin.type.value}"
        
        # 1. Save Markdown
        filename_md = f"{base_name}.md"
        file_path_md = self.dir_path / filename_md
        checkin.file_path = str(file_path_md)
        atomic_write(file_path_md, content)
        
        # 2. Save JSON Data (Snapshot)
        filename_json = f"{base_name}.json"
        file_path_json = self.dir_path / filename_json
        
        data = checkin.model_dump(mode='json')
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        atomic_write(file_path_json, json_content)
        
        return file_path_md

    def list_all(self) -> List[Path]:
        if not self.dir_path.exists():
            return []
        # Return all md files sorted by name (date)descending
        return sorted(self.dir_path.glob("*.md"), reverse=True)

    def load_all_snapshots(self) -> List[CheckIn]:
        """Loads all CheckIn objects from JSON files."""
        if not self.dir_path.exists():
            return []
        
        json_files = sorted(self.dir_path.glob("*.json"), key=os.path.getmtime)
        checkins = []
        for jf in json_files:
            try:
                with open(jf, 'r') as f:
                    data = json.load(f)
                    checkins.append(CheckIn(**data))
            except Exception:
                continue
        return checkins
