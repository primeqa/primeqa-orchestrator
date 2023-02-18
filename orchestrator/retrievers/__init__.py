from typing import List, Union
from datetime import datetime, timedelta, timezone
from copy import deepcopy

from orchestrator.store import StoreFactory
from orchestrator.constants import (
    GENERIC,
    PARAMETER,
    PRIMEQA,
    WATSON_DISCOVERY,
    RETRIEVER,
    ATTR_PARAMETERS,
    ATTR_PROVENANCE,
    ATTR_SCORE,
)
from orchestrator.exceptions import Error, ErrorMessages
from orchestrator.utils import normalize
from orchestrator.retrievers.discovery import (
    get_discovery_retrievers,
    get_collections_for_discovery_retriever,
    retrieve_for_discovery_retrievers,
)
from orchestrator.retrievers.primeqa import (
    get_primeqa_retrievers,
    get_collections_for_primeqa_retriever,
    retrieve_for_primeqa_retrievers,
)


class RetrieversRegistry:
    _retrievers = {}
    _registry_ttl = 60 * 5
    _last_refreshed = None

    @classmethod
    def is_stale(cls) -> bool:
        # If retrievers are recently fetched
        if cls._last_refreshed and cls._last_refreshed + timedelta(
            seconds=cls._registry_ttl
        ) < datetime.now(timezone.utc):
            return False

        return True

    @classmethod
    def has(cls, retriever_id: str) -> bool:
        if retriever_id in cls._retrievers:
            return True

        return False

    @classmethod
    def get(cls, retriever_id: str = None) -> Union[dict, List[dict]]:
        if retriever_id:
            return cls._retrievers[retriever_id]

        return [retriever for retriever in cls._retrievers.values()]

    @classmethod
    def load(
        cls,
        settings: dict = StoreFactory.get_store().get_settings()[
            GENERIC.ATTR_RETRIEVERS.value
        ],
    ):
        # Step 1: Load Watson Discovery retrievers, only if integrated
        if (
            WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value in settings
            and settings[WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value]
        ):
            for retriever in get_discovery_retrievers():
                retriever[ATTR_PROVENANCE] = WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value
                cls._retrievers[retriever["retriever_id"]] = retriever

        # Step 2: Load PrimeQA retrievers, only if integrated
        if (
            PRIMEQA.ATTR_INTEGRATION_ID.value in settings
            and settings[PRIMEQA.ATTR_INTEGRATION_ID.value]
        ):
            for retriever in get_primeqa_retrievers(
                settings=settings[PRIMEQA.ATTR_INTEGRATION_ID.value]
            ):
                retriever[ATTR_PROVENANCE] = PRIMEQA.ATTR_INTEGRATION_ID.value
                cls._retrievers[retriever["retriever_id"]] = retriever

        # Update last_refreshed
        cls._last_refreshed = datetime.now(timezone.utc)


def fetch_collections(retriever_id: str):
    # Step 1: Fetch requested retriever from registry
    retriever = RetrieversRegistry.get(retriever_id=retriever_id)

    # Step 2: Make appropriate get collections call based on provenance
    retriever_settings = StoreFactory.get_store().get_settings()[
        GENERIC.ATTR_RETRIEVERS.value
    ]
    # Step 2.a: Watson Discovery retriever
    if (
        retriever[ATTR_PROVENANCE] == WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value
        and WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value in retriever_settings
        and retriever_settings[WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value]
    ):
        return get_collections_for_discovery_retriever(
            settings=retriever_settings[WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value]
        )

    # Step 2.b: PrimeQA retriever
    elif (
        retriever[ATTR_PROVENANCE] == PRIMEQA.ATTR_INTEGRATION_ID.value
        and PRIMEQA.ATTR_INTEGRATION_ID.value in retriever_settings
        and retriever_settings[PRIMEQA.ATTR_INTEGRATION_ID.value]
    ):
        return get_collections_for_primeqa_retriever(
            engine_type=retriever[RETRIEVER.ATTR_ENGINE_TYPE]
            if RETRIEVER.ATTR_ENGINE_TYPE in retriever
            else "",
            settings=retriever_settings[PRIMEQA.ATTR_INTEGRATION_ID.value],
        )
    else:
        return []


def retrieve(
    query: str,
    retriever_id: str,
    collection_id: str,
    parameters_with_updates: Union[List[dict], None] = None,
    should_normalize: bool = False,
) -> List[dict]:
    # Step 1: Verify non-empty query
    if not query:
        raise Error(
            ErrorMessages.INVALID_REQUEST.value.format(
                '"query" cannot be empty.'
            ).strip()
        )

    # Step 2: Fetch requested retriever from registry
    retriever_settings = StoreFactory.get_store().get_settings()[
        GENERIC.ATTR_RETRIEVERS.value
    ]
    try:
        # Step 2.a: Check retriever registry's health
        if RetrieversRegistry.is_stale():
            RetrieversRegistry.load(settings=retriever_settings)

        # Step 2.b: Get retriever
        retriever = RetrieversRegistry.get(retriever_id=retriever_id)
    except KeyError as err:
        raise Error(
            ErrorMessages.RETRIEVER_DOES_NOT_EXISTS.value.format(retriever_id).strip()
        ) from err

    # Step 3: If retriever parameter are provided
    if parameters_with_updates:
        # Step 3.a: Create a deepcopy to preserve default values for retriever
        retriever = deepcopy(retriever)

        # Step 3.b: Update parameter values in newly deep-copied retriever
        for parameter_with_update in parameters_with_updates:
            for existing_parameter in retriever[ATTR_PARAMETERS]:
                if (
                    existing_parameter[PARAMETER.ATTR_ID.value]
                    == parameter_with_update.parameter_id
                ):
                    existing_parameter[
                        PARAMETER.ATTR_VALUE.value
                    ] = parameter_with_update.value

    # Step 4: Call retriever's retrieve method
    if (
        retriever[ATTR_PROVENANCE] == WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value
        and WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value in retriever_settings
        and retriever_settings[WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value]
    ):
        documents = retrieve_for_discovery_retrievers(
            query=query,
            retriever=retriever,
            collection_id=collection_id,
            settings=retriever_settings[WATSON_DISCOVERY.ATTR_INTEGRATION_ID.value],
        )
        # Normalize document scores
        if should_normalize:
            normalize(
                documents,
                field=ATTR_SCORE,
            )
        return documents
    elif (
        retriever[ATTR_PROVENANCE] == PRIMEQA.ATTR_INTEGRATION_ID.value
        and PRIMEQA.ATTR_INTEGRATION_ID.value in retriever_settings
        and retriever_settings[PRIMEQA.ATTR_INTEGRATION_ID.value]
    ):
        documents = retrieve_for_primeqa_retrievers(
            query=query,
            retriever=retriever,
            collection_id=collection_id,
            settings=retriever_settings[PRIMEQA.ATTR_INTEGRATION_ID.value],
        )
        # Normalize document scores
        if should_normalize:
            normalize(
                documents,
                field=ATTR_SCORE,
            )
        return documents
    else:
        return []
