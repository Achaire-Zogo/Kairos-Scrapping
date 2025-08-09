from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
from typing import Optional
from datetime import datetime
from typing import List
import requests
import random
import time

router = APIRouter(
    prefix="/api/service-feeds",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)

# Charger les variables d'environnement avant d'importer les autres modules
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


# List of public SearxNG instances
SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://search.unlocked.link",
    "https://searx.tiekoetter.com",
    "https://searx.thegpm.org"
]

# List of common user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

def get_random_instance():
    return random.choice(SEARXNG_INSTANCES)

def get_random_user_agent():
    return random.choice(USER_AGENTS)

@router.get("/search/")
async def search(q: str, max_retries: int = 3):
    """
    Search using SearxNG with instance rotation and retries.
    """
    retries = 0
    last_error = None

    while retries < max_retries:
        try:
            # Get random instance and user agent
            instance = get_random_instance()
            headers = {
                "User-Agent": get_random_user_agent(),
                "Accept": "application/json"
            }

            # Add random delay
            time.sleep(random.uniform(1, 2))
            
            # Make request
            response = requests.get(
                f"{instance}/search",
                params={
                    "q": q,
                    "format": "json",
                    "pageno": 1,
                    "language": "en",
                    "time_range": None,
                    "category_general": 1
                },
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            # Parse results
            data = response.json()
            results = []
            
            for result in data.get("results", []):
                results.append({
                    "title": result.get("title"),
                    "link": result.get("url"),
                    "content": result.get("content"),
                    "engine": result.get("engine")
                })
                
            if results:
                return {
                    "results": results,
                    "search_time": data.get("search_time"),
                    "total_results": len(results)
                }
            
            retries += 1
            time.sleep(2 ** retries)  # Exponential backoff
            
        except Exception as e:
            last_error = str(e)
            retries += 1
            time.sleep(2 ** retries)
            continue

    raise HTTPException(
        status_code=503,
        detail=f"Search failed after {max_retries} attempts. Last error: {last_error}"
    )

