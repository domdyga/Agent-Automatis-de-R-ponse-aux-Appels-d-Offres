from __future__ import annotations
import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from app.models.schemas import ProposalResponse
from app.utils.logger import logger

_OUTPUT_DIR = Path("data/processed")


def export_proposal_to_pdf(proposal: ProposalResponse, output_dir: Path | None = None) -> Path:
    out_dir = output_dir or _OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_title = "".join(c if c.isalnum() or c in "- " else "_" for c in proposal.project_title)
    pdf_path = out_dir / f"{safe_title[:60]}.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                            rightMargin=2.5*cm, leftMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=22, spaceAfter=12)
    h_style = ParagraphStyle("H", parent=styles["Heading1"], fontSize=14, spaceBefore=16, spaceAfter=6)
    body = styles["BodyText"]
    body.leading = 16

    story = []

    # page de garde
    story.append(Paragraph(proposal.project_title, title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"<b>Soumis par :</b> {proposal.company_name}", body))
    story.append(Paragraph(f"<b>À l'attention de :</b> {proposal.client_name}", body))
    story.append(Paragraph(f"<b>Confiance :</b> {proposal.confidence_score:.0%}", body))
    story.append(PageBreak())

    for title, content in [
        ("Résumé Exécutif", proposal.executive_summary),
        ("Approche Technique", proposal.technical_approach),
        ("Méthodologie", proposal.methodology),
        ("Organisation du Projet", proposal.project_organization),
        ("Conclusion", proposal.conclusion),
    ]:
        story.append(Paragraph(title, h_style))
        story.append(Paragraph("<br/>".join(textwrap.wrap(content, width=120)), body))
        story.append(Spacer(1, 0.5*cm))

    if proposal.sources:
        story.append(Paragraph("Sources", h_style))
        for i, src in enumerate(proposal.sources, start=1):
            story.append(Paragraph(f"[{i}] {src.source} — {src.relevance_score:.0%}", body))

    doc.build(story)
    logger.info("PDF généré → %s", pdf_path)
    return pdf_path
