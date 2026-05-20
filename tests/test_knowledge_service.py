import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.application.use_cases.knowledge.indexing import KnowledgeIndexingService
from src.core.paths import project_path


class KnowledgeIndexingTests(unittest.TestCase):
    def setUp(self):
        self.temp_path = project_path("data", "test_runtime", f"ro_ws_knowledge_{uuid4().hex}")
        self.temp_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        return None

    def test_index_saved_document_registers_chunks(self):
        service = KnowledgeIndexingService()
        service.knowledge_dir = self.temp_path / "knowledge_docs"
        service.knowledge_dir.mkdir(parents=True, exist_ok=True)
        service.registry.path = self.temp_path / "knowledge_index.json"
        source = service.knowledge_dir / "policy.txt"
        source.write_text("Policy text " * 300, encoding="utf-8")

        fake_collection = MagicMock()
        fake_client = MagicMock()
        fake_client.get_or_create_collection.return_value = fake_collection
        service.client = fake_client

        with patch("src.application.use_cases.knowledge.indexing.get_embedder") as mock_embedder:
            mock_embedder.return_value.encode.return_value = [[0.0] * 4] * 3
            record = service.index_saved_document(source, "CRMD", "tester")

        self.assertEqual(record.department, "CRMD")
        self.assertGreater(record.chunks, 1)
        fake_collection.upsert.assert_called_once()

    def test_list_documents_returns_empty_collection_when_uninitialized(self):
        service = KnowledgeIndexingService()
        service.registry.path = self.temp_path / "knowledge_index.json"
        self.assertEqual(service.list_documents(), [])
