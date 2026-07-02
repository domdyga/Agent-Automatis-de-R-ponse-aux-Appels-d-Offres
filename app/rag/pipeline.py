from __future__ import annotations
import json
import re

from langchain_core.output_parsers import StrOutputParser

from app.models.schemas import AskResponse, ProposalResponse
from app.rag import memory as mem
from app.rag.llm_client import get_llm
from app.rag.prompts import ASK_PROMPT, PROPOSAL_PROMPT
from app.rag.retriever import build_context_string, retrieve
from app.rag.vector_store import VectorStore
from app.utils.config import get_settings
from app.utils.logger import logger


def answer_question(
    question: str,
    vector_store: VectorStore,
    conversation_id: str | None,
    top_k: int | None = None,
) -> AskResponse:
    settings = get_settings()

    sources, confidence = retrieve(question, vector_store, top_k=top_k or settings.top_k_results)
    context = build_context_string(sources) if sources else "Aucun document pertinent trouvé."

    conv_id, memory = mem.get_or_create(conversation_id)
    history = memory.load_memory_variables({}).get("chat_history", "")

    chain = ASK_PROMPT | get_llm() | StrOutputParser()
    answer = chain.invoke({"context": context, "chat_history": str(history), "question": question})

    mem.save_exchange(conv_id, question, answer)
    logger.info("Réponse ok (conv=%s, confiance=%.3f)", conv_id, confidence)

    return AskResponse(answer=answer, conversation_id=conv_id, sources=sources, confidence_score=confidence)


def generate_proposal(
    company_name: str,
    client_name: str,
    project_description: str,
    requirements: list[str],
    budget_range: str | None,
    deadline: str | None,
    vector_store: VectorStore,
) -> ProposalResponse:
    settings = get_settings()

    query = f"{project_description}\n" + "\n".join(requirements)
    sources, confidence = retrieve(query, vector_store, top_k=settings.top_k_results)
    context = build_context_string(sources) if sources else "Aucun document interne disponible."

    chain = PROPOSAL_PROMPT | get_llm() | StrOutputParser()
    raw = chain.invoke({
        "context": context,
        "company_name": company_name,
        "client_name": client_name,
        "project_description": project_description,
        "requirements_list": "\n".join(f"- {r}" for r in requirements),
        "budget_range": budget_range or "Non précisé",
        "deadline": deadline or "Non précisé",
    })

    payload = _extract_json(raw)
    logger.info("Proposition générée : %s → %s (confiance=%.3f)", company_name, client_name, confidence)

    return ProposalResponse(
        company_name=company_name,
        client_name=client_name,
        project_title=payload.get("project_title", f"Proposition pour {client_name}"),
        executive_summary=payload["executive_summary"],
        technical_approach=payload["technical_approach"],
        methodology=payload["methodology"],
        project_organization=payload["project_organization"],
        conclusion=payload["conclusion"],
        sources=sources,
        confidence_score=confidence,
        generation_model=settings.openai_model,
    )


def _extract_json(text: str) -> dict:
    # GPT entoure parfois le JSON de ```json ... ``` même quand on lui dit de pas le faire
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("JSON invalide : %s\n%s", exc, text[:500])
        raise ValueError(f"Le LLM a retourné un JSON invalide : {exc}") from exc
