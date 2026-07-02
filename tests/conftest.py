import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("CHROMA_PERSIST_DIR", tempfile.mkdtemp())
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder")


@pytest.fixture(scope="session")
def tmp_data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("data")


@pytest.fixture()
def sample_txt_file(tmp_data_dir: Path) -> Path:
    path = tmp_data_dir / "sample.txt"
    path.write_text(
        "Ceci est un document d'appel d'offres exemple.\n\n"
        "Section 1 : Exigences techniques\n"
        "Le système doit traiter les documents automatiquement grâce à l'IA.\n\n"
        "Section 2 : Livrables\n"
        "Un pipeline RAG fonctionnel exposé via une API REST.",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def sample_csv_file(tmp_data_dir: Path) -> Path:
    path = tmp_data_dir / "sample.csv"
    path.write_text(
        "exigence,priorite,notes\n"
        "Temps de réponse API < 2s,Haute,Exigence non fonctionnelle\n"
        "Support ingestion PDF,Haute,Fonctionnalité principale\n"
        "Déploiement Docker,Moyenne,Exigence DevOps\n",
        encoding="utf-8",
    )
    return path
