"""
Tests d'intégration pour les endpoints FastAPI.

On utilise TestClient de FastAPI + des mocks pour :
  - ne pas démarrer un vrai ChromaDB
  - ne pas faire d'appels réels à OpenAI
  - tester uniquement la logique des endpoints (validation, codes HTTP, etc.)

Chaque classe teste un endpoint. On commence par les cas qui marchent,
puis on teste les cas d'erreur (formats invalides, champs manquants...).
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.schemas import SourceDocument


@pytest.fixture()
def mock_vs():
    vs = MagicMock()
    vs.count_documents.return_value = 10
    vs.similarity_search.return_value = []
    vs.add_documents.return_value = ["id1", "id2"]
    return vs


@pytest.fixture()
def client(mock_vs):
    from app.api.routes import get_vector_store as _gvs
    from app.main import app
    app.dependency_overrides[_gvs] = lambda: mock_vs
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# GET /health

class TestHealth:

    def test_retourne_ok(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_affiche_nombre_de_documents(self, client):
        assert client.get("/api/v1/health").json()["documents_indexed"] == 10

    def test_schema_complet(self, client):
        data = client.get("/api/v1/health").json()
        for champ in ["vector_store", "llm_model", "embedding_model"]:
            assert champ in data


# POST /upload

class TestUpload:

    def test_upload_txt(self, client):
        contenu = b"Bonjour appel d'offres"
        r = client.post("/api/v1/upload", files={"file": ("test.txt", io.BytesIO(contenu), "text/plain")})
        assert r.status_code == 201
        assert r.json()["filename"] == "test.txt"
        assert r.json()["size_bytes"] == len(contenu)

    def test_rejette_extension_inconnue(self, client):
        r = client.post("/api/v1/upload", files={"file": ("truc.exe", io.BytesIO(b"data"), "application/octet-stream")})
        assert r.status_code == 415

    def test_rejette_nom_vide(self, client):
        r = client.post("/api/v1/upload", files={"file": ("", io.BytesIO(b"data"), "text/plain")})
        assert r.status_code == 400


# POST /ingest

class TestIngest:

    def test_erreur_fichier_inexistant(self, client):
        r = client.post("/api/v1/ingest", json={"file_path": "/chemin/inexistant/doc.txt"})
        assert r.status_code in (404, 422)


# POST /ask

class TestAsk:

    def test_question_obligatoire(self, client):
        assert client.post("/api/v1/ask", json={}).status_code == 422

    def test_question_trop_courte(self, client):
        # "hi" = 2 chars, min_length=3
        assert client.post("/api/v1/ask", json={"question": "hi"}).status_code == 422


# POST /generate-proposal

class TestGenerateProposal:

    def test_corps_vide_rejete(self, client):
        assert client.post("/api/v1/generate-proposal", json={}).status_code == 422

    def test_liste_exigences_vide_rejetee(self, client):
        r = client.post("/api/v1/generate-proposal", json={
            "company_name": "Acme",
            "client_name": "Gouvernement",
            "project_description": "Une nouvelle plateforme de données",
            "requirements": [],  # liste vide → doit être rejetée
        })
        assert r.status_code == 422
