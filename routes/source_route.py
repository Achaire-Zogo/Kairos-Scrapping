from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from dotenv import load_dotenv
# Importer les dépendances depuis le fichier dependencies.py
from utils.dependencies import StandardResponse
from utils.database import get_db
import os
import requests
import favicon
import datetime
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from fastapi.responses import Response
from feedgenerator import Rss201rev2Feed
from typing import Optional, Dict, Any, List
from datetime import datetime

router = APIRouter(
    prefix="/api/service-sources",
    tags=["Sources"],
    responses={404: {"description": "Not found"}},
)

# Charger les variables d'environnement avant d'importer les autres modules
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())



# Get all discovery popular feed
@router.get("/discovery-popular")
def get_discovery_popular_feed(db: Session = Depends(get_db)):
    try:
        # Récupérer les flux populaires
        discovery_popular_result = db.execute(
            text(
                """
                SELECT 
                    d.id,
                    d.name,
                    d.description,
                    d.url,
                    d.category,
                    d.created_at,
                    d.updated_at
                FROM 
                    discovery_popular_feed d
                ORDER BY 
                    d.created_at DESC
                """
            )
        )
        discovery_popular_feeds = [dict(row._mapping) for row in discovery_popular_result.fetchall()]
        
        # Récupérer les sites à scanner
        popular_sites_result = db.execute(
            text(
                """
                SELECT 
                    p.id,
                    p.name,
                    p.url,
                    p.logo,
                    p.created_at,
                    p.updated_at
                FROM 
                    popular_site_to_scan p
                ORDER BY 
                    p.created_at DESC
                """
            )
        )
        popular_sites_to_scan = [dict(row._mapping) for row in popular_sites_result.fetchall()]
        
        # Retourner la liste des flux populaires et sites à scanner
        return JSONResponse(
            status_code=200,
            content={
                "message": "success",
                "data": {
                    "discovery_popular_feeds": discovery_popular_feeds,
                    "popular_sites_to_scan": popular_sites_to_scan
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Error getting discovery popular feed: {str(e)}"
            }
        )
    
