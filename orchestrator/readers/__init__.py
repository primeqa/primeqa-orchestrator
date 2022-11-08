from typing import List, Union
from datetime import datetime, timedelta, timezone
from copy import deepcopy

from orchestrator.store import StoreFactory
from orchestrator.constants import (
    GENERIC,
    PRIMEQA,
    PARAMETER,
    ATTR_PARAMETERS,
    ATTR_PROVENANCE,
)
from orchestrator.readers.primeqa import get_primeqa_readers, get_answers
from orchestrator.exceptions import Error, ErrorMessages


class ReadersRegistry:
    _readers = {}
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
    def has(cls, reader_id: str) -> bool:
        if reader_id in cls._readers:
            return True

        return False

    @classmethod
    def get(cls, reader_id: str = None) -> Union[dict, List[dict]]:
        if reader_id:
            return cls._readers[reader_id]

        return [reader for reader in cls._readers.values()]

    @classmethod
    def load(
        cls,
        settings: dict = StoreFactory.get_store().get_settings()[
            GENERIC.ATTR_READERS.value
        ],
    ):
        # Step 1: Load PrimeQA readers, only if integrated
        if (
            PRIMEQA.ATTR_INTEGRATION_ID.value in settings
            and settings[PRIMEQA.ATTR_INTEGRATION_ID.value]
        ):
            for reader in get_primeqa_readers(
                settings=settings[PRIMEQA.ATTR_INTEGRATION_ID.value]
            ):
                reader[ATTR_PROVENANCE] = PRIMEQA.ATTR_INTEGRATION_ID.value
                cls._readers[reader["reader_id"]] = reader

        # Update last_refreshed
        cls._last_refreshed = datetime.now(timezone.utc)


def read(
    query: str,
    reader_id: str,
    contexts: List[dict],
    parameters_with_updates: List[dict],
) -> List[dict]:
    # Step 1: Verify non-empty query
    if not query:
        raise Error(
            ErrorMessages.INVALID_REQUEST.value.format(
                '"query" cannot be empty.'
            ).strip()
        )

    # Step 2: Fetch requested reader from registry
    reader_settings = StoreFactory.get_store().get_settings()[
        GENERIC.ATTR_READERS.value
    ]
    try:
        # Step 2.a: Check reader registry's health
        if ReadersRegistry.is_stale():
            ReadersRegistry.load(settings=reader_settings)

        # Step 2.b: Get reader
        reader = ReadersRegistry.get(reader_id)

    except KeyError as err:
        raise Error(
            ErrorMessages.READER_DOES_NOT_EXISTS.value.format(reader_id).strip()
        ) from err

    # Step 3: If parameters with update are provided
    if parameters_with_updates:
        # Step 3.a: Create a deepcopy to preserve default values for reader
        reader = deepcopy(reader)

        # Step 3.b: Update parameter values in newly deep-copied reader
        for parameter_with_update in parameters_with_updates:
            for existing_parameter in reader[ATTR_PARAMETERS]:
                if (
                    existing_parameter[PARAMETER.ATTR_ID.value]
                    == parameter_with_update.parameter_id
                ):
                    existing_parameter[
                        PARAMETER.ATTR_VALUE.value
                    ] = parameter_with_update.value

    # Step 4: Call reader's get_answers method
    if (
        reader[ATTR_PROVENANCE] == PRIMEQA.ATTR_INTEGRATION_ID.value
        and PRIMEQA.ATTR_INTEGRATION_ID.value in reader_settings
        and reader_settings[PRIMEQA.ATTR_INTEGRATION_ID.value]
    ):
        return get_answers(
            reader=reader,
            query=query,
            contexts=contexts,
            settings=reader_settings[PRIMEQA.ATTR_INTEGRATION_ID.value],
        )
    else:
        return []
