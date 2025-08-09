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
from typing import Optional, Dict, Any, List
from datetime import datetime

router = APIRouter(
    prefix="/api/service-feeds",
    tags=["Feeds"],
    responses={404: {"description": "Not found"}},
)

# Charger les variables d'environnement avant d'importer les autres modules
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def get_site_info(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Get site title
        title = soup.title.string if soup.title else urlparse(url).netloc
        
        # Get site description
        description = ""
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")
        
        # Get favicon
        icon_url = None
        try:
            icons = favicon.get(url)
            if icons:
                icon_url = icons[0].url
        except:
            pass
            
        return {
            "title": title,
            "description": description,
            "icon_url": icon_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la récupération des informations du site: {str(e)}")

def get_main_image(element, url: str) -> Optional[str]:
    # Chercher d'abord dans les métadonnées OpenGraph
    og_image = element.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        return urljoin(url, og_image['content'])
    
    # Chercher une image avec des classes communes pour les images principales
    img = element.find('img', class_=lambda x: x and any(cls in x.lower() for cls in ['featured', 'main', 'hero', 'thumbnail', 'preview']))
    if img and img.get('src'):
        return urljoin(url, img['src'])
    
    # Chercher la première image de taille raisonnable
    for img in element.find_all('img'):
        src = img.get('src')
        if not src:
            continue
        # Ignorer les petites images (probablement des icônes)
        width = img.get('width')
        height = img.get('height')
        if width and height:
            try:
                if int(width) < 50 or int(height) < 50:
                    continue
            except ValueError:
                pass
        return urljoin(url, src)
    
    # Chercher une image d'arrière-plan dans le style
    style = element.get('style', '')
    if 'background-image' in style:
        import re
        match = re.search(r'url\([\'"]?([^\'"]+)[\'"]?\)', style)
        if match:
            return urljoin(url, match.group(1))
    
    return None

def extract_articles(url: str, soup: BeautifulSoup):
    articles = []
    seen_titles = set()  # Pour suivre les titres uniques
    seen_links = set()   # Pour suivre les liens uniques
    
    # Chercher les articles potentiels
    article_elements = soup.find_all(['article', 'div', 'section'])
    
    for element in article_elements:
        # Chercher un titre
        title_element = element.find(['h1', 'h2', 'h3'])
        if not title_element:
            continue
            
        title = title_element.get_text(strip=True)
        
        # Chercher un lien
        link = None
        link_element = title_element.find('a') or element.find('a')
        if link_element and link_element.get('href'):
            link = urljoin(url, link_element['href'])
            
        # Vérifier si l'article est un doublon
        if title.lower() in seen_titles or (link and link in seen_links):
            continue
            
        # Chercher une description
        description = ""
        desc_element = element.find(['p', 'div'])
        if desc_element:
            description = desc_element.get_text(strip=True)
            
        # Chercher une date
        pub_date = datetime.now()
        date_element = element.find(['time', 'span', 'div'], class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
        if date_element:
            try:
                # Si l'élément time a un attribut datetime, l'utiliser
                if date_element.name == 'time' and date_element.get('datetime'):
                    pub_date = datetime.fromisoformat(date_element['datetime'].replace('Z', '+00:00'))
            except:
                # Si la conversion échoue, garder la date actuelle
                pass
        
        # Chercher l'image principale
        image_url = get_main_image(element, url)
        
        if title and (link or description):
            # Ajouter aux ensembles de suivi
            seen_titles.add(title.lower())
            if link:
                seen_links.add(link)
                
            # Ajouter l'image à la description si elle existe
            if image_url:
                description = f'<img src="{image_url}" /><br/>{description}'
                
            articles.append({
                "title": title,
                "link": link,
                "description": description,
                "pub_date": pub_date
            })
    
    return articles

def generate_feed_data(url: str, site_info: Dict[str, Any], articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Génère une structure de données JSON à partir des informations du site et des articles.
    
    Args:
        url: URL du site source
        site_info: Dictionnaire contenant les informations du site
        articles: Liste des articles extraits
        
    Returns:
        Dict: Structure de données contenant les informations du flux
    """
    return {
        "site": {
            "title": site_info["title"],
            "url": url,
            "description": site_info["description"],
            "favicon": site_info["icon_url"]
        },
        "articles": [
            {
                "title": article["title"],
                "url": article["link"] or url,
                "description": article["description"],
                "publication_date": article["pub_date"].isoformat() if article["pub_date"] else None
            }
            for article in articles
        ]
    }

@router.get("/feed")
async def get_feed(url: str, db: Session = Depends(get_db)):
    try:
        # Vérifier l'URL
        if not url.startswith(('http://', 'https://')):
            return JSONResponse(
                status_code=400,
                content={
                    "message": "URL invalide",
                    "data": {}
                }
            )
            
        # Faire la requête HTTP
        response = requests.get(url)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Obtenir les informations du site
        site_info = get_site_info(url)
        
        # Extraire les articles
        articles = extract_articles(url, soup)
        
        if not articles:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "no article found",
                    "data": {}
                }
            )
        
        # Générer la structure de données
        feed_data = generate_feed_data(url, site_info, articles)
        
        # Retourner la réponse JSON
        return JSONResponse(
            status_code=200,
            content={
                "message": "Feed generated successfully",
                "data": feed_data
            }
        )
        
    except requests.exceptions.RequestException as e:
        return JSONResponse(
            status_code=400,
            content={
                "message":"error http request",
                "data": f"Error HTTP request: {str(e)}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message":"error internal",
                "data": f"Error internal: {str(e)}"
            }
        )


#get feed about some subjet
@router.get("/feed-subject")
async def get_feed_subject(subject: str, db: Session = Depends(get_db)):
    try:
        # Vérifier le sujet
        if not subject:
            return JSONResponse(
                status_code=400, 
                content={
                    "message": "Subject is required",
                    "data": {}
                }
            )
            
        # Faire la requête HTTP
        response = requests.get(f"https://news.google.com/search?q={subject}&hl=fr&gl=FR&ceid=FR:fr")
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Obtenir les informations du site
        site_info = get_site_info(response.url)
        
        # Extraire les articles
        articles = extract_articles(response.url, soup)
        
        if not articles:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "no article found",
                    "data": {}
                }
            )
        
        # Générer la structure de données
        feed_data = {
            "site": {
                "title": site_info["title"],
                "url": response.url,
                "description": site_info["description"],
                "favicon": site_info["icon_url"]
            },
            "articles": [
                {
                    "title": article["title"],
                    "url": article["link"] or response.url,
                    "description": article["description"],
                    "publication_date": article["pub_date"].isoformat() if article["pub_date"] else None
                }
                for article in articles
            ]
        }
        
        # Retourner la réponse JSON
        return JSONResponse(
            status_code=200,
            content={
                "message": "feed generated successfully",
                "data": feed_data
            }
        )
        
    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=400, content={"message":f"Erreur lors de la requête HTTP: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message":f"Erreur interne: {str(e)}"})

#get feed about some subjet and url 
@router.get("/feed-subject-url")
async def get_feed_subject_url(subject: str, url: str, db: Session = Depends(get_db)):
    try:
        # Vérifier l'URL
        if not url.startswith(('http://', 'https://')):
            return JSONResponse(
                status_code=400, 
                content={
                    "message": "URL invalide",
                    "data": {}
                }
            )
            
        # Faire la requête HTTP
        response = requests.get(url)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Obtenir les informations du site
        site_info = get_site_info(url)
        
        # Extraire les articles
        articles = extract_articles(url, soup)

        # Filtrer les articles en fonction du sujet
        articles = [
            article for article in articles 
            if subject.lower() in article["title"].lower() or 
               subject.lower() in article["description"].lower()
        ]
        
        if not articles:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "no article found for this subject",
                    "data": {}
                }
            )
        
        # Créer la structure de données
        feed_data = {
            "site": {
                "title": site_info["title"],
                "url": url,
                "description": site_info["description"],
                "favicon": site_info["icon_url"]
            },
            "articles": [
                {
                    "title": article["title"],
                    "url": article["link"] or url,
                    "description": article["description"],
                    "publication_date": article["pub_date"].isoformat() if article["pub_date"] else None
                }
                for article in articles
            ]
        }
        
        # Retourner la réponse JSON
        return JSONResponse(
            status_code=200,
            content={
                "message": "feed generated successfully",
                "data": feed_data
            }
        )
        
    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=400, content={"message":f"Erreur lors de la requête HTTP: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message":f"Erreur interne: {str(e)}"})


# scraper yahoo news
def scrape_yahoo_news(subject: str, max_results: int = 10):
    """Scraper Yahoo Actualités pour un sujet donné"""
    articles = []
    try:
        # URL de recherche Yahoo Actualités
        search_url = f"https://fr.news.yahoo.com/search?p={subject.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sélecteurs spécifiques à Yahoo News
        article_elements = soup.find_all('div', class_=['Ov(h)', 'StreamItem'])[:max_results]
        
        for element in article_elements:
            try:
                # Titre
                title_elem = element.find('h3') or element.find('a')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # Lien
                link_elem = element.find('a', href=True)
                link = link_elem['href'] if link_elem else None
                if link and not link.startswith('http'):
                    link = f"https://fr.news.yahoo.com{link}"
                
                # Description
                desc_elem = element.find('p') or element.find('div', class_='summary')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Date
                time_elem = element.find('time') or element.find('span', class_='time')
                pub_date = datetime.now()
                if time_elem and time_elem.get('datetime'):
                    try:
                        pub_date = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
                    except:
                        pass
                
                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "pub_date": pub_date,
                        "source": "Yahoo Actualités"
                    })
                    
            except Exception as e:
                logger.warning(f"Erreur lors du parsing d'un article Yahoo: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Erreur lors du scraping Yahoo News: {e}")
    
    return articles


def scrape_bing_news(subject: str, max_results: int = 10):
    """Scraper Bing News pour un sujet donné"""
    articles = []
    try:
        # URL de recherche Bing News
        search_url = f"https://www.bing.com/news/search?q={subject.replace(' ', '+')}&form=HDRSC1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sélecteurs spécifiques à Bing News
        article_elements = soup.find_all('div', class_=['news-card', 'newsitem'])[:max_results]
        
        for element in article_elements:
            try:
                # Titre
                title_elem = element.find('a', class_='title') or element.find('h2') or element.find('a')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # Lien
                link = title_elem.get('href') if title_elem else None
                if link and link.startswith('/'):
                    link = f"https://www.bing.com{link}"
                
                # Description
                desc_elem = element.find('div', class_='snippet') or element.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Date
                time_elem = element.find('span', class_='time') or element.find('time')
                pub_date = datetime.now()
                if time_elem:
                    try:
                        time_text = time_elem.get_text(strip=True)
                        # Traitement basique des dates relatives (ex: "il y a 2 heures")
                        if "heure" in time_text:
                            hours = int(time_text.split()[0]) if time_text.split()[0].isdigit() else 1
                            pub_date = datetime.now() - datetime.timedelta(hours=hours)
                        elif "jour" in time_text:
                            days = int(time_text.split()[0]) if time_text.split()[0].isdigit() else 1
                            pub_date = datetime.now() - datetime.timedelta(days=days)
                    except:
                        pass
                
                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "pub_date": pub_date,
                        "source": "Bing News"
                    })
                    
            except Exception as e:
                logger.warning(f"Erreur lors du parsing d'un article Bing: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Erreur lors du scraping Bing News: {e}")
    
    return articles


def scrape_baidu_news(subject: str, max_results: int = 10):
    """Scraper Baidu News pour un sujet donné"""
    articles = []
    try:
        # URL de recherche Baidu News
        search_url = f"https://news.baidu.com/ns?word={subject.replace(' ', '+')}&tn=news&from=news&cl=2&pn=0&rn={max_results}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        response = requests.get(search_url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sélecteurs spécifiques à Baidu News
        article_elements = soup.find_all('div', class_=['result', 'news-item'])[:max_results]
        
        for element in article_elements:
            try:
                # Titre
                title_elem = element.find('h3') or element.find('a')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # Lien
                link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                link = link_elem.get('href') if link_elem else None
                
                # Description
                desc_elem = element.find('p') or element.find('div', class_='c-abstract')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Date
                time_elem = element.find('span', class_='c-color-gray2') or element.find('time')
                pub_date = datetime.now()
                if time_elem:
                    try:
                        time_text = time_elem.get_text(strip=True)
                        # Traitement basique des dates chinoises
                        if "小时前" in time_text:
                            hours = int(time_text.replace("小时前", "")) if time_text.replace("小时前", "").isdigit() else 1
                            pub_date = datetime.now() - datetime.timedelta(hours=hours)
                        elif "天前" in time_text:
                            days = int(time_text.replace("天前", "")) if time_text.replace("天前", "").isdigit() else 1
                            pub_date = datetime.now() - datetime.timedelta(days=days)
                    except:
                        pass
                
                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "pub_date": pub_date,
                        "source": "Baidu News"
                    })
                    
            except Exception as e:
                logger.warning(f"Erreur lors du parsing d'un article Baidu: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Erreur lors du scraping Baidu News: {e}")
    
    return articles


def get_multi_source_articles(subject: str, sources: list = None, max_per_source: int = 5):
    """Récupérer des articles de plusieurs sources pour un sujet donné"""
    if sources is None:
        sources = ['yahoo', 'bing', 'baidu']
    
    all_articles = []
    
    if 'yahoo' in sources:
        yahoo_articles = scrape_yahoo_news(subject, max_per_source)
        all_articles.extend(yahoo_articles)
        logger.info(f"Récupéré {len(yahoo_articles)} articles de Yahoo News")
    
    if 'bing' in sources:
        bing_articles = scrape_bing_news(subject, max_per_source)
        all_articles.extend(bing_articles)
        logger.info(f"Récupéré {len(bing_articles)} articles de Bing News")
    
    if 'baidu' in sources:
        baidu_articles = scrape_baidu_news(subject, max_per_source)
        all_articles.extend(baidu_articles)
        logger.info(f"Récupéré {len(baidu_articles)} articles de Baidu News")
    
    # Trier par date de publication (plus récent en premier)
    all_articles.sort(key=lambda x: x['pub_date'], reverse=True)
    
    return all_articles

# Nouveaux endpoints pour les sources multiples
@router.get("/multi-sources/{subject}")
async def get_multi_source_feed(subject: str, sources: str = "yahoo,bing,baidu", max_per_source: int = 5, db: Session = Depends(get_db)):
    """
    Récupérer des articles de plusieurs sources (Yahoo, Bing, Baidu) pour un sujet donné
    
    Args:
        subject: Le sujet à rechercher
        sources: Sources séparées par des virgules (yahoo,bing,baidu)
        max_per_source: Nombre maximum d'articles par source
    
    Returns:
        JSON: Structure de données contenant les articles des différentes sources
    """
    try:
        # Parser les sources
        source_list = [s.strip().lower() for s in sources.split(',')]
        valid_sources = ['yahoo', 'bing', 'baidu']
        source_list = [s for s in source_list if s in valid_sources]
        
        if not source_list:
            return JSONResponse(
                status_code=400, 
                content={
                    "message": "no valid source specified",
                    "data": {}
                }
            )
        
        # Récupérer les articles de toutes les sources
        articles = get_multi_source_articles(subject, source_list, max_per_source)
        
        if not articles:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "no article found",
                    "data": {}
                }
            )
        
        # Créer la structure de données
        feed_data = {
            "subject": subject,
            "sources": source_list,
            "total_articles": len(articles),
            "articles": [
                {
                    "title": article["title"],
                    "url": article["link"],
                    "description": article["description"],
                    "source": article["source"],
                    "publication_date": article["pub_date"].isoformat() if article["pub_date"] else None
                }
                for article in articles
            ]
        }
        
        # Retourner la réponse JSON
        return JSONResponse(
            status_code=200,
            content={
                "message": f"successfully retrieved {len(articles)} articles from {len(source_list)} sources",
                "data": feed_data
            }
        )
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"message":f"Erreur interne: {str(e)}"})


@router.get("/yahoo-news/{subject}")
async def get_yahoo_news_feed(subject: str, max_results: int = 10, db: Session = Depends(get_db)):
    """
    Récupérer les actualités Yahoo pour un sujet donné
    
    Args:
        subject: Sujet de recherche
        max_results: Nombre maximum d'articles à retourner
        
    Returns:
        JSON: Structure de données contenant les articles de Yahoo Actualités
    """
    try:
        articles = scrape_yahoo_news(subject, max_results)
        
        if not articles:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "no article found on Yahoo News",
                    "data": {}
                }
            )
        
        # Créer la structure de données
        feed_data = {
            "source": "Yahoo News",
            "subject": subject,
            "total_articles": len(articles),
            "articles": [
                {
                    "title": article["title"],
                    "url": article["link"],
                    "description": article["description"],
                    "publication_date": article["pub_date"].isoformat() if article["pub_date"] else None,
                    "source": article.get("source", "Yahoo News")
                }
                for article in articles
            ]
        }
        
        # Retourner la réponse JSON
        return JSONResponse(
            status_code=200,
            content={
                "message": f"successfully retrieved {len(articles)} articles from Yahoo News",
                "data": feed_data
            }
        )
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"message":f"Erreur Yahoo News: {str(e)}"})


@router.get("/bing-news/{subject}")
async def get_bing_news_feed(subject: str, max_results: int = 10, db: Session = Depends(get_db)):
    """
    Récupérer les actualités Bing pour un sujet donné
    
    Args:
        subject: Sujet de recherche
        max_results: Nombre maximum d'articles à retourner
        
    Returns:
        JSON: Structure de données contenant les articles de Bing News
    """
    try:
        articles = scrape_bing_news(subject, max_results)
        
        if not articles:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "no article found on Bing News",
                    "data": {}
                }
            )
        
        # Créer la structure de données
        feed_data = {
            "source": "Bing News",
            "subject": subject,
            "total_articles": len(articles),
            "articles": [
                {
                    "title": article["title"],
                    "url": article["link"],
                    "description": article["description"],
                    "publication_date": article["pub_date"].isoformat() if article["pub_date"] else None,
                    "source": article.get("source", "Bing News")
                }
                for article in articles
            ]
        }
        
        # Retourner la réponse JSON
        return JSONResponse(
            status_code=200,
            content={
                "message": f"successfully retrieved {len(articles)} articles from Bing News",
                "data": feed_data
            }
        )
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"message":f"Erreur Bing News: {str(e)}"})


@router.get("/baidu-news/{subject}")
async def get_baidu_news_feed(subject: str, max_results: int = 10, db: Session = Depends(get_db)):
    """
    Générer un feed RSS à partir de Baidu News pour un sujet donné
    """
    try:
        articles = scrape_baidu_news(subject, max_results)
        
        if not articles:
            return JSONResponse(status_code=404, content={"message":"Aucun article trouvé sur Baidu News"})
        
        # Créer le feed RSS
        feed = Rss201rev2Feed(
            title=f"Baidu News: {subject}",
            link="https://news.baidu.com",
            description=f"Articles Baidu sur '{subject}'",
            language="zh-cn",
        )
        
        for article in articles:
            feed.add_item(
                title=article["title"],
                link=article["link"],
                description=article["description"],
                pubdate=article["pub_date"]
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "message":f"Feed Baidu généré avec {len(articles)} articles",
                "feed": feed.writeString('utf-8')
            }
        )
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"message":f"Erreur Baidu News: {str(e)}"})
