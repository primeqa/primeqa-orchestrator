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

from orchestrator.retrievers.primeqa import (
    get_primeqa_retrievers,
    get_collections_for_primeqa_retriever,
    retrieve_for_primeqa_retrievers,
)
from orchestrator.exceptions import Error, ErrorMessages


class TestPrimeQARetrievers:
    @pytest.fixture()
    def mock_connect_primeqa_service(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.primeqa.connect_primeqa_service",
            autospec=True,
        )

    @pytest.fixture()
    def mock_primeqa_get_retrievers_rpc(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.primeqa.get_retrievers_rpc",
            return_value=[],
            autospec=True,
        )

    @pytest.fixture()
    def mock_primeqa_retrieve_rpc(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.primeqa.retrieve_rpc",
            return_value=[],
            autospec=True,
        )

    @pytest.fixture()
    def mock_primeqa_get_indexes_rpc(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.primeqa.get_indexes_rpc",
            return_value=[],
            autospec=True,
        )

    @pytest.fixture(autouse=True)
    def mock_settings(self) -> dict:
        return {"service_endpoint": "", "beta": 0.7}

    def test_get_primeqa_retrievers(
        self,
        mock_settings,
        mock_connect_primeqa_service,
        mock_primeqa_get_retrievers_rpc,
    ):
        get_primeqa_retrievers(settings=mock_settings)
        mock_connect_primeqa_service.assert_called_once_with("")
        mock_primeqa_get_retrievers_rpc.assert_called_once()

    def test_get_primeqa_retrievers_with_missing_service_endpoint(
        self,
    ):
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT):
            get_primeqa_retrievers(settings={})

    def test_get_collections_for_primeqa_retriever_with_missing_service_endpoint(self):
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT):
            get_collections_for_primeqa_retriever(
                retriever_id="test retriever", settings={}
            )

    def test_get_collections_for_primeqa_retriever(
        self,
        mock_settings,
        mock_connect_primeqa_service,
        mock_primeqa_get_indexes_rpc,
    ):
        get_collections_for_primeqa_retriever(
            retriever_id="test retriever", settings=mock_settings
        )
        mock_connect_primeqa_service.assert_called_once_with("")
        mock_primeqa_get_indexes_rpc.assert_called_once_with("test retriever")

    def test_retrieve_for_primeqa_retrievers_with_missing_service_endpoint(
        self,
    ):
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT):
            retrieve_for_primeqa_retrievers(
                query="test query",
                retriever={"retriever_id": "test retriever"},
                collection_id="test collection",
                settings={},
            )

    def test_retrieve_for_primeqa_retrievers(
        self,
        mock_settings,
        mock_connect_primeqa_service,
        mock_primeqa_retrieve_rpc,
    ):
        retrieve_for_primeqa_retrievers(
            query="test query",
            retriever={"retriever_id": "test retriever"},
            collection_id="test collection",
            settings=mock_settings,
        )
        mock_connect_primeqa_service.assert_called_once_with("")
        mock_primeqa_retrieve_rpc.assert_called_once_with(
            retriever={"retriever_id": "test retriever"},
            index_id="test collection",
            query="test query",
        )
