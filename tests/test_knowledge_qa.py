import unittest
from unittest.mock import patch

from src.application.use_cases.knowledge.qa import KnowledgeQaService


class KnowledgeQaTests(unittest.TestCase):
    def test_answer_question_passes_department_filter_to_search(self):
        service = KnowledgeQaService()
        with patch.object(service.search_service, "search", return_value=[]) as mock_search:
            with patch.object(service.llm, "generate", return_value="No documents found."):
                service.answer_question("What is the rule?", dept_filter="CRMD")
        mock_search.assert_called_once_with("What is the rule?", n_results=5, dept_filter="CRMD")

    def test_answer_question_returns_source_metadata(self):
        chunks = [
            {"content": "Policy text", "metadata": {"title": "Circular 1", "department": "CRMD"}},
            {"content": "Second policy text", "metadata": {"title": "Circular 2", "department": "CRMD"}},
        ]
        service = KnowledgeQaService()
        with patch.object(service.search_service, "search", return_value=chunks):
            with patch.object(service.llm, "generate", return_value="Answer with [1] and [2]."):
                result = service.answer_question("Summarize", dept_filter="CRMD")
        self.assertEqual(result["sources"], [chunk["metadata"] for chunk in chunks])
        self.assertIn("[1]", result["answer"])
