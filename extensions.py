from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
import os

# Création du dossier logs
if not os.path.exists('logs'):
    os.makedirs('logs')

# Initialisation des extensions
db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

# Configuration du logger
logger = logging.getLogger('educinfo')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Correction de levellevel en levelname

handlers = [
    RotatingFileHandler('logs/educinfo.log', maxBytes=10240, backupCount=10),
    logging.StreamHandler()
]

for handler in handlers:
    handler.setFormatter(formatter)
    logger.addHandler(handler)
