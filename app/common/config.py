# coding: utf-8
import os

# Base directory of the application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directory
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Database path
DB_PATH = os.path.join(DATA_DIR, 'pos.db')

# Backup directory
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Backup settings
MAX_BACKUPS = 720
BACKUP_CHECK_INTERVAL_MS = 60000  # 60 seconds
BACKUP_HOUR = 2  # 2:00 AM

# App info
APP_NAME = '收银系统'
APP_VERSION = '1.0.0'
