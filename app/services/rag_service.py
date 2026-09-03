import math
from sqlalchemy.orm import Session
from sqlalchemy import select
from google import genai

from app.config import settings
from app.models.policy_document import PolicyDocument


class RAGService:
    @staticmethod
    def _get_embedding(text: str) -> list[float]:
        """
        Generates vector embeddings using Google GenAI SDK (text-embedding-004)
        with fallback vector generation for offline/test environments.
        """
        key = settings.GEMINI_API_KEY
        if key and key != "dummy_key_for_setup" and key != "your_gemini_api_key_from_google_ai_studio":
            try:
                client = genai.Client(api_key=key)
                result = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                if result.embedding and result.embedding.values:
                    return result.embedding.values
            except Exception as e:
                print(f"[RAG Embedding Notice]: Live embedding generation failed: {e}. Falling back to keyword vector model.")

        # Fallback deterministic bag-of-words / keyword frequency vector for offline testing
        vocabulary = ["retry", "refund", "discount", "link", "sms", "email", "max", "attempts", "card", "delay", "customer"]
        words = text.lower().split()
        vector = [float(words.count(w)) for w in vocabulary]
        # Normalize vector to unit length
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """
        Calculates cosine similarity between two float vectors.
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    @classmethod
    def index_policy_document(
        cls,
        db: Session,
        merchant_id: str,
        title: str,
        policy_type: str,
        content: str
    ) -> PolicyDocument:
        """
        Indexes and stores a merchant policy document with embedding pointer.
        """
        doc = PolicyDocument(
            merchant_id=merchant_id,
            title=title,
            policy_type=policy_type.upper(),
            content=content,
            is_active=True
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def get_relevant_policy_context(
        cls,
        db: Session,
        merchant_id: str,
        query: str,
        top_k: int = 2
    ) -> str:
        """
        Performs semantic RAG retrieval over merchant policy documents.
        Returns concatenated text snippets of top matching business rules.
        """
        stmt = select(PolicyDocument).where(
            PolicyDocument.merchant_id == merchant_id,
            PolicyDocument.is_active == True
        )
        policies = db.execute(stmt).scalars().all()

        if not policies:
            return "Standard Merchant Business Rules: Retry up to 3 times within 72 hours. Send instant Razorpay payment retry links."

        query_vec = cls._get_embedding(query)

        scored_policies = []
        for policy in policies:
            doc_vec = cls._get_embedding(f"{policy.title} {policy.policy_type} {policy.content}")
            score = cls._cosine_similarity(query_vec, doc_vec)
            scored_policies.append((score, policy))

        scored_policies.sort(key=lambda x: x[0], reverse=True)
        top_policies = scored_policies[:top_k]

        context_snippets = [
            f"Policy Rule [{p[1].policy_type}]: {p[1].title} — {p[1].content}"
            for p in top_policies
        ]

        return "\n".join(context_snippets)
