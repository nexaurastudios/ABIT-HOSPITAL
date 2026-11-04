import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'hospital-opt-default-secret-key-2026')
    
    # Database
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_user = os.getenv('DB_USER', 'root')
        db_pass = os.getenv('DB_PASSWORD', '')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3306')
        db_name = os.getenv('DB_NAME', 'hospital_analytics_db')
        db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # Session & Security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'sample_data')
    BACKUP_FOLDER = os.path.join(basedir, 'backups')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max

    # Operational Thresholds
    BED_OCCUPANCY_ALERT_THRESHOLD = int(os.getenv('BED_OCCUPANCY_ALERT_THRESHOLD', 85))
    WAITING_TIME_ALERT_THRESHOLD = int(os.getenv('WAITING_TIME_ALERT_THRESHOLD', 45))

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    # Use in-memory SQLite for super-fast tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
