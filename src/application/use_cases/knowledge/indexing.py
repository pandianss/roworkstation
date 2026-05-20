from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.core.paths import project_path
from src.domain.schemas.knowledge import IndexedDocument


class _FallbackEmbedder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), float(sum(map(ord, text[:32])) % 997)] for text in texts]


def get_embedder():
    """Return a lightweight local embedder.

    Production deployments can monkey-patch or replace this with a sentence
    transformer. The fallback keeps offline tests and basic indexing usable.
    """
    return _FallbackEmbedder()


class _MemoryCollection:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def upsert(self, *, ids: list[str], documents: list[str], metadatas: list[dict], embeddings: list[list[float]]) -> None:
        self.items.extend(
            {"id": doc_id, "content": doc, "metadata": meta, "embedding": embedding}
            for doc_id, doc, meta, embedding in zip(ids, documents, metadatas, embeddings)
        )


class _MemoryClient:
    def __init__(self) -> None:
        self.collection = _MemoryCollection()

    def get_or_create_collection(self, name: str) -> _MemoryCollection:
        return self.collection


class KnowledgeRegistry:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or project_path("data", "knowledge_index.json")

    def list(self) -> list[IndexedDocument]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        return [IndexedDocument.model_validate(item) for item in data]

    def add(self, record: IndexedDocument) -> None:
        records = self.list()
        records.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([item.model_dump(mode="json") for item in records], indent=2),
            encoding="utf-8",
        )


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 120) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += max(1, chunk_size - overlap)
    return chunks


class KnowledgeIndexingService:
    def __init__(self, client: object | None = None) -> None:
        self.knowledge_dir = project_path("data", "knowledge_docs")
        self.registry = KnowledgeRegistry()
        self.client = client or _MemoryClient()

    def index_saved_document(self, source: Path, department: str, uploaded_by: str) -> IndexedDocument:
        text = source.read_text(encoding="utf-8", errors="ignore")
        chunks = _chunk_text(text)
        embeddings = get_embedder().encode(chunks)
        metadata = [{"title": source.name, "department": department, "uploaded_by": uploaded_by} for _ in chunks]
        ids = [f"{source.stem}-{index}" for index in range(len(chunks))]

        collection = self.client.get_or_create_collection("ro_knowledge")
        collection.upsert(ids=ids, documents=chunks, metadatas=metadata, embeddings=embeddings)

        record = IndexedDocument(
            file_name=source.name,
            department=department,
            uploaded_by=uploaded_by,
            chunks=len(chunks),
            indexed_at=datetime.now(),
        )
        self.registry.add(record)
        return record

    def list_documents(self) -> list[IndexedDocument]:
        return self.registry.list()
