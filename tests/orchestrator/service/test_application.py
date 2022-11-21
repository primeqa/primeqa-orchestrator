#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 PrimeQA Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from orchestrator.service.application import app
from orchestrator.constants import FEEDBACK


class TestApplication:
    @pytest.fixture()
    def client(self):
        return TestClient(app)

    @pytest.fixture()
    def mock_STORE(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.service.application.STORE",
            autospec=True,
        )

    def test_get_settings(self, client, mock_STORE):
        mock_settings = {"retrievers": {}, "readers": {"PrimeQA": {}}}
        mock_STORE.get_settings.return_value = mock_settings
        response = client.get("/settings")
        assert response.status_code == 200
        assert response.json() == mock_settings

    def test_update_settings(self, client, mock_STORE):
        mock_settings_update = {
            "readers": {"PrimeQA": {"service_endpoint": "test endpoint"}}
        }
        response = client.patch("/settings", json=mock_settings_update)
        assert response.status_code == 200
        mock_STORE.update_settings.assert_called_once_with(mock_settings_update)

    def test_get_retrievers(self, client, mock_STORE):
        mock_STORE.get_settings.return_value = {"retrievers": {}}
        response = client.get("/retrievers")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_retriever_collections_with_invalid_retriever_id(self, client):
        response = client.get("/retrievers/random/collections")
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E6001",
                "message": "random retriever does not exists. Please make sure you are selecting one of the available retrievers.",
            }
        }

    def test_get_retriever_collections(self, client, mocker):
        mock_fetch_collections = mocker.patch(
            "orchestrator.service.application.fetch_collections", return_value=[]
        )
        response = client.get("/retrievers/random/collections")
        mock_fetch_collections.assert_called_once_with("random")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_documents_for_question_with_no_results(self, client, mocker):
        mock_retrieve = mocker.patch(
            "orchestrator.service.application.retrieve", return_value=[]
        )
        response = client.post(
            "/GetDocumentsRequest",
            json={
                "question": "test question",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
            },
        )
        mock_retrieve.assert_called_once_with(
            query="test question",
            retriever_id="test retriever",
            collection_id="test collection",
            parameters_with_updates=None,
        )
        assert response.status_code == 201
        assert response.json() == []

    def test_get_documents_for_question(self, client, mocker):
        mock_retrieve = mocker.patch(
            "orchestrator.service.application.retrieve",
            return_value=[
                {"text": "test document text", "score": 0.5, "confidence": 1.0}
            ],
        )
        response = client.post(
            "/GetDocumentsRequest",
            json={
                "question": "test question",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
            },
        )
        mock_retrieve.assert_called_once_with(
            query="test question",
            retriever_id="test retriever",
            collection_id="test collection",
            parameters_with_updates=None,
        )
        assert response.status_code == 201
        assert response.json() == [
            {
                "text": "test document text",
                "confidence": 1.0,
                "score": 0.5,
                "document_id": None,
                "title": None,
                "url": None,
            }
        ]

    def test_get_documents_for_question_with_empty_question(self, client):
        response = client.post(
            "/GetDocumentsRequest",
            json={
                "question": "",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
            },
        )
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E1001",
                "message": 'Invalid Request. "query" cannot be empty.',
            }
        }

    def test_get_documents_for_question_with_invalid_retriever(self, client, mocker):
        mock_StoreFactory = mocker.patch(
            "orchestrator.retrievers.StoreFactory",
            return_value={"retrievers": {}},
            autospec=True,
        )
        mock_StoreFactory.get_store().get_settings.return_value = {"retrievers": {}}
        response = client.post(
            "/GetDocumentsRequest",
            json={
                "question": "test question",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
            },
        )
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E6001",
                "message": "test retriever retriever does not exists. Please make sure you are selecting one of the available retrievers.",
            }
        }

    def test_get_readers(self, client, mock_STORE):
        mock_STORE.get_settings.return_value = {"readers": {}}
        response = client.get("/readers")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_readers_with_missing_service_endpoint(self, client, mock_STORE):
        mock_STORE.get_settings.return_value = {
            "readers": {"PrimeQA": {"service_endpoint": ""}}
        }
        response = client.get("/readers")
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E5001",
                "message": "Missing primeqa service endpoint in settings.",
            }
        }

    def test_get_answers_for_contexts_with_empty_question(self, client):
        response = client.post(
            "/GetAnswersRequest",
            json={
                "question": "",
                "contexts": ["test context"],
                "reader": {"reader_id": "test reader"},
            },
        )
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E1001",
                "message": 'Invalid Request. "query" cannot be empty.',
            }
        }

    def test_get_answers_for_contexts_with_invalid_reader(self, client, mocker):
        mock_StoreFactory = mocker.patch(
            "orchestrator.readers.StoreFactory",
            return_value={"retrievers": {}},
            autospec=True,
        )
        mock_StoreFactory.get_store().get_settings.return_value = {"readers": {}}
        response = client.post(
            "/GetAnswersRequest",
            json={
                "question": "test question",
                "contexts": ["test context"],
                "reader": {"reader_id": "test reader"},
            },
        )
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E7001",
                "message": "test reader reader does not exists. Please make sure you are selecting one of the available readers.",
            }
        }

    def test_get_answers_for_contexts(self, client, mocker):
        mock_read = mocker.patch(
            "orchestrator.service.application.read",
            return_value=[
                {
                    "text": "test answer text",
                    "confidence": 1.0,
                    "start_char_offset": 0,
                    "end_char_offset": 1,
                    "context_index": 0,
                }
            ],
        )
        response = client.post(
            "/GetAnswersRequest",
            json={
                "question": "test question",
                "contexts": ["test context"],
                "reader": {"reader_id": "test reader"},
            },
        )
        mock_read.assert_called_once_with(
            query="test question",
            reader_id="test reader",
            contexts=[{"text": "test context", "confidence": 1.0}],
            parameters_with_updates=None,
        )
        assert response.status_code == 201
        assert response.json() == [
            {
                "text": "test answer text",
                "confidence_score": 1.0,
                "start_char_offset": 0,
                "end_char_offset": 1,
                "context_index": 0,
            }
        ]

    def test_get_answers_for_contexts_with_no_answers(self, client, mocker):
        mock_read = mocker.patch(
            "orchestrator.service.application.read",
            return_value=[],
        )
        response = client.post(
            "/GetAnswersRequest",
            json={
                "question": "test question",
                "contexts": ["test context"],
                "reader": {"reader_id": "test reader"},
            },
        )
        mock_read.assert_called_once_with(
            query="test question",
            reader_id="test reader",
            contexts=[{"text": "test context", "confidence": 1.0}],
            parameters_with_updates=None,
        )
        assert response.status_code == 201
        assert response.json() == []

    def test_ask_with_empty_question(self, client):
        response = client.post(
            "/ask",
            json={
                "question": "",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
                "reader": {"reader_id": "test reader"},
            },
        )
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E1001",
                "message": 'Invalid Request. "query" cannot be empty.',
            }
        }

    def test_ask_with_invalid_retriever(self, client, mocker):
        mock_StoreFactory = mocker.patch(
            "orchestrator.retrievers.StoreFactory",
            return_value={"retrievers": {}},
            autospec=True,
        )
        mock_StoreFactory.get_store().get_settings.return_value = {"retrievers": {}}
        response = client.post(
            "/ask",
            json={
                "question": "test question",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
                "reader": {"reader_id": "test reader"},
            },
        )
        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "code": "E6001",
                "message": "test retriever retriever does not exists. Please make sure you are selecting one of the available retrievers.",
            }
        }

    def test_ask_with_no_answers(self, client, mocker):
        mock_retrieve = mocker.patch(
            "orchestrator.service.application.retrieve",
            return_value=[
                {"text": "test document text", "score": 0.5, "confidence": 1.0}
            ],
        )
        mock_read = mocker.patch(
            "orchestrator.service.application.read",
            return_value=[],
        )
        response = client.post(
            "/ask",
            json={
                "question": "test question",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
                "reader": {"reader_id": "test reader"},
            },
        )
        mock_retrieve.assert_called_once_with(
            query="test question",
            retriever_id="test retriever",
            collection_id="test collection",
            parameters_with_updates=None,
        )
        mock_read.assert_called_once_with(
            query="test question",
            reader_id="test reader",
            contexts=[{"text": "test document text", "score": 0.5, "confidence": 1.0}],
            parameters_with_updates=None,
        )
        assert response.status_code == 201
        assert response.json() == []

    def test_ask(self, client, mocker):
        mock_retrieve = mocker.patch(
            "orchestrator.service.application.retrieve",
            return_value=[
                {"text": "test document text", "score": 0.5, "confidence": 1.0}
            ],
        )
        mock_read = mocker.patch(
            "orchestrator.service.application.read",
            return_value=[
                {
                    "text": "test answer text",
                    "confidence": 1.0,
                    "start_char_offset": 0,
                    "end_char_offset": 1,
                    "context_index": 0,
                }
            ],
        )
        response = client.post(
            "/ask",
            json={
                "question": "test question",
                "retriever": {"retriever_id": "test retriever"},
                "collection": {"collection_id": "test collection"},
                "reader": {"reader_id": "test reader"},
            },
        )
        mock_retrieve.assert_called_once_with(
            query="test question",
            retriever_id="test retriever",
            collection_id="test collection",
            parameters_with_updates=None,
        )
        mock_read.assert_called_once_with(
            query="test question",
            reader_id="test reader",
            contexts=[{"text": "test document text", "score": 0.5, "confidence": 1.0}],
            parameters_with_updates=None,
        )
        assert response.status_code == 201
        assert response.json() == [
            {
                "answer": {
                    "text": "test answer text",
                    "confidence_score": 1.0,
                    "start_char_offset": 0,
                    "end_char_offset": 1,
                    "context_index": 0,
                },
                "document": {
                    "text": "test document text",
                    "score": 0.5,
                    "confidence": 1.0,
                    "document_id": None,
                    "title": None,
                    "url": None,
                },
            }
        ]

    def test_get_feedback(self, client, mock_STORE):
        mock_STORE.get_feedbacks.return_value = []
        response = client.get("/feedbacks")
        mock_STORE.get_feedbacks.assert_called_once()
        assert response.status_code == 200
        assert response.json() == []

    def test_post_feedback(self, client, mock_STORE):
        mock_feedback = {
            FEEDBACK.FEEDBACK_ID.value: "test feedback id",
            FEEDBACK.USER_ID.value: "test user id",
            FEEDBACK.QUESTION.value: "test question",
            FEEDBACK.ANSWER.value: "test answer",
            FEEDBACK.THUMBS_UP: True,
            FEEDBACK.THUMBS_DOWN: False,
        }
        mock_STORE.get_feedbacks.return_value = [mock_feedback]
        response = client.post(
            "/feedbacks",
            json=mock_feedback,
        )
        mock_STORE.save_feedback.assert_called_once()
        assert response.status_code == 201
