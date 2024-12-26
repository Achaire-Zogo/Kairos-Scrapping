from fastapi import FastAPI, HTTPException, Response
from bs4 import BeautifulSoup
import requests
from feedgenerator import Rss201rev2Feed
from datetime import datetime
from urllib.parse import urljoin, urlparse
import favicon
from typing import Optional

app = FastAPI(title="Site to RSS Scraper")

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

@app.get("/feed")
async def get_feed(url: str):
    try:
        # Vérifier l'URL
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL invalide")
            
        # Faire la requête HTTP
        response = requests.get(url)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Obtenir les informations du site
        site_info = get_site_info(url)
        
        # Créer le flux RSS
        feed = Rss201rev2Feed(
            title=site_info["title"],
            link=url,
            description=site_info["description"],
            language="fr",
            image_url=site_info["icon_url"]
        )
        
        # Extraire et ajouter les articles
        articles = extract_articles(url, soup)
        
        if not articles:
            raise HTTPException(status_code=404, detail="Aucun article trouvé sur cette page")
            
        for article in articles:
            feed.add_item(
                title=article["title"],
                link=article["link"] or url,
                description=article["description"],
                pubdate=article["pub_date"]
            )
        
        # Générer le XML
        return Response(
            content=feed.writeString('utf-8'),
            media_type="application/rss+xml"
        )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la requête HTTP: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
