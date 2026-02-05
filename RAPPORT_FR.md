# Générateur de FAQ — Rapport de Projet (Français)

**Titre du projet :** Génération de FAQ à partir d’une page Web (Scraping → LLM → JSON strict)

**Date :** 05/02/2026

**Auteur(s) :** _[Votre Nom]_  
**UE / Module :** _[Nom du cours]_  
**Encadrant :** _[Nom de l’encadrant]_  
**Établissement :** _[Nom de l’université]_  

---

## Résumé
Ce projet met en place un outil local permettant de transformer le contenu textuel d’un site Web en un jeu de données FAQ structuré. Le système (1) récupère et nettoie le texte d’une page via du scraping, (2) interroge un modèle de langage (Google Gemini) afin de produire **exactement cinq** paires question/réponse ancrées dans le texte fourni, et (3) renvoie le résultat sous forme de **JSON strict**. Une API Flask et une interface Web minimaliste permettent une utilisation simple, tandis qu’un script CLI offre une alternative en ligne de commande.

**Mots-clés :** scraping Web, BeautifulSoup, API Flask, Gemini, ingénierie de prompt, contrat JSON, génération de FAQ

---

## 1. Introduction
De nombreuses informations utiles sont publiées sur des pages Web sous forme non structurée. Construire une FAQ à partir de ces contenus est une tâche répétitive. L’objectif est donc d’automatiser la création d’une FAQ cohérente tout en imposant un format de sortie exploitable par une machine (JSON).

---

## 2. Problématique
À partir d’une URL (ou d’un texte), produire automatiquement un objet JSON contenant cinq questions/réponses de type FAQ, où les réponses sont basées sur le contenu textuel récupéré. Le système doit être robuste face :
- au bruit des pages HTML (menus, scripts, styles) ;
- aux écarts possibles de sortie d’un LLM (texte hors JSON, mauvais schéma, nombre d’items incorrect) ;
- au besoin d’une utilisation simple (interface Web) et automatisable (CLI).

---

## 3. Objectifs
### 3.1 Objectifs fonctionnels
1. Scraper et nettoyer le texte d’une page Web.
2. Générer **exactement 5** entrées de FAQ au format JSON strict.
3. Fournir une API permettant de lancer la génération.
4. Fournir une interface Web minimaliste pour entrer l’URL et télécharger le JSON.
5. Fournir un mode CLI pour une utilisation en terminal.

### 3.2 Objectifs non fonctionnels
- Simplicité d’installation sur Windows.
- Gestion claire de la configuration via `.env`.
- Messages d’erreur utiles (scraping, modèle, parsing JSON).

---

## 4. Spécifications
### 4.1 Entrées
- `url` (HTTP/HTTPS) **ou** `text` (texte collé).

### 4.2 Contrat de sortie (JSON)
Le format attendu est :

```json
{
  "faqs": [
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."}
  ]
}
```

Contraintes :
- 5 objets exactement.
- `question` et `answer` sont des chaînes de caractères.
- aucune sortie en Markdown ; **JSON uniquement**.

### 4.3 Configuration
Variables prises en charge :
- `GEMINI_API_KEY` ou `GOOGLE_API_KEY` — clé d’API
- `OPENAI_MODEL` — nom du modèle (par défaut `gemini-2.5-flash-lite`)

---

## 5. Vue d’ensemble du système
Le projet propose deux modes :

1. **Mode Web** (interactif)
   - Backend Flask : `web_app.py`
   - UI statique : `static/index.html`, `static/app.js`, `static/style.css`
2. **Mode CLI** : `faq_generator.py`

### 5.1 Architecture globale

```
Utilisateur (UI/CLI)
   |
   v
API Flask (/generate)
   |
   +--> Scraping (requests + BeautifulSoup)
   |
   +--> Construction du prompt (contrat JSON)
   |
   +--> Appel Gemini (SDK google-genai, fallback REST)
   |
   +--> Parsing/validation JSON
   v
Réponse JSON (succès ou erreur)
```

---

## 6. Détails d’implémentation
### 6.1 Scraping et nettoyage
Stratégie utilisée :
- téléchargement HTML via `requests` ;
- parsing avec `BeautifulSoup` ;
- suppression des balises `script`, `style`, `noscript` ;
- extraction du texte visible ;
- normalisation des espaces ;
- limitation de la taille (≈ 25 000 caractères) pour réduire le coût et la latence.

### 6.2 Ingénierie de prompt
Le prompt impose explicitement :
- un seul objet JSON ;
- une seule clé de premier niveau : `faqs` ;
- exactement 5 objets ;
- des réponses concises et basées sur le texte fourni.

Ce choix vise à limiter les sorties “créatives” hors format et à faciliter le parsing.

### 6.3 Intégration du modèle (Gemini)
Deux approches sont implémentées :
1. appel via SDK officiel `google-genai` ;
2. fallback via endpoint REST `generativelanguage.googleapis.com` si le SDK échoue.

Ce design améliore la robustesse en cas de variations de versions du SDK.

### 6.4 Parsing JSON et gestion d’erreurs
Le backend tente un `json.loads()` sur la sortie du modèle :
- succès : renvoie `{success: true, faqs: ...}` ;
- échec : renvoie `{success: false, error: ..., raw: ...}` avec code HTTP 502.

Cette transparence aide au diagnostic en cas de réponse non conforme.

### 6.5 Endpoints Flask
- `GET /health` : état du service + présence de clé + modèle.
- `POST /generate` : génération à partir de `url` ou `text`.
- `GET /scraped` : accès au fichier `scraped_page.txt`.
- `GET /` : sert l’UI si `index.html` existe.

### 6.6 Interface Web
L’UI a été volontairement simplifiée :
- un seul champ URL ;
- bouton “Generate” ;
- bouton “Download JSON” ;
- lien “View scraped text”.

---

## 7. Stockage et traçabilité
Le texte utilisé est sauvegardé dans `scraped_page.txt` afin de :
- vérifier la qualité du scraping ;
- comparer le contenu source et les FAQ générées ;
- faciliter le débogage.

---

## 8. Validation et tests
Validation principalement manuelle :
- `GET /health` ;
- génération sur des URLs de test ;
- vérification : JSON parseable et 5 items.

Tests recommandés (améliorations) :
- tests unitaires sur le nettoyage HTML ;
- tests de contrat sur la taille de `faqs` ;
- fixtures HTML pour tests reproductibles.

---

## 9. Limites
- Le scraping peut inclure du contenu répétitif (menus, footer).
- Les pages nécessitant du rendu JavaScript ne sont pas supportées.
- L’exigence “exactement 5” dépend du respect des consignes par le modèle ; le backend n’effectue pas de “réparation” automatique.
- Disponibilité des modèles : certaines clés n’ont pas accès à certains noms de modèles.

---

## 10. Sécurité et aspects éthiques
- Ne jamais versionner la clé API : `.env` doit rester local.
- Respecter les conditions d’utilisation des sites et éviter le scraping abusif.
- Pour des usages sensibles, prévoir une validation humaine (risque d’hallucination).

---

## 11. Conclusion
Le projet fournit une chaîne complète et simple pour transformer le contenu d’une page Web en un JSON de FAQ exploitable. L’association scraping + prompt strict + parsing JSON + UI légère constitue une base solide pour des extensions futures (multi-pages, validation renforcée, export multi-format).

---

## 12. Pistes d’amélioration
- Re-prompt automatique en cas de JSON invalide.
- Filtrage de boilerplate (menus, répétitions) via heuristiques.
- Crawl multi-pages (sitemap, liens internes).
- Choix de langue (FR/EN) côté UI.
- Conteneurisation (Docker) et sécurisation d’accès.

---

## Annexe A — Exécution locale (Windows)
1. Dépendances :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

2. Fichier `.env` :

```
GEMINI_API_KEY=...
OPENAI_MODEL=gemini-2.5-flash-lite
```

3. Lancement :

```powershell
python web_app.py
```

4. UI :

http://127.0.0.1:5000/static/index.html

---

## Annexe B — Structure du dépôt (typique)
```
faq_generator.py
web_app.py
web_scraper.py
requirements.txt
.env
static/
  index.html
  app.js
  style.css
scraped_page.txt
```
