# Site to RSS Scraper

Une application FastAPI qui convertit n'importe quel site web en flux RSS en extrayant automatiquement les articles et leurs informations associées.

## 🚀 Fonctionnalités

- Conversion de n'importe quel site web en flux RSS
- Extraction automatique des articles avec :
  - Titre
  - Description
  - Image principale
  - Date de publication
  - Lien vers l'article
- Détection automatique du logo/favicon du site
- Déduplication des articles
- Support du HTML dans les descriptions RSS

## 📋 Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)

## 🛠️ Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/Achaire-Zogo/Kairos-Scrapping.git
cd Kairos-Scrapping
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt 
```
Ou 
```bash
pip3 install -r requirements.txt
```

## 🚀 Démarrage

1. Lancez l'application :
```bash
python main.py
```
OU
```bash
python3 main.py
```

2. L'application sera accessible à l'adresse : `http://localhost:5001`

## 📖 Utilisation

1. Vous pouvez tester ici : `http://localhost:5001/docs`

### Endpoint principal

- URL : `/feed`
- Méthode : GET
- Paramètre : `url` (l'URL du site à scraper)
- Exemple : `http://localhost:5000/feed?url=https://example.com`

### Format de retour

L'application retourne un flux RSS au format XML avec la structure suivante :

```xml
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>[Titre du site]</title>
    <link>[URL du site]</link>
    <description>[Description du site]</description>
    <image>
      <url>[URL du favicon/logo]</url>
      <title>[Titre du site]</title>
      <link>[URL du site]</link>
    </image>
    <item>
      <title>[Titre de l'article]</title>
      <link>[URL de l'article]</link>
      <description>
        <![CDATA[
          <img src="[URL de l'image]" />
          [Description de l'article]
        ]]>
      </description>
      <pubDate>[Date de publication]</pubDate>
    </item>
    <!-- Plus d'articles... -->
  </channel>
</rss>
```

### Codes de retour

- **200** : Succès
  - Retourne le flux RSS au format XML
- **400** : Erreur de requête
  - URL invalide
  - Site inaccessible
  - Erreur lors du scraping
- **404** : Aucun article trouvé
  - Le site est accessible mais aucun article n'a été détecté
- **500** : Erreur serveur
  - Erreur interne lors du traitement

## 🔍 Détection des articles

L'application utilise plusieurs stratégies pour détecter les articles :

1. **Structure HTML** : Recherche des balises `<article>`, `<div>`, `<section>`
2. **Titres** : Détection des `<h1>`, `<h2>`, `<h3>` comme titres d'articles
3. **Images** : Recherche des images principales via :
   - Métadonnées OpenGraph
   - Classes CSS spécifiques (featured, main, hero, etc.)
   - Première image de taille significative
   - Images d'arrière-plan en CSS

## 🔄 Déduplication

Les articles sont dédupliqués selon :
- Titres identiques (insensible à la casse)
- URLs identiques

## 📝 Limitations

- Les sites nécessitant une authentification ne sont pas supportés
- Le JavaScript dynamique n'est pas exécuté lors du scraping
- Certains sites peuvent bloquer le scraping
- Le nombre d'articles est limité à ceux présents sur la page principale

## 📜 Licence

MIT License
