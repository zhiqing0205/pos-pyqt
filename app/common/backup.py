# coding: utf-8
import os
import shutil
from datetime import datetime, date

from PyQt5.QtCore import QTimer, QObject

from .config import DB_PATH, BACKUP_DIR, MAX_BACKUPS, BACKUP_CHECK_INTERVAL_MS, BACKUP_HOUR


class BackupManager(QObject):
    """Handles automatic and manual database backups."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_backup_date = None
        self._backup_dir = BACKUP_DIR
        self._backup_hour = BACKUP_HOUR
        self._backup_minute = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_auto_backup)

    def start(self):
        """Start the auto-backup timer."""
        self._load_settings()
        self._timer.start(BACKUP_CHECK_INTERVAL_MS)

    def stop(self):
        self._timer.stop()

    def _load_settings(self):
        """Load backup settings from the database."""
        try:
            from ..models.settings import SettingsModel
            folder = SettingsModel.get('backup_folder', '')
            if folder:
                self._backup_dir = folder
                os.makedirs(self._backup_dir, exist_ok=True)
            hour = SettingsModel.get('backup_hour', '')
            if hour:
                self._backup_hour = int(hour)
            minute = SettingsModel.get('backup_minute', '')
            if minute:
                self._backup_minute = int(minute)
        except Exception:
            pass

    def update_settings(self, backup_dir=None, backup_hour=None, backup_minute=None):
        """Update backup settings at runtime."""
        if backup_dir:
            self._backup_dir = backup_dir
            os.makedirs(self._backup_dir, exist_ok=True)
        if backup_hour is not None:
            self._backup_hour = backup_hour
        if backup_minute is not None:
            self._backup_minute = backup_minute

    def should_backup_on_close(self):
        """Check if auto-backup on close is enabled."""
        try:
            from ..models.settings import SettingsModel
            return SettingsModel.get('backup_on_close', '1') == '1'
        except Exception:
            return True

    def _check_auto_backup(self):
        """Check if it's time for auto backup (daily at backup_hour:backup_minute)."""
        now = datetime.now()
        today = date.today()
        if (now.hour == self._backup_hour and now.minute == self._backup_minute
                and self._last_backup_date != today):
            self._last_backup_date = today
            self.create_backup(prefix='auto')

    def create_backup(self, prefix='manual'):
        """Create a backup of the database. Returns the backup file path."""
        if not os.path.exists(DB_PATH):
            return None

        os.makedirs(self._backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = '{}_{}.db'.format(prefix, timestamp)
        backup_path = os.path.join(self._backup_dir, backup_name)
        shutil.copy2(DB_PATH, backup_path)
        self._cleanup_old_backups()
        return backup_path

    def _cleanup_old_backups(self):
        """Keep only the most recent MAX_BACKUPS backup files."""
        backups = self.list_backups()
        if len(backups) > MAX_BACKUPS:
            for old in backups[MAX_BACKUPS:]:
                try:
                    os.remove(old['path'])
                except OSError:
                    pass

    def list_backups(self):
        """List all backup files sorted by modification time (newest first)."""
        if not os.path.exists(self._backup_dir):
            return []
        files = []
        for f in os.listdir(self._backup_dir):
            if f.endswith('.db'):
                path = os.path.join(self._backup_dir, f)
                mtime = os.path.getmtime(path)
                files.append({
                    'name': f,
                    'path': path,
                    'time': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'size': os.path.getsize(path),
                })
        files.sort(key=lambda x: x['time'], reverse=True)
        return files

    @staticmethod
    def restore_backup(backup_path):
        """Restore database from a backup file."""
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DB_PATH)
            return True
        return False

    @staticmethod
    def export_database(export_path):
        """Export the database to a specified path."""
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, export_path)
            return True
        return False

    @staticmethod
    def import_database(import_path):
        """Import a database from a specified path."""
        if os.path.exists(import_path):
            shutil.copy2(import_path, DB_PATH)
            return True
        return False
