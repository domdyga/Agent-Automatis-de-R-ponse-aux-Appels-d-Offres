# Agent Automatisé de Réponse aux Appels d'Offres 

> Un agent IA qui lit tes anciens documents d'appels d'offres et génère automatiquement des propositions techniques complètes. Concrètement : tu lui donnes un cahier des charges, il te pond une réponse structurée en quelques secondes.

C'est mon projet de portfolio pour démontrer des compétences en **Data Engineering**, **IA générative**, **RAG** et **déploiement Docker**. Si tu es recruteur ou curieux, bienvenue !

---

## C'est quoi le problème que ça résout ?

Répondre à un appel d'offres, c'est long. Il faut retrouver d'anciens projets similaires, rédiger un résumé exécutif, détailler la méthodologie... et souvent on réécrit les mêmes choses d'un dossier à l'autre.

Ce projet automatise ça : on charge les anciens documents de l'entreprise (propositions, fiches techniques, références), et quand un nouveau cahier des charges arrive, le système retrouve les passages pertinents et génère une proposition sur mesure.

C'est le principe du **RAG (Retrieval-Augmented Generation)** : on ne demande pas à l'IA d'inventer, on lui donne des vraies sources, et elle les synthétise.

---

## Comment ça marche — en clair

```
Tes documents (PDF, Word, CSV...)
        ↓
   Découpage en morceaux
        ↓
   Transformation en vecteurs (embeddings)
        ↓
      ChromaDB (base vectorielle)
        ↓
Nouveau cahier des charges → recherche des passages les plus proches
        ↓
      GPT-4o génère la proposition
        ↓
    Réponse JSON structurée (+ export PDF en bonus)
```

---

## Architecture du projet

```
projet/
├── app/
│   ├── api/
│   │   └── routes.py           → les 5 endpoints FastAPI
│   ├── models/
│   │   └── schemas.py          → tous les modèles Pydantic (entrées/sorties)
│   ├── rag/
│   │   ├── vector_store.py     → connexion à ChromaDB
│   │   ├── retriever.py        → recherche par similarité + score de confiance
│   │   ├── pipeline.py         → orchestration complète du RAG
│   │   ├── prompts.py          → templates de prompts (séparés de la logique)
│   │   ├── memory.py           → mémoire de conversation par session
│   │   └── llm_client.py       → factory OpenAI / Ollama (local)
│   ├── services/
│   │   ├── document_loader.py  → loaders PDF / DOCX / TXT / CSV
│   │   ├── chunker.py          → découpage sémantique des textes
│   │   ├── ingest_service.py   → pipeline d'ingestion complet
│   │   └── proposal_exporter.py→ export PDF avec ReportLab
│   ├── utils/
│   │   ├── config.py           → settings via variables d'environnement
│   │   └── logger.py           → logging structuré
│   └── main.py                 → point d'entrée FastAPI
│
├── data/
│   ├── raw/                    → documents source à ingérer
│   └── processed/              → PDFs générés
│
├── vector_store/               → données ChromaDB (créé automatiquement)
├── tests/                      → tests pytest
├── notebooks/                  → exploration Jupyter
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Technologies utilisées

| Quoi | Pourquoi ce choix |
|---|---|
| **FastAPI** | Rapide à prototyper, doc Swagger auto, typage natif |
| **LangChain** | Abstraction propre pour les chaînes LLM et la mémoire |
| **ChromaDB** | Base vectorielle légère, pas besoin de serveur séparé |
| **OpenAI GPT-4o** | Meilleure qualité de génération pour des textes longs |
| **PyPDF / python-docx** | Extraction de texte des formats courants en entreprise |
| **Docker** | Déploiement reproductible en une commande |

---

## Lancer le projet

### Ce qu'il faut avoir installé

- Python 3.12+
- Docker Desktop (pour l'option Docker)
- Une clé API OpenAI

### Option 1 — Avec Docker (recommandé)

```bash
# 1. Cloner le projet
git clone https://github.com/ton-username/tender-response-agent.git
cd tender-response-agent

# 2. Créer le fichier de config
cp .env.example .env
# Ouvrir .env et renseigner OPENAI_API_KEY=sk-...

# 3. Lancer
docker-compose up --build
```

L'API est dispo sur **http://localhost:8000/docs** 🎉

### Option 2 — En local (plus rapide pour développer)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\Activate.ps1

pip install -r requirements.txt

cp .env.example .env             # renseigner OPENAI_API_KEY

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Variables d'environnement

À copier dans un fichier `.env` à la racine :

```env
OPENAI_API_KEY=sk-...            # obligatoire
OPENAI_MODEL=gpt-4o              # modèle de génération
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

CHROMA_PERSIST_DIR=./vector_store
CHROMA_COLLECTION_NAME=tender_docs

CHUNK_SIZE=1000                  # taille des morceaux de texte
CHUNK_OVERLAP=200                # chevauchement entre morceaux
TOP_K_RESULTS=5                  # nombre de sources récupérées par requête

LOG_LEVEL=INFO
```

> Ne jamais commiter le `.env` — il est dans le `.gitignore`.

---

## Les endpoints de l'API

La doc interactive complète est sur **`/docs`** après démarrage.

### `GET /api/v1/health` — vérifier que tout tourne

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "ok",
  "vector_store": "chromadb",
  "llm_model": "gpt-4o",
  "embedding_model": "text-embedding-3-small",
  "documents_indexed": 42
}
```

---

### `POST /api/v1/upload` — uploader un document

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@data/raw/exemple_proposition.txt"
```

Formats acceptés : **PDF, DOCX, TXT, CSV**

---

### `POST /api/v1/ingest` — indexer le document dans ChromaDB

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/raw/exemple_proposition.txt",
    "metadata": {"projet": "ministere-finance", "annee": "2023"}
  }'
```

```json
{
  "chunks_created": 12,
  "collection_name": "tender_docs",
  "message": "12 chunks ingérés avec succès."
}
```

---

### `POST /api/v1/generate-proposal` — générer une proposition

C'est l'endpoint principal. On lui donne le contexte du nouveau projet, il retrouve les infos pertinentes dans les anciens documents et génère une proposition complète.

```bash
curl -X POST http://localhost:8000/api/v1/generate-proposal \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Acme Consulting",
    "client_name": "Parlement Européen",
    "project_description": "Plateforme d'\''analyse de données parlementaires.",
    "requirements": [
      "Déploiement cloud AWS",
      "Ingestion temps-réel depuis 20 sources",
      "Tableaux de bord self-service",
      "Conformité RGPD"
    ],
    "budget_range": "500k–800k€",
    "deadline": "Décembre 2025"
  }'
```

```json
{
  "project_title": "Plateforme Cloud-Native d'Analyse pour le Parlement Européen",
  "executive_summary": "Acme Consulting propose une architecture moderne...",
  "technical_approach": "Notre approche s'appuie sur AWS (S3, Glue, Redshift)...",
  "methodology": "Phase 1 — Cadrage (semaines 1-4)...",
  "project_organization": "L'équipe sera pilotée par une directrice de projet certifiée PMP...",
  "conclusion": "Acme Consulting est idéalement positionné pour...",
  "sources": [
    {
      "source": "data/raw/exemple_proposition.txt",
      "relevance_score": 0.87,
      "excerpt": "Nous avons adopté une architecture data lakehouse..."
    }
  ],
  "confidence_score": 0.82,
  "generation_model": "gpt-4o"
}
```

Ajouter `?export_pdf=true` pour générer aussi un fichier PDF dans `data/processed/`.

---

### `POST /api/v1/ask` — poser une question sur les documents

Pratique pour explorer la base de connaissances avant de générer une proposition.

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelles certifications cloud avons-nous ?"}'
```

La réponse inclut un `conversation_id` — tu peux le réutiliser pour poser des questions de suivi et maintenir le contexte.

---

## Lancer les tests

```bash
pip install pytest pytest-asyncio httpx

pytest tests/ -v
```

Les tests couvrent : le chargement de documents, le découpage, la recherche de similarité et les endpoints API. Ils utilisent des mocks pour ne pas faire d'appels OpenAI réels.

---

## Ce que j'ai appris en faisant ce projet

- Comment fonctionne vraiment le RAG (pas juste la théorie)
- Pourquoi séparer les prompts de la logique métier rend le code beaucoup plus maintenable
- L'importance de la taille des chunks : trop grands = contexte bruité, trop petits = perte de sens
- Comment structurer une API FastAPI proprement avec injection de dépendances
- Les subtilités du déploiement Docker multi-stage pour garder une image légère

---

## Pistes d'amélioration

- [ ] Interface web (Streamlit ou Next.js)
- [ ] Authentification (clés API ou OAuth2)
- [ ] Ingestion en arrière-plan (tâches asynchrones avec Celery)
- [ ] Métriques d'évaluation RAG (framework RAGAS)
- [ ] Support FAISS comme alternative à ChromaDB
- [ ] Endpoint batch pour ingérer un dossier entier

---

## Licence

MIT — libre d'utilisation.

---

*Projet réalisé dans le cadre d'un portfolio Junior Data Analyst / AI Developer.*  
*N'hésite pas à ouvrir une issue ou à me contacter si tu as des questions !*
