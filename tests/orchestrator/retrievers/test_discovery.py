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

from orchestrator.constants import GENERIC, WATSON_DISCOVERY
from orchestrator.retrievers.discovery import (
    get_discovery_retrievers,
    get_collections_for_discovery_retriever,
    retrieve_for_discovery_retrievers,
)
from orchestrator.exceptions import Error, ErrorMessages


class TestDiscoveryRetriever:
    @pytest.fixture()
    def mock_connect_cp4d_discovery_service_instance(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.discovery.connect_cp4d_discovery_service_instance",
            autospec=True,
        )

    @pytest.fixture()
    def mock_connect_cloud_discovery_service_instance(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.discovery.connect_cloud_discovery_service_instance",
            autospec=True,
        )

    @pytest.fixture()
    def mock_discovery_get_discovery_collections(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.discovery.get_discovery_collections",
            return_value=[],
            autospec=True,
        )

    @pytest.fixture()
    def mock_discovery_retrieve(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.retrievers.discovery.retrieve",
            return_value=[],
            autospec=True,
        )

    @pytest.fixture(autouse=True)
    def mock_cp4d_discovery_service_instance_settings(self) -> dict:
        return {
            GENERIC.ATTR_SERVICE_ENDPOINT.value: "https://cpd-test/discovery/instance",
            GENERIC.ATTR_SERVICE_TOKEN.value: "",
            WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value: "Test Project ID",
        }

    @pytest.fixture(autouse=True)
    def mock_cloud_discovery_service_instance_settings(self) -> dict:
        return {
            GENERIC.ATTR_SERVICE_ENDPOINT.value: "https://api.us-south.discovery.watson.cloud.ibm.com/instances/",
            GENERIC.ATTR_SERVICE_API_KEY.value: "",
            WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value: "Test Project ID",
        }

    @pytest.fixture(autouse=True)
    def mock_unsupported_discovery_service_instance_settings(self) -> dict:
        return {
            GENERIC.ATTR_SERVICE_ENDPOINT.value: "https://random.com",
        }

    def test_get_discovery_retrievers(self):
        retrievers = get_discovery_retrievers()
        assert retrievers[0]["retriever_id"] == "WatsonDiscovery"

    def test_get_collections_for_discovery_retriever_with_missing_service_endpoint(
        self,
    ):
        with pytest.raises(
            Error, match=ErrorMessages.DISCOVERY_MISSING_SERVICE_ENDPOINT.value.strip()
        ):
            get_collections_for_discovery_retriever(settings={})

    def test_get_collections_for_discovery_retriever_for_unsupported_discovery_service_instance(
        self, mock_unsupported_discovery_service_instance_settings
    ):
        with pytest.raises(
            Error,
            match=ErrorMessages.DISCOVERY_UNSUPPORTED_CONNECTION_TYPE.value.strip(),
        ):
            get_collections_for_discovery_retriever(
                settings=mock_unsupported_discovery_service_instance_settings
            )

    def test_get_collections_for_discovery_retriever_for_cloud_discovery_service_instance_with_missing_credentials(
        self,
        mock_cloud_discovery_service_instance_settings,
    ):
        with pytest.raises(
            Error,
            match=ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip(),
        ):
            get_collections_for_discovery_retriever(
                settings=mock_cloud_discovery_service_instance_settings
            )

    def test_get_collections_for_discovery_retriever_for_cloud_discovery_service_instance(
        self,
        mock_cloud_discovery_service_instance_settings,
        mock_connect_cloud_discovery_service_instance,
        mock_discovery_get_discovery_collections,
    ):
        mock_cloud_discovery_service_instance_settings[
            GENERIC.ATTR_SERVICE_API_KEY.value
        ] = "Test API Key"
        get_collections_for_discovery_retriever(
            settings=mock_cloud_discovery_service_instance_settings
        )
        mock_connect_cloud_discovery_service_instance.assert_called_once_with(
            "https://api.us-south.discovery.watson.cloud.ibm.com/instances/",
            "Test API Key",
        )
        mock_discovery_get_discovery_collections.assert_called_once_with(
            "Test Project ID"
        )

    def test_get_collections_for_discovery_retriever_for_cp4d_discovery_service_instance_with_missing_credentials(
        self,
        mock_cp4d_discovery_service_instance_settings,
    ):
        with pytest.raises(
            Error,
            match=ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip(),
        ):
            get_collections_for_discovery_retriever(
                settings=mock_cp4d_discovery_service_instance_settings
            )

    def test_get_collections_for_discovery_retriever_for_cp4d_discovery_service_instance(
        self,
        mock_cp4d_discovery_service_instance_settings,
        mock_connect_cp4d_discovery_service_instance,
        mock_discovery_get_discovery_collections,
    ):
        mock_cp4d_discovery_service_instance_settings[
            GENERIC.ATTR_SERVICE_TOKEN
        ] = "Test Token"
        get_collections_for_discovery_retriever(
            settings=mock_cp4d_discovery_service_instance_settings
        )
        mock_connect_cp4d_discovery_service_instance.assert_called_once_with(
            "https://cpd-test/discovery/instance", "Test Token"
        )
        mock_discovery_get_discovery_collections.assert_called_once_with(
            "Test Project ID"
        )

    def test_retrieve_for_discovery_retrievers_with_missing_service_endpoint(
        self,
    ):
        with pytest.raises(
            Error, match=ErrorMessages.DISCOVERY_MISSING_SERVICE_ENDPOINT
        ):
            retrieve_for_discovery_retrievers(
                query="test query",
                retriever={"retriever_id": "test retriever"},
                collection_id="test collection",
                settings={},
            )

    def test_retrieve_for_discovery_retrievers_for_unsupported_discovery_service_instance(
        self, mock_unsupported_discovery_service_instance_settings
    ):
        with pytest.raises(
            Error,
            match=ErrorMessages.DISCOVERY_UNSUPPORTED_CONNECTION_TYPE.value.strip(),
        ):
            retrieve_for_discovery_retrievers(
                query="test query",
                retriever={"retriever_id": "test retriever"},
                collection_id="test collection",
                settings=mock_unsupported_discovery_service_instance_settings,
            )

    def test_retrieve_for_discovery_retrievers_for_cloud_discovery_service_instance_with_missing_credentials(
        self, mock_cloud_discovery_service_instance_settings
    ):
        with pytest.raises(
            Error,
            match=ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip(),
        ):
            retrieve_for_discovery_retrievers(
                query="test query",
                retriever={"retriever_id": "test retriever"},
                collection_id="test collection",
                settings=mock_cloud_discovery_service_instance_settings,
            )

    def test_retrieve_for_discovery_retrievers_for_cloud_discovery_service_instance(
        self,
        mock_cloud_discovery_service_instance_settings,
        mock_connect_cloud_discovery_service_instance,
        mock_discovery_retrieve,
    ):
        mock_cloud_discovery_service_instance_settings[
            GENERIC.ATTR_SERVICE_API_KEY.value
        ] = "Test API Key"
        retrieve_for_discovery_retrievers(
            query="test query",
            retriever={"retriever_id": "test retriever"},
            collection_id="test collection",
            settings=mock_cloud_discovery_service_instance_settings,
        )
        mock_connect_cloud_discovery_service_instance.assert_called_once_with(
            "https://api.us-south.discovery.watson.cloud.ibm.com/instances/",
            "Test API Key",
        )
        mock_discovery_retrieve.assert_called_once_with(
            project_id=mock_cloud_discovery_service_instance_settings[
                WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID
            ],
            question="test query",
            collection_id="test collection",
            limit=10,
        )

    def test_retrieve_for_discovery_retrievers_for_cloud_discovery_service_instance_with_custom_parameter_value(
        self,
        mock_cloud_discovery_service_instance_settings,
        mock_connect_cloud_discovery_service_instance,
        mock_discovery_retrieve,
    ):
        mock_cloud_discovery_service_instance_settings[
            GENERIC.ATTR_SERVICE_API_KEY.value
        ] = "Test API Key"
        retrieve_for_discovery_retrievers(
            query="test query",
            retriever={
                "retriever_id": "test retriever",
                "parameters": [{"parameter_id": "count", "value": 5}],
            },
            collection_id="test collection",
            settings=mock_cloud_discovery_service_instance_settings,
        )
        mock_connect_cloud_discovery_service_instance.assert_called_once_with(
            "https://api.us-south.discovery.watson.cloud.ibm.com/instances/",
            "Test API Key",
        )
        mock_discovery_retrieve.assert_called_once_with(
            project_id=mock_cloud_discovery_service_instance_settings[
                WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID
            ],
            question="test query",
            collection_id="test collection",
            limit=5,
        )

    def test_retrieve_for_discovery_retrievers_for_cp4d_discovery_service_instance_with_missing_credentials(
        self, mock_cp4d_discovery_service_instance_settings
    ):
        with pytest.raises(
            Error,
            match=ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip(),
        ):
            retrieve_for_discovery_retrievers(
                query="test query",
                retriever={"retriever_id": "test retriever"},
                collection_id="test collection",
                settings=mock_cp4d_discovery_service_instance_settings,
            )

    def test_retrieve_for_discovery_retrievers_for_cp4_discovery_service_instance(
        self,
        mock_cp4d_discovery_service_instance_settings,
        mock_connect_cp4d_discovery_service_instance,
        mock_discovery_retrieve,
    ):
        mock_cp4d_discovery_service_instance_settings[
            GENERIC.ATTR_SERVICE_TOKEN.value
        ] = "Test Token"
        retrieve_for_discovery_retrievers(
            query="test query",
            retriever={"retriever_id": "test retriever"},
            collection_id="test collection",
            settings=mock_cp4d_discovery_service_instance_settings,
        )
        mock_connect_cp4d_discovery_service_instance.assert_called_once_with(
            "https://cpd-test/discovery/instance", "Test Token"
        )
        mock_discovery_retrieve.assert_called_once_with(
            project_id=mock_cp4d_discovery_service_instance_settings[
                WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID
            ],
            question="test query",
            collection_id="test collection",
            limit=10,
        )
