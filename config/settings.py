import os
from pathlib import Path
import logging
import os
from dotenv import load_dotenv
import sys
import logging
from pathlib import Path
import requests 


# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

def get_config(application_name, url):
    if not application_name or not url:
        logger.warning(f"Paramètres manquants: application_name={application_name}, url={url}")
        return None
        
    try:
        logger.info(f"Tentative de récupération de la configuration pour {application_name} depuis {url}")
        response = requests.get(f"{url}/{application_name}/profile", timeout=5)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Erreur lors de la récupération de la configuration: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception lors de la requête vers le serveur de configuration: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue dans get_config: {e}")
        return None

# Fonction pour mettre à jour les variables d'environnement
def update_env_file(env_vars):
    try:
        env_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / '.env'
        
        # Lire le fichier .env existant
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Créer un dictionnaire des variables existantes
        env_dict = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_dict[key.strip()] = value.strip()
        
        # Mettre à jour avec les nouvelles valeurs
        env_dict.update(env_vars)
        
        # Écrire le fichier .env mis à jour
        with open(env_path, 'w') as f:
            for key, value in env_dict.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"Fichier .env mis à jour avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du fichier .env: {e}")
        return False

# Fonction pour mettre à jour les variables d'environnement en mémoire
def update_env_vars(env_vars):
    for key, value in env_vars.items():
        os.environ[key] = str(value)
    logger.info("Variables d'environnement mises à jour en mémoire")


def load_config():
    try:
        # Vérifier les variables d'environnement requises
        app_name = os.getenv('APP_NAME')
        config_uri = os.getenv('SERVICE_CONFIG_URI')
        
        if not app_name or not config_uri:
            logger.warning(f"Variables d'environnement manquantes: APP_NAME={app_name}, SERVICE_CONFIG_URI={config_uri}")
            logger.info("Utilisation des configurations par défaut")
            return
            
        # Récupérer la configuration depuis le serveur de configuration
        CONF = get_config(app_name, config_uri)
        
        if not CONF:
            logger.warning("Impossible de récupérer la configuration, utilisation des configurations par défaut")
            return
            
        # Extraire les propriétés de la source
        if 'propertySources' not in CONF or not CONF.get("propertySources"):
            logger.warning("Format de configuration invalide, utilisation des configurations par défaut")
            return
            
        properties = CONF.get("propertySources")[0].get('source')
        #logger.info(f"Configuration récupérée: {properties}")

        
        # Convert flat properties to nested dictionary
        def nest_dict(flat_dict):
            nested_dict = {}
            for key, value in flat_dict.items():
                if value is None:
                    continue
                keys = key.split('.')
                current = nested_dict
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            return nested_dict
            
        # Get nested configuration
        config = nest_dict(properties)
        #logger.info(f"Configuration convertie: {config}")
        
        # Configuration de l'application
        app_config = config.get('app', {})
        
        # Configuration RabbitMQ
        rabbitmq_config = config.get('rabbitmq', {})
        RABBITMQ = {
            'host': rabbitmq_config.get('host', 'localhost'),
            'port': int(rabbitmq_config.get('port', 5672)),
            'username': rabbitmq_config.get('user', 'guest'),
            'password': rabbitmq_config.get('password', 'guest')
        }
        #logger.info(f"Configuration RabbitMQ: {RABBITMQ}")
        
        # Configuration MySQL
        db_config = config.get('database', {})
        MYSQL = {
            'host': db_config.get('host', 'localhost'),
            'port': int(db_config.get('port', 3306)),
            'database': db_config.get('name', 'service_scrapping_db'),
            'username': db_config.get('user', 'root'),
            'password': db_config.get('password', 'root')
        }
        #logger.info(f"Configuration MySQL: {MYSQL}")
        
        # Configuration Service Discovery
        service_discovery = config.get('service_discovery', {})
        eureka_config = service_discovery.get('eureka', {})
        config_uri = service_discovery.get('config', {}).get('uri', 'http://localhost:8080')
        
        # Mettre à jour les variables d'environnement
        env_updates = {
            'APP_PORT': str(app_config.get('port', 5000)),
            'APP_NAME': app_config.get('name', 'service-scrapping'),
            'SECRET_KEY': app_config.get('secret_key', ''),
            'MYSQL_HOST': MYSQL['host'],
            'MYSQL_PORT': str(MYSQL['port']),
            'MYSQL_DB': MYSQL['database'],
            'MYSQL_USER': MYSQL['username'],
            'MYSQL_PASSWORD': MYSQL['password'],
            'RABBITMQ_HOST': RABBITMQ['host'],
            'RABBITMQ_PORT': str(RABBITMQ['port']),
            'RABBITMQ_USER': RABBITMQ['username'],
            'RABBITMQ_PASSWORD': RABBITMQ['password'],
            'EUREKA_SERVER': eureka_config.get('server', 'http://localhost:8761/eureka/'),
            'SERVICE_CONFIG_URI': config_uri
        }
        
        # Mettre à jour les variables d'environnement en mémoire
        update_env_vars(env_updates)
        
        # Mettre à jour le fichier .env
        update_env_file(env_updates)
        
        logger.info(f"Chargement de la configuration réussi")
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration: {e}")
        logger.info("Utilisation des configurations par défaut")







