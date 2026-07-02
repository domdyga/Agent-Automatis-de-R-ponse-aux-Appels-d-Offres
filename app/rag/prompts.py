from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

# --- prompt pour /ask ---

ASK_SYSTEM = """Tu es un expert en appels d'offres et réponses à des RFP.

Réponds uniquement à partir des extraits ci-dessous. Si la réponse n'est pas dedans,
dis-le clairement. Cite tes sources avec [Source N].

Contexte :
{context}

Historique :
{chat_history}
"""

ASK_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(ASK_SYSTEM),
    ("human", "{question}"),
])

# --- prompt pour /generate-proposal ---

PROPOSAL_SYSTEM = """Tu es un expert en rédaction de propositions commerciales et techniques.
Appuie-toi sur les documents internes ci-dessous pour personnaliser ta réponse.
Sois précis et professionnel.

Documents internes :
{context}
"""

PROPOSAL_HUMAN = """Génère une proposition technique avec ces informations :

Entreprise : {company_name}
Client : {client_name}
Projet : {project_description}
Exigences :
{requirements_list}
Budget : {budget_range}
Délai : {deadline}

Réponds avec ce JSON exact (sans markdown autour) :
{{
  "project_title": "...",
  "executive_summary": "...",
  "technical_approach": "...",
  "methodology": "...",
  "project_organization": "...",
  "conclusion": "..."
}}

Chaque section doit faire au moins 150 mots.
"""

PROPOSAL_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(PROPOSAL_SYSTEM),
    ("human", PROPOSAL_HUMAN),
])
