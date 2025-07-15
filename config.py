import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'mood_bot'),
        'password': os.getenv('DB_PASSWORD', '-Tm70qM52'),
        'db': os.getenv('DB_NAME', 'mood_bot'),
        'autocommit': True
    }
    NOTIFICATION_TIME = os.getenv('NOTIFICATION_TIME', '10:00')
config = Config()
