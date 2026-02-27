"""RAG engine for answering university questions."""
from typing import List, Dict, Optional
from openai import OpenAI
from .config import Config
from .qdrant_rest import QdrantRESTClient as VectorStore


class RAGEngine:
    """Retrieval-Augmented Generation engine for Q&A."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize the RAG engine.

        Args:
            vector_store: VectorStore instance for retrieval
        """
        self.vector_store = vector_store or VectorStore()
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

        self.system_prompt = """Tu es UniHelp, un assistant IA pour les services universitaires de l'Institut International de Technologie / NAU.

Ton rôle est d'aider les étudiants en répondant à leurs questions sur:
- Inscription et réinscription
- Certificats et attestations
- Bourses et aides financières
- Stages et conventions
- Absences et justifications
- Rattrapage et examens
- Paiement des frais
- Calendrier académique
- Règlement intérieur

BASES DE CONNAISSANCE:
Utilise uniquement les documents fournis dans le contexte pour répondre. Si l'information n'est pas dans les documents, indique-le poliment.

STYLE DE RÉPONSE:
- Sois précis et factuel
- Utilise un langage clair et accessible
- Structure tes réponses avec des puces quand approprié
- Donne les références des documents quand possible
- Sois courtois et professionnel

Réponds toujours en français sauf si l'étudiant pose une question en anglais."""

    def retrieve_context(self, query: str, k: int = 5) -> str:
        """
        Retrieve relevant context for a query.

        Args:
            query: User question
            k: Number of documents to retrieve

        Returns:
            Formatted context string
        """
        results = self.vector_store.search(query, limit=k)

        if not results:
            return "Aucun document pertinent trouvé."

        context_parts = []
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "Document inconnu")
            context_parts.append(
                f"[Document {i} - {source}]\n{result['text']}"
            )

        return "\n\n".join(context_parts)

    def answer(self, question: str, context: Optional[str] = None) -> Dict:
        """
        Generate an answer to a question using RAG.

        Args:
            question: User question
            context: Optional pre-retrieved context

        Returns:
            Dictionary with answer and sources
        """
        # Retrieve context if not provided
        if context is None:
            context = self.retrieve_context(question)

        # Generate response
        response = self.openai_client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"CONTEXTE:\n{context}\n\nQUESTION: {question}"}
            ],
            temperature=0.3,
            max_tokens=800
        )

        answer = response.choices[0].message.content

        # Extract sources from context
        sources = self._extract_sources(context)

        return {
            "answer": answer,
            "sources": sources,
            "context_used": bool(sources)
        }

    def chat(self, question: str, history: List[Dict] = None) -> Dict:
        """
        Chat mode with conversation history.

        Args:
            question: Current user question
            history: List of previous messages

        Returns:
            Response with answer
        """
        # Retrieve relevant context
        context = self.retrieve_context(question)

        # Build messages
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add history
        if history:
            messages.extend(history[-6:])  # Keep last 3 exchanges

        # Add current question with context
        messages.append({
            "role": "user",
            "content": f"CONTEXTE:\n{context}\n\nQUESTION: {question}"
        })

        # Generate response
        response = self.openai_client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=messages,
            temperature=0.4,
            max_tokens=800
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": self._extract_sources(context)
        }

    def _extract_sources(self, context: str) -> List[str]:
        """Extract source document names from context."""
        import re
        pattern = r'\[Document \d+ - ([^\]]+)\]'
        matches = re.findall(pattern, context)
        return list(set(matches))


class EmailGenerator:
    """Generate administrative emails based on templates."""

    def __init__(self):
        """Initialize the email generator."""
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

        self.system_prompt = """Tu es un assistant qui génère des emails administratifs professionnels pour les étudiants de l'Institut International de Technologie.

Génère des emails:
- Formels et professionnels
- Concis et clairs
- Avec un objet approprié
- Correctement structurés (salutation, corps, formule de politesse)

Types de demandes courantes:
- Demande d'attestation de scolarité
- Demande de certificat de réussite
- Demande de convention de stage
- Justification d'absence
- Demande de rattrapage
- Réclamation
- Demande d'information sur les bourses
- Demande de rendez-vous

Format de réponse:
OBJET: [objet de l'email]

[corps de l'email]"""

    def generate_email(
        self,
        request_type: str,
        user_details: Optional[Dict] = None,
        additional_info: str = ""
    ) -> Dict:
        """
        Generate an administrative email.

        Args:
            request_type: Type of request (e.g., "attestation de scolarité")
            user_details: Optional student information (name, student_id, etc.)
            additional_info: Additional context or requirements

        Returns:
            Dictionary with email subject and body
        """
        # Build prompt
        user_info = ""
        if user_details:
            for key, value in user_details.items():
                user_info += f"{key}: {value}\n"

        prompt = f"""Type de demande: {request_type}

Informations de l'étudiant:
{user_info}

Informations supplémentaires:
{additional_info}

Génère un email administratif professionnel pour cette demande."""

        response = self.openai_client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )

        email_text = response.choices[0].message.content

        # Parse subject and body
        subject, body = self._parse_email(email_text)

        return {
            "subject": subject,
            "body": body,
            "full_text": email_text
        }

    def _parse_email(self, email_text: str) -> tuple[str, str]:
        """Parse subject and body from generated email."""
        lines = email_text.split('\n')

        subject = "Demande administrative"
        body_lines = []

        found_subject = False
        for line in lines:
            if line.upper().startswith("OBJET:"):
                subject = line.split(":", 1)[1].strip()
                found_subject = True
            elif found_subject or not line.upper().startswith("OBJET"):
                body_lines.append(line)

        body = '\n'.join(body_lines).strip()

        return subject, body

    def get_request_types(self) -> List[str]:
        """Get list of common request types."""
        return [
            "Attestation de scolarité",
            "Certificat de réussite",
            "Convention de stage",
            "Justification d'absence",
            "Demande de rattrapage",
            "Réclamation",
            "Demande de bourse",
            "Rendez-vous administration",
            "Transfert de dossier",
            "Attestation d'inscription"
        ]
