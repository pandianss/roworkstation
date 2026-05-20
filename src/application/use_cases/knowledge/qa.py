from __future__ import annotations

from src.application.use_cases.knowledge.search import KnowledgeSearchService


class _OfflineLLM:
    def generate(self, prompt: str) -> str:
        return "No documents found."


class KnowledgeQaService:
    def __init__(self, search_service: KnowledgeSearchService | None = None, llm: object | None = None) -> None:
        self.search_service = search_service or KnowledgeSearchService()
        self.llm = llm or _OfflineLLM()

    def answer_question(self, question: str, dept_filter: str | None = None) -> dict:
        chunks = self.search_service.search(question, n_results=5, dept_filter=dept_filter)
        if not chunks:
            return {"answer": self.llm.generate(question), "sources": []}

        context = "\n\n".join(f"[{index}] {chunk['content']}" for index, chunk in enumerate(chunks, start=1))
        answer = self.llm.generate(f"Answer using these sources:\n{context}\n\nQuestion: {question}")
        return {"answer": answer, "sources": [chunk["metadata"] for chunk in chunks]}
