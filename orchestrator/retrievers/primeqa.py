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

from orchestrator.exceptions import Error, ErrorMessages
from orchestrator.constants import (
    GENERIC,
    ATTR_DOCUMENT_ID,
    ATTR_TEXT,
    ATTR_TITLE,
    ATTR_SCORE,
)
from orchestrator.integrations.primeqa import (
    connect_primeqa_service,
    get_retrievers as get_retrievers_rpc,
    get_indexes as get_indexes_rpc,
    retrieve as retrieve_rpc,
)


def get_primeqa_retrievers(settings: dict):
    # Step 1: Establish connection to PrimeQA service
    try:
        connect_primeqa_service(endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value])
    except KeyError as err:
        raise Error(ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT.value) from err

    # Step 2: Request available retrievers
    return get_retrievers_rpc()


def get_collections_for_primeqa_retriever(engine_type: str, settings: dict):
    # Step 1: Establish connection to PrimeQA service
    try:
        connect_primeqa_service(endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value])
    except KeyError as err:
        raise Error(ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT.value) from err

    # Step 2: Request collections for retriever
    return get_indexes_rpc(engine_type)


def retrieve_for_primeqa_retrievers(
    query: str, retriever: dict, collection_id: str, settings: dict
):
    # Step 1: Establish connection to PrimeQA service
    try:
        connect_primeqa_service(endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value])
    except KeyError as err:
        raise Error(ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT.value) from err

    # Step 2: Run retrieve RPC
    return [
        {
            ATTR_TEXT: hit["document"][ATTR_TEXT],
            ATTR_SCORE: hit[ATTR_SCORE],
            ATTR_DOCUMENT_ID: hit["document"][ATTR_DOCUMENT_ID]
            if ATTR_DOCUMENT_ID in hit["document"]
            else None,
            ATTR_TITLE: hit["document"][ATTR_TITLE]
            if ATTR_TITLE in hit["document"]
            else None,
        }
        for hit in retrieve_rpc(
            retriever=retriever, index_id=collection_id, query=query
        )
    ]
