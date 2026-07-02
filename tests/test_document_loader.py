import pytest
from app.services.document_loader import _clean_text, load_csv, load_document, load_txt


class TestCleanText:

    def test_supprime_espaces(self):
        assert _clean_text("  bonjour  ") == "bonjour"

    def test_reduit_espaces_multiples(self):
        assert _clean_text("bonjour   monde") == "bonjour monde"

    def test_reduit_sauts_de_ligne(self):
        assert _clean_text("a\n\n\n\nb") == "a\n\nb"


class TestLoadTxt:

    def test_charge_contenu(self, sample_txt_file):
        docs = load_txt(sample_txt_file)
        assert len(docs) == 1
        assert "appel d'offres" in docs[0].page_content

    def test_metadonnees_source(self, sample_txt_file):
        docs = load_txt(sample_txt_file)
        assert docs[0].metadata["source"] == str(sample_txt_file)
        assert docs[0].metadata["file_type"] == "txt"

    def test_erreur_si_vide(self, tmp_path):
        vide = tmp_path / "vide.txt"
        vide.write_text("")
        with pytest.raises(ValueError, match="vide"):
            load_txt(vide)


class TestLoadCsv:

    def test_un_doc_par_ligne(self, sample_csv_file):
        docs = load_csv(sample_csv_file)
        assert len(docs) == 3

    def test_contenu_present(self, sample_csv_file):
        docs = load_csv(sample_csv_file)
        assert "Temps de réponse" in docs[0].page_content

    def test_numero_de_ligne(self, sample_csv_file):
        docs = load_csv(sample_csv_file)
        assert docs[0].metadata["row"] == 1


class TestLoadDocument:

    def test_charge_txt(self, sample_txt_file):
        assert len(load_document(sample_txt_file)) >= 1

    def test_charge_csv(self, sample_csv_file):
        assert len(load_document(sample_csv_file)) >= 1

    def test_erreur_format_inconnu(self, tmp_path):
        f = tmp_path / "fichier.xyz"
        f.write_text("contenu")
        with pytest.raises(ValueError, match="non supporté"):
            load_document(f)

    def test_erreur_fichier_manquant(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_document(tmp_path / "nexistepas.txt")
