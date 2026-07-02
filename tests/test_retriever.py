from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from app.models.schemas import SourceDocument
from app.rag.retriever import build_context_string, retrieve


def _mock_vs(results=None):
    vs = MagicMock()
    vs.similarity_search.return_value = results if results is not None else [
        (Document(page_content="Expérience en infrastructure cloud.", metadata={"source": "proposition.pdf"}), 0.2),
        (Document(page_content="5 architectes certifiés dans l'équipe.", metadata={"source": "equipe.docx"}), 0.35),
    ]
    return vs


class TestRetrieve:

    def test_retourne_source_documents(self):
        sources, _ = retrieve("cloud", _mock_vs())
        assert len(sources) == 2
        assert all(isinstance(s, SourceDocument) for s in sources)

    def test_confiance_moyenne_des_scores(self):
        sources, confidence = retrieve("cloud", _mock_vs())
        assert abs(confidence - sum(s.relevance_score for s in sources) / len(sources)) < 1e-6

    def test_aucun_resultat(self):
        sources, confidence = retrieve("quelque chose", _mock_vs(results=[]))
        assert sources == [] and confidence == 0.0

    def test_requete_vide(self):
        with pytest.raises(ValueError, match="vide"):
            retrieve("   ", _mock_vs())

    def test_extrait_tronque(self):
        vs = _mock_vs(results=[(Document(page_content="A" * 1000, metadata={"source": "x.pdf"}), 0.1)])
        sources, _ = retrieve("requête", vs)
        assert len(sources[0].excerpt) <= 305


class TestBuildContextString:

    def test_sources_numerotees(self):
        sources = [
            SourceDocument(source="a.pdf", relevance_score=0.9, excerpt="Bonjour"),
            SourceDocument(source="b.pdf", relevance_score=0.7, excerpt="Monde"),
        ]
        ctx = build_context_string(sources)
        assert "[Source 1]" in ctx and "[Source 2]" in ctx

    def test_vide_retourne_chaine_vide(self):
        assert build_context_string([]) == ""
