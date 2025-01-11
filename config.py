import os
from datetime import timedelta
from typing import Type
from flask import Flask


basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuración base para la aplicación"""
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True 
    SESSION_COOKIE_SAMESITE = 'Lax'  
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1) 
    REMEMBER_COOKIE_DURATION = timedelta(hours=int(os.getenv('SESSION_DURATION', '1')))  


    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "database.db")}')
    
    @staticmethod
    def init_app(app: Flask) -> None:
        """Método para inicializar configuraciones específicas en el app"""
        pass

class DevelopmentConfig(Config):
    """Configuración para el entorno de desarrollo"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI', f'sqlite:///{os.path.join(basedir, "dev_database.db")}')
    
    @staticmethod
    def init_app(app: Flask) -> None:
        """Configura el logging para el entorno de desarrollo"""
        import logging
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s'))
        app.logger.addHandler(stream_handler)
        app.logger.info("Aplicación en modo desarrollo con logging en consola activado.")

class ProductionConfig(Config):
    """Configuración para el entorno de producción"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "prod_database.db")}')
    
    @staticmethod
    def init_app(app: Flask) -> None:
        """Configura el logging para el entorno de producción"""
        import logging
        from logging.handlers import RotatingFileHandler
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/prod_log.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] - %(message)s [in %(pathname)s:%(lineno)d]'
        ))

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.ERROR)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s'))

        app.logger.addHandler(file_handler)
        app.logger.addHandler(stream_handler)
        app.logger.info("Logging de producción activado en archivo y consola.")



config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
