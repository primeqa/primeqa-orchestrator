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

from orchestrator.readers.primeqa import get_primeqa_readers, get_answers
from orchestrator.exceptions import Error, ErrorMessages


class TestPrimeQAReaders:
    @pytest.fixture()
    def mock_connect_primeqa_service(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.readers.primeqa.connect_primeqa_service",
            autospec=True,
        )

    @pytest.fixture()
    def mock_primeqa_get_readers_rpc(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.readers.primeqa.get_readers_rpc",
            return_value=[],
            autospec=True,
        )

    @pytest.fixture()
    def mock_primeqa_get_answers_rpc(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.readers.primeqa.get_answers_rpc",
            return_value=[],
            autospec=True,
        )

    @pytest.fixture(scope="class", autouse=True)
    def mock_settings(self) -> dict:
        return {"service_endpoint": "", "beta": 0.7}

    def test_get_primeqa_readers(
        self,
        mock_settings,
        mock_connect_primeqa_service,
        mock_primeqa_get_readers_rpc,
    ):
        get_primeqa_readers(settings=mock_settings)
        mock_connect_primeqa_service.assert_called_once_with("")
        mock_primeqa_get_readers_rpc.assert_called_once()

    def test_get_primeqa_readers_with_missing_service_endpoint(
        self,
    ):
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT):
            get_primeqa_readers(settings={})

    def test_get_answers_with_missing_service_endpoint(
        self,
    ):
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT):
            get_answers(
                reader={"reader_id": "test reader"},
                query="test",
                contexts=[["test context 1", "test context 2"]],
                settings={},
            )

    def test_get_answers(
        self,
        mock_settings,
        mock_connect_primeqa_service,
        mock_primeqa_get_answers_rpc,
    ):
        get_answers(
            reader={"reader_id": "test reader"},
            query="test query",
            contexts=[["test context 1", "test context 2"]],
            settings=mock_settings,
        )
        mock_connect_primeqa_service.assert_called_once_with("")
        mock_primeqa_get_answers_rpc.assert_called_once_with(
            {"reader_id": "test reader"},
            "test query",
            [["test context 1", "test context 2"]],
        )
