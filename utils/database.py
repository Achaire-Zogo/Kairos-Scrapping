#!/usr/bin/env python3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging
import pymysql

# Charger les variables d'environnement
load_dotenv()

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration de la base de données
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_DB = os.getenv('MYSQL_DATABASE', 'service_scrapping_feed_db')

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Créer le moteur SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Crée les tables dans la base de données"""
    try:
        # Importer les modèles après la définition de Base
        from models.user_model import UserEntity
        from models.axe_model import AxeEntity
        from models.theme_model import ThemeEntity
        from models.popular_site_to_scan_model import PopularSiteToScanEntity
        from models.discovery_popular_feed_model import DiscoveryPopularFeedEntity
        from models.feed_model import FeedEntity
        from models.article_model import ArticleEntity
        from models.base import Base
        
        # Créer toutes les tables définies dans les modèles
        Base.metadata.create_all(bind=engine, tables=[
            UserEntity.__table__,
            AxeEntity.__table__,
            ThemeEntity.__table__,
            PopularSiteToScanEntity.__table__,
            DiscoveryPopularFeedEntity.__table__,
            FeedEntity.__table__,
            ArticleEntity.__table__
        ])
        logger.info("Tables créées avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Fonction pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Fonction pour initialiser la base de données
def init_database():
    try:
        logger.info("Initialisation de la base de données...")
        # logger.info(f"Connexion à MySQL: {MYSQL_HOST}:{MYSQL_PORT} avec l'utilisateur {MYSQL_USER}")
        # Utiliser les variables définies en haut du fichier
        mysql_host = MYSQL_HOST
        mysql_port = int(MYSQL_PORT)
        mysql_user = MYSQL_USER
        mysql_password = MYSQL_PASSWORD
        mysql_database = os.getenv('MYSQL_DB', 'service_scrapping_feed_db')
        
        #logger.info(f"Connexion à MySQL: {mysql_host}:{mysql_port} avec l'utilisateur {mysql_user}")
        
        # Créer la base de données si elle n'existe pas
        conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password
        )
        
        cursor = conn.cursor()
        # cursor.execute(f"DROP DATABASE IF EXISTS {mysql_database}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_database}")
        conn.commit()
        
        # logger.info(f"Base de données '{mysql_database}' créée ou déjà existante.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False


# Fonction pour ajouter des données de test
def seed_database():
    try:
        logger.info("Ajout des données de test...")
        
        # Helper pour exécuter un fichier SQL contenant plusieurs requêtes séparées par ';'
        def execute_sql_file(sql_path: str):
            abs_path = os.path.abspath(sql_path)
            logger.info(f"Exécution du fichier SQL: {abs_path}")
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Fichier SQL introuvable: {abs_path}")
            with open(abs_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            # Séparer grossièrement par ';' (suffisant pour des fichiers seed simples)
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            if not statements:
                logger.warning(f"Aucune requête trouvée dans {abs_path}")
                return
            # Utiliser une transaction
            with engine.begin() as conn:
                for stmt in statements:
                    conn.exec_driver_sql(stmt)
            logger.info(f"Fichier SQL exécuté avec succès: {abs_path}")

        # Résoudre les chemins des fichiers SQL dans le dossier seed
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        seed_dir = os.path.join(base_dir, 'Kairos-Scrapping', 'seed') if 'Kairos-Scrapping' not in base_dir else os.path.join(base_dir, 'seed')
        discovery_feed_sql = os.path.join(seed_dir, 'discovery_popular_feed.sql')
        popular_site_sql = os.path.join(seed_dir, 'popular_site_to_scan.sql')

        # Exécuter les fichiers SQL (sites populaires d'abord, puis discovery feeds)
        execute_sql_file(popular_site_sql)
        execute_sql_file(discovery_feed_sql)

        logger.info("Données de test ajoutées avec succès.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des données de test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
