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

import re
from orchestrator.constants import (
    ATTR_DOCUMENT_ID,
    ATTR_PARAMETERS,
    ATTR_SCORE,
    ATTR_TEXT,
    ATTR_TITLE,
    ATTR_CONFIDENCE,
    ATTR_URL,
    GENERIC,
    PARAMETER,
    WATSON_DISCOVERY,
)
from orchestrator.integrations.discovery import (
    connect_cp4d_discovery_service_instance,
    connect_cloud_discovery_service_instance,
    get_discovery_collections,
    retrieve,
)
from orchestrator.exceptions import Error, ErrorMessages


PATTERN_WATSON_DISCOVEY_CP4D_ENDPOINT = re.compile(r"https?://(cpd.*)/discovery/.*")
PATTERN_WATSON_DISCOVEY_CLOUD_ENDPOINT = re.compile(
    r"https://api.*.discovery.watson.cloud.ibm.com/.*"
)


def get_discovery_retrievers():
    return [
        {
            "retriever_id": "WatsonDiscovery",
            "parameters": [
                {
                    "parameter_id": "count",
                    "name": "Count",
                    "description": "Maximum number of documents",
                    "type": "Numeric",
                    "value": 5,
                    "range": [1, 20, 1],
                }
            ],
        }
    ]


def get_collections_for_discovery_retriever(settings: dict):
    try:
        # Step 1: Identify Watson Discovery instance type (IBM Cloud, Cloud Pack for Data [CP4D])
        # Step 1.a: Cloud Pack for Data [CP4D]
        cp4d_endpoint_mobj = PATTERN_WATSON_DISCOVEY_CP4D_ENDPOINT.match(
            settings[GENERIC.ATTR_SERVICE_ENDPOINT.value]
        )
        if cp4d_endpoint_mobj:
            # Step 1.a.i: Verify availability of connection credentials and establish connection
            if (
                settings[GENERIC.ATTR_SERVICE_TOKEN.value]
                and settings[WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value]
            ):
                connect_cp4d_discovery_service_instance(
                    endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value],
                    token=settings[GENERIC.ATTR_SERVICE_TOKEN.value],
                )
            else:
                raise Error(
                    ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip()
                )
        # Step 1.b: IBM Cloud
        elif PATTERN_WATSON_DISCOVEY_CLOUD_ENDPOINT.match(
            settings[GENERIC.ATTR_SERVICE_ENDPOINT.value]
        ):
            # Step 1.b.i: Verify availability of connection credentials and establish connection
            if (
                settings[GENERIC.ATTR_SERVICE_API_KEY.value]
                and settings[WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value]
            ):
                connect_cloud_discovery_service_instance(
                    endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value],
                    api_key=settings[GENERIC.ATTR_SERVICE_API_KEY.value],
                )
            else:
                raise Error(
                    ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip()
                )
        else:
            raise Error(
                ErrorMessages.DISCOVERY_UNSUPPORTED_CONNECTION_TYPE.value.strip()
            )

        return get_discovery_collections(
            settings[WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value]
        )
    except KeyError as err:
        raise Error(
            ErrorMessages.DISCOVERY_MISSING_SERVICE_ENDPOINT.value.strip()
        ) from err


def retrieve_for_discovery_retrievers(
    query: str, retriever: dict, collection_id: str, settings: dict
):
    # Step 1: Identify Watson Discovery instance type (IBM Cloud, Cloud Pack for Data [CP4D])
    try:
        # Step 1.a: Cloud Pack for Data [CP4D]
        cp4d_endpoint_mobj = PATTERN_WATSON_DISCOVEY_CP4D_ENDPOINT.match(
            settings[GENERIC.ATTR_SERVICE_ENDPOINT.value]
        )
        if cp4d_endpoint_mobj:
            # Step 1.a.i: Verify availability of connection credentials and establish connection
            if (
                settings[GENERIC.ATTR_SERVICE_TOKEN.value]
                and settings[WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value]
            ):
                connect_cp4d_discovery_service_instance(
                    endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value],
                    token=settings[GENERIC.ATTR_SERVICE_TOKEN.value],
                )
            else:
                raise Error(
                    ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip()
                )
        # Step 1.b: IBM Cloud
        elif PATTERN_WATSON_DISCOVEY_CLOUD_ENDPOINT.match(
            settings[GENERIC.ATTR_SERVICE_ENDPOINT.value]
        ):
            # Step 1.b.i: Verify availability of connection credentials and establish connection
            if (
                settings[GENERIC.ATTR_SERVICE_API_KEY.value]
                and settings[WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value]
            ):
                connect_cloud_discovery_service_instance(
                    endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value],
                    api_key=settings[GENERIC.ATTR_SERVICE_API_KEY.value],
                )
            else:
                raise Error(
                    ErrorMessages.DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS.value.strip()
                )
        else:
            raise Error(
                ErrorMessages.DISCOVERY_UNSUPPORTED_CONNECTION_TYPE.value.strip()
            )
    except KeyError as err:
        raise Error(
            ErrorMessages.DISCOVERY_MISSING_SERVICE_ENDPOINT.value.strip()
        ) from err

    # Step 2: Read parameters
    limit = 10
    if ATTR_PARAMETERS in retriever:
        for parameter in retriever[ATTR_PARAMETERS]:
            if parameter[PARAMETER.ATTR_ID.value] == "count":
                limit = parameter[PARAMETER.ATTR_VALUE.value]

    # Step 3: Run
    return [
        {
            ATTR_TEXT: " ".join(hit[ATTR_TEXT]),
            ATTR_SCORE: hit["result_metadata"][ATTR_CONFIDENCE],
            ATTR_DOCUMENT_ID: hit[ATTR_DOCUMENT_ID]
            if ATTR_DOCUMENT_ID in hit
            else None,
            ATTR_TITLE: hit[ATTR_TITLE] if ATTR_TITLE in hit else None,
            ATTR_URL: hit[ATTR_URL] if ATTR_URL in hit else None,
        }
        for hit in retrieve(
            project_id=settings[WATSON_DISCOVERY.ATTR_SERVICE_PROJECT_ID.value],
            question=query,
            collection_id=collection_id,
            limit=limit,
        )
    ]
