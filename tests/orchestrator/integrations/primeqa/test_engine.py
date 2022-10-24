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

import grpc

from orchestrator.constants import PARAMETER
from orchestrator.exceptions import Error, ErrorMessages
from orchestrator.integrations.primeqa.engine import (
    build_grpc_parameters,
    connect_primeqa_service,
    get_readers,
    get_answers,
    get_indexes,
    get_retrievers,
    retrieve,
)


class TestPrimeQAIntegration:
    @pytest.fixture()
    def mock_grpc_connection_error(self) -> Exception:
        grpc_error = grpc.RpcError()
        grpc_error.code = lambda: grpc.StatusCode.UNAVAILABLE
        return grpc_error

    @pytest.fixture()
    def mock_grpc_unknown_error(self) -> Exception:
        grpc_error = grpc.RpcError()
        grpc_error.code = lambda: grpc.StatusCode.UNKNOWN
        return grpc_error

    @pytest.fixture()
    def mock_grpc_invalid_argument_error(self) -> Exception:
        grpc_error = grpc.RpcError()
        grpc_error.code = lambda: grpc.StatusCode.INVALID_ARGUMENT
        return grpc_error

    @pytest.fixture()
    def mock_RETRIEVER_STUB(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.integrations.primeqa.engine.RETRIEVER_STUB",
        )

    @pytest.fixture()
    def mock_INDEXER_STUB(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.integrations.primeqa.engine.INDEXER_STUB",
        )

    @pytest.fixture()
    def mock_READER_STUB(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.integrations.primeqa.engine.READER_STUB",
        )

    def test_build_grpc_parameters(self):
        parameters = [
            {
                PARAMETER.ATTR_ID.value: "string parameter",
                PARAMETER.ATTR_TYPE.value: "String",
                PARAMETER.ATTR_VALUE.value: "test string",
            },
            {
                PARAMETER.ATTR_ID.value: "numeric int parameter",
                PARAMETER.ATTR_TYPE.value: "Numeric",
                PARAMETER.ATTR_VALUE.value: 10,
            },
            {
                PARAMETER.ATTR_ID.value: "numeric float parameter",
                PARAMETER.ATTR_TYPE.value: "Numeric",
                PARAMETER.ATTR_VALUE.value: 5.0,
            },
            {
                PARAMETER.ATTR_ID.value: "bool parameter",
                PARAMETER.ATTR_TYPE.value: "Boolean",
                PARAMETER.ATTR_VALUE.value: True,
            },
            {
                PARAMETER.ATTR_ID.value: "unknow parameter",
                PARAMETER.ATTR_TYPE.value: "unknown",
                PARAMETER.ATTR_VALUE.value: "unknow",
            },
        ]

        grpc_parameters = build_grpc_parameters(parameters)
        assert len(grpc_parameters) == 4
        for idx, grpc_parameter in enumerate(grpc_parameters):
            assert parameters[idx][PARAMETER.ATTR_TYPE.value] == grpc_parameter.type

    def test_connect_primeqa_service(self, mocker):
        mock_grpc_insecure_channel = mocker.patch(
            "orchestrator.integrations.primeqa.engine.grpc.insecure_channel",
            autospec=True,
        )
        mock_RetrieverStub = mocker.patch(
            "orchestrator.integrations.primeqa.engine.RetrieverStub", autospec=True
        )
        mock_ReaderStub = mocker.patch(
            "orchestrator.integrations.primeqa.engine.ReaderStub", autospec=True
        )
        mock_IndexerStub = mocker.patch(
            "orchestrator.integrations.primeqa.engine.IndexerStub", autospec=True
        )
        connect_primeqa_service(endpoint="test endpoint")
        mock_grpc_insecure_channel.assert_called_once_with("test endpoint")
        mock_RetrieverStub.assert_called_once()
        mock_ReaderStub.assert_called_once()
        mock_IndexerStub.assert_called_once()

    def test_get_readers(self, mock_READER_STUB):
        get_readers()
        mock_READER_STUB.GetReaders.assert_called_once()

    def test_get_readers_with_connection_error(
        self, mock_READER_STUB, mock_grpc_connection_error
    ):
        mock_READER_STUB.GetReaders.side_effect = mock_grpc_connection_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_CONNECTION_ERROR.value):
            get_readers()
            mock_READER_STUB.GetReaders.assert_called_once()

    def test_get_readers_with_unknown_error(
        self, mock_READER_STUB, mock_grpc_unknown_error
    ):
        mock_READER_STUB.GetReaders.side_effect = mock_grpc_unknown_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value):
            get_readers()
            mock_READER_STUB.GetReaders.assert_called_once()

    def test_get_answers(self, mock_READER_STUB):
        get_answers(
            reader={"reader_id": "test reader"},
            query="test query",
            documents=[{"text": "test document"}],
        )
        mock_READER_STUB.GetAnswers.assert_called_once()

    def test_get_answers_with_connection_error(
        self, mock_READER_STUB, mock_grpc_connection_error
    ):
        mock_READER_STUB.GetAnswers.side_effect = mock_grpc_connection_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_CONNECTION_ERROR.value):
            get_answers(
                reader={"reader_id": "test reader"},
                query="test query",
                documents=[{"text": "test document"}],
            )
            mock_READER_STUB.GetAnswers.assert_called_once()

    def test_get_answers_with_invalid_argument_error(
        self, mock_READER_STUB, mock_grpc_invalid_argument_error
    ):
        mock_READER_STUB.GetAnswers.side_effect = mock_grpc_invalid_argument_error
        with pytest.raises(
            Error, match=ErrorMessages.PRIMEQA_INVALID_ARGUMENT_ERROR.value
        ):
            get_answers(
                reader={"reader_id": "test reader"},
                query="test query",
                documents=[{"text": "test document"}],
            )
            mock_READER_STUB.GetAnswers.assert_called_once()

    def test_get_answers_with_unknown_error(
        self, mock_READER_STUB, mock_grpc_unknown_error
    ):
        mock_READER_STUB.GetAnswers.side_effect = mock_grpc_unknown_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value):
            get_answers(
                reader={"reader_id": "test reader"},
                query="test query",
                documents=[{"text": "test document"}],
            )
            mock_READER_STUB.GetAnswers.assert_called_once()

    def test_get_retrievers(self, mock_RETRIEVER_STUB):
        get_retrievers()
        mock_RETRIEVER_STUB.GetRetrievers.assert_called_once()

    def test_get_retrievers_with_connection_error(
        self, mock_RETRIEVER_STUB, mock_grpc_connection_error
    ):
        mock_RETRIEVER_STUB.GetRetrievers.side_effect = mock_grpc_connection_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_CONNECTION_ERROR.value):
            get_retrievers()
            mock_RETRIEVER_STUB.GetRetrievers.assert_called_once()

    def test_get_retrievers_with_unknown_error(
        self, mock_RETRIEVER_STUB, mock_grpc_unknown_error
    ):
        mock_RETRIEVER_STUB.GetRetrievers.side_effect = mock_grpc_unknown_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value):
            get_retrievers()
            mock_RETRIEVER_STUB.GetRetrievers.assert_called_once()

    def test_retrieve(self, mock_RETRIEVER_STUB):
        retrieve(
            retriever={"retriever_id": "test retriever"},
            index_id="test indexe id",
            query="test query",
        )
        mock_RETRIEVER_STUB.Retrieve.assert_called_once()

    def test_retrieve_with_connection_error(
        self, mock_RETRIEVER_STUB, mock_grpc_connection_error
    ):
        mock_RETRIEVER_STUB.Retrieve.side_effect = mock_grpc_connection_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_CONNECTION_ERROR.value):
            retrieve(
                retriever={"retriever_id": "test retriever"},
                index_id="test indexe id",
                query="test query",
            )
            mock_RETRIEVER_STUB.Retrieve.assert_called_once()

    def test_retrieve_with_invalid_argument_error(
        self, mock_RETRIEVER_STUB, mock_grpc_invalid_argument_error
    ):
        mock_RETRIEVER_STUB.Retrieve.side_effect = mock_grpc_invalid_argument_error
        with pytest.raises(
            Error, match=ErrorMessages.PRIMEQA_INVALID_ARGUMENT_ERROR.value
        ):
            retrieve(
                retriever={"retriever_id": "test retriever"},
                index_id="test indexe id",
                query="test query",
            )
            mock_RETRIEVER_STUB.Retrieve.assert_called_once()

    def test_retrieve_with_unknown_error(
        self, mock_RETRIEVER_STUB, mock_grpc_unknown_error
    ):
        mock_RETRIEVER_STUB.Retrieve.side_effect = mock_grpc_unknown_error
        with pytest.raises(Error, match=ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value):
            retrieve(
                retriever={"retriever_id": "test retriever"},
                index_id="test indexe id",
                query="test query",
            )
            mock_RETRIEVER_STUB.Retrieve.assert_called_once()

    def test_get_indexes(self):
        assert not get_indexes(retriever_id="test retriever")
