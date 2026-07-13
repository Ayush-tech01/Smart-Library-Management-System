import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'library_management')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    @classmethod
    def validate_config(cls):
        """Validate that required environment variables are set"""
        required = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_DB']
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            print(f"Warning: Missing environment variables: {missing}")
        return len(missing) == 0

# Validate configuration on import
Config.validate_config()