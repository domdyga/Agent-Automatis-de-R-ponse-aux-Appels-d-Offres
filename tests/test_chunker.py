from langchain_core.documents import Document
from app.services.chunker import chunk_documents


def _doc(text: str, source: str = "test.txt") -> Document:
    return Document(page_content=text, metadata={"source": source})


class TestChunkDocuments:

    def test_court_doc_reste_un_chunk(self):
        chunks = chunk_documents([_doc("Texte court.")], chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 1

    def test_long_doc_est_decoupe(self):
        chunks = chunk_documents([_doc("Mot " * 600)], chunk_size=500, chunk_overlap=50)
        assert len(chunks) > 1

    def test_index_consecutifs(self):
        chunks = chunk_documents([_doc("Mot " * 600)], chunk_size=500, chunk_overlap=50)
        assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))

    def test_metadata_taille_presente(self):
        chunks = chunk_documents([_doc("Bonjour monde.")], chunk_size=500, chunk_overlap=0)
        assert all("chunk_size" in c.metadata for c in chunks)

    def test_source_preservee(self):
        chunks = chunk_documents([_doc("Du texte", source="mon_fichier.pdf")], chunk_size=500, chunk_overlap=0)
        assert all(c.metadata["source"] == "mon_fichier.pdf" for c in chunks)

    def test_plusieurs_docs(self):
        docs = [_doc("A " * 300), _doc("B " * 300)]
        assert len(chunk_documents(docs, chunk_size=200, chunk_overlap=20)) >= 2
