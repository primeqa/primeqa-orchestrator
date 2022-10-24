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

from ibm_watson import DiscoveryV2, ApiException
from ibm_cloud_sdk_core.authenticators import (
    IAMAuthenticator,
    BearerTokenAuthenticator,
)

# Configure IBM Watson discovery service connection
ACTIVE_ENDPOINT = None
WDS = None


def connect_cloud_discovery_service_instance(endpoint: str, api_key: str):
    global ACTIVE_ENDPOINT, WDS
    if ACTIVE_ENDPOINT != endpoint:
        WDS = DiscoveryV2(version="2020-08-30", authenticator=IAMAuthenticator(apikey=api_key))
        WDS.set_service_url(endpoint)

        # Set active endpoint
        ACTIVE_ENDPOINT = endpoint


def connect_cp4d_discovery_service_instance(endpoint: str, token: str):
    global ACTIVE_ENDPOINT, WDS
    if ACTIVE_ENDPOINT != endpoint:
        WDS = DiscoveryV2(version="2020-08-30", authenticator=BearerTokenAuthenticator(token))
        WDS.set_service_url(endpoint)
        WDS.set_disable_ssl_verification(True)

        # Set active endpoint
        ACTIVE_ENDPOINT = endpoint



def retrieve(project_id: str, question: str, collection_id: str, limit: int = 3):
    try:
        hits = WDS.query(
                    project_id=project_id,
                    collection_ids=[collection_id],
                    natural_language_query=question,
                    count=limit,
                ).get_result()["results"]
        return hits
    except ApiException:
        return []


def get_discovery_collections(project_id: str) -> list[dict]:
    return WDS.list_collections(project_id=project_id).get_result()["collections"]
        