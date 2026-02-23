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
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_auto_backup)

    def start(self):
        """Start the auto-backup timer."""
        self._timer.start(BACKUP_CHECK_INTERVAL_MS)

    def stop(self):
        self._timer.stop()

    def _check_auto_backup(self):
        """Check if it's time for auto backup (daily at BACKUP_HOUR)."""
        now = datetime.now()
        today = date.today()
        if now.hour == BACKUP_HOUR and self._last_backup_date != today:
            self._last_backup_date = today
            self.create_backup(prefix='auto')

    def create_backup(self, prefix='manual'):
        """Create a backup of the database. Returns the backup file path."""
        if not os.path.exists(DB_PATH):
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = '{}_{}.db'.format(prefix, timestamp)
        backup_path = os.path.join(BACKUP_DIR, backup_name)
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
        if not os.path.exists(BACKUP_DIR):
            return []
        files = []
        for f in os.listdir(BACKUP_DIR):
            if f.endswith('.db'):
                path = os.path.join(BACKUP_DIR, f)
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
