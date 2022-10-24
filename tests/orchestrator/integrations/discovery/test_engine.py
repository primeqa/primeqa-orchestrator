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

from orchestrator.integrations.discovery.engine import (
    connect_cloud_discovery_service_instance,
    connect_cp4d_discovery_service_instance,
    get_discovery_collections,
    retrieve,
)


class TestDiscoveryIntegration:
    @pytest.fixture()
    def mock_ibm_watson_DiscoveryV2(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.integrations.discovery.engine.DiscoveryV2",
            autospec=True,
        )

    @pytest.fixture()
    def mock_ibm_cloud_sdk_core_authenticators_IAMAuthenticator(
        self, mocker
    ) -> MagicMock:
        return mocker.patch(
            "orchestrator.integrations.discovery.engine.IAMAuthenticator",
            autospec=True,
        )

    @pytest.fixture()
    def mock_ibm_cp4d_sdk_core_authenticators_BearerTokenAuthenticator(
        self, mocker
    ) -> MagicMock:
        return mocker.patch(
            "orchestrator.integrations.discovery.engine.BearerTokenAuthenticator",
            autospec=True,
        )

    @pytest.fixture()
    def mock_WDS(self, mocker) -> MagicMock:
        return mocker.patch(
            "orchestrator.integrations.discovery.engine.WDS",
        )

    def test_connect_cloud_discovery_service_instance(
        self,
        mock_ibm_cloud_sdk_core_authenticators_IAMAuthenticator,
        mock_ibm_watson_DiscoveryV2,
    ):
        connect_cloud_discovery_service_instance(
            endpoint="test endpoint", api_key="test api key"
        )
        mock_ibm_cloud_sdk_core_authenticators_IAMAuthenticator.assert_called_once_with(
            apikey="test api key"
        )
        mock_ibm_watson_DiscoveryV2.assert_called_once()
        mock_ibm_watson_DiscoveryV2_instance = mock_ibm_watson_DiscoveryV2.return_value
        mock_ibm_watson_DiscoveryV2_instance.set_service_url.assert_called_once_with(
            "test endpoint"
        )

    def test_connect_cp4d_discovery_service_instance(
        self,
        mock_ibm_cp4d_sdk_core_authenticators_BearerTokenAuthenticator,
        mock_ibm_watson_DiscoveryV2,
    ):
        connect_cp4d_discovery_service_instance(
            endpoint="test endpoint 2", token="test token"
        )
        mock_ibm_cp4d_sdk_core_authenticators_BearerTokenAuthenticator.assert_called_once_with(
            "test token"
        )
        mock_ibm_watson_DiscoveryV2.assert_called_once()
        mock_ibm_watson_DiscoveryV2_instance = mock_ibm_watson_DiscoveryV2.return_value
        mock_ibm_watson_DiscoveryV2_instance.set_service_url.assert_called_once_with(
            "test endpoint 2"
        )
        mock_ibm_watson_DiscoveryV2_instance.set_disable_ssl_verification.assert_called_once_with(
            True
        )

    def test_get_discovery_collections(
        self,
        mock_WDS,
    ):
        get_discovery_collections(project_id="test project id")
        mock_WDS.list_collections.assert_called_once_with(project_id="test project id")

    def test_retrieve(
        self,
        mock_WDS,
    ):
        retrieve(
            project_id="test project id",
            question="test question",
            collection_id="test collection id",
            limit=5,
        )
        mock_WDS.query.assert_called_once_with(
            project_id="test project id",
            collection_ids=["test collection id"],
            natural_language_query="test question",
            count=5,
        )
