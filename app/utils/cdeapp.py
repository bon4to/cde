import os

from flask import Flask
from datetime import timedelta
from dotenv import load_dotenv

class config:
    # carrega o .env
    load_dotenv()
    
    debug = False
    db_path = os.getenv('DB_PATH')

    def set_debug(debug) -> None:
        config.debug = debug
        
    def get_debug() -> bool:
        return config.debug
    
    def get_db_path() -> str:
        return config.db_path
    
    def set(__name__):
        # define app
        app = Flask(__name__)
        
        # parâmetros
        app.secret_key = os.getenv('SECRET_KEY')
        app.config['APP_UNIT'] = '' # sets a default value
        app.config['CDE_SESSION_LIFETIME'] = timedelta(minutes=90)
        app.config['APP_VERSION'] = ['1.11.0', 'Ago/2025', False]   # 'versão', 'release-date', 'debug-mode'
        
        return app, None