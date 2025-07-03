from fastapi import FastAPI, HTTPException, Response

import requests
from feedgenerator import Rss201rev2Feed
from datetime import datetime
from urllib.parse import urljoin, urlparse
import favicon
from typing import Optional
import os
import sys
import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from config.eureka_client import register_with_eureka, shutdown_eureka
from routes.feed_route import router as feed_router
from routes.axe_route import router as axe_router
from routes.theme_route import router as theme_router
from config.settings import load_config
from utils.database import create_tables, init_database

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement avant d'importer les autres modules
load_dotenv()

# Importer et exécuter les configurations depuis settings.py si disponible
logger.info("Chargement des configurations...")
try:
    load_config()
    logger.info("Configurations chargées avec succès")
except ImportError:
    logger.warning("Module config.settings non trouvé, utilisation des variables d'environnement par défaut")
except Exception as e:
    logger.error(f"Erreur lors du chargement des configurations: {e}")


app = FastAPI(
    title="Service Axes API",
    description="API pour gérer les axes",
    version="1.0.0",
    docs_url="/swagger"
)

# Ajouter le middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    
# Eureka lifecycle events
@app.on_event("startup")
async def startup_event():
    # Initialiser la base de données
    if init_database():
        #creation de la base de donnee
        create_tables()
        await register_with_eureka()
    else:
        logger.error("Impossible de démarrer l'application en raison d'erreurs d'initialisation.")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_eureka()



# Endpoint de santé pour Eureka
@app.get('/api/service-axes/health', tags=['Système'])
def health_check():
    """Endpoint de vérification de santé pour Eureka"""
    return {"status": "UP"}

@app.get("/api/service-axes/info")
def info():
    return {
        "app": os.getenv('APP_NAME', 'service-axes'),
        "version": app.version
    }



app.include_router(feed_router)
app.include_router(axe_router)
app.include_router(theme_router)


if __name__ == '__main__':
    # Récupérer le port de l'application depuis les variables d'environnement
    
    app_port = int(os.getenv('APP_PORT', 5001))
    logger.info(f"Port de l'application configuré: {app_port}")
    import uvicorn
    logger.info(f"Démarrage de l'application FastAPI sur le port {app_port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=5002, reload=True)
