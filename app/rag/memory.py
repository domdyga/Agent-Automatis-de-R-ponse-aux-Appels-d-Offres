"""
Mémoire de conversation simple.
On garde les 10 derniers échanges par session, stockés en RAM.
Si on redémarre le serveur, la mémoire repart de zéro — c'est ok pour l'instant.
"""
from __future__ import annotations
import uuid
from collections import defaultdict

from langchain.memory import ConversationBufferWindowMemory

_WINDOW_SIZE = 10
_registry: dict[str, ConversationBufferWindowMemory] = defaultdict()


def get_or_create(conversation_id: str | None) -> tuple[str, ConversationBufferWindowMemory]:
    if conversation_id and conversation_id in _registry:
        return conversation_id, _registry[conversation_id]

    new_id = conversation_id or str(uuid.uuid4())
    memory = ConversationBufferWindowMemory(k=_WINDOW_SIZE, memory_key="chat_history", return_messages=True)
    _registry[new_id] = memory
    return new_id, memory


def save_exchange(conversation_id: str, human: str, ai: str) -> None:
    _, memory = get_or_create(conversation_id)
    memory.save_context({"input": human}, {"output": ai})


def get_history(conversation_id: str) -> list[dict]:
    _, memory = get_or_create(conversation_id)
    return memory.load_memory_variables({}).get("chat_history", [])
