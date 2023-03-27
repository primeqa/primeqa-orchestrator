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

import logging
from typing import List
from statistics import fmean

from orchestrator.exceptions import Error, ErrorMessages
from orchestrator.constants import (
    GENERIC,
    ANSWER,
    EVIDENCE,
    ATTR_CONFIDENCE_SCORE,
    ATTR_CONFIDENCE,
)
from orchestrator.integrations.primeqa import (
    connect_primeqa_service,
    get_readers as get_readers_rpc,
    get_answers as get_answers_rpc,
)


_logger = logging.getLogger(__name__)


def get_primeqa_readers(settings: dict):
    # Step 1: Establish connection to PrimeQA service
    try:
        connect_primeqa_service(endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value])
    except KeyError as err:
        raise Error(ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT.value) from err

    # Step 2: Request available readers
    return get_readers_rpc()


def add_combination_score(documents: List[dict], answers: List[dict], beta: float):
    """
    Add combination score in answers based on it's document's confidence and answer's score

    **NOTE**: Answer must have "context_index" attribute in order to scale as per
    document's confidence

    Parameters
    ----------
    documents: list
        documents from which answers were derived
    answers: list
        answers to be scaled
    beta: float
        mixing parameter

    Returns
    -------

    """
    for answer in answers:
        # If "evidence" exits,
        if (
            ANSWER.ATTR_EVIDENCES.value in answer
            and answer[ANSWER.ATTR_EVIDENCES.value]
        ):
            try:
                document_confidence = fmean(
                    [
                        documents[evidence[EVIDENCE.ATTR_CONTEXT_INDEX.value]][
                            ATTR_CONFIDENCE
                        ]
                        for evidence in answer[ANSWER.ATTR_EVIDENCES.value]
                    ]
                )

                answer[ATTR_CONFIDENCE] = (
                    beta * answer[ATTR_CONFIDENCE_SCORE]
                    + (1 - beta) * document_confidence
                )
            except IndexError:
                _logger.warning(
                    "Failed to locate relevant context to compute combination score for answer: %s",
                    answer,
                )
                answer[ATTR_CONFIDENCE] = answer[ATTR_CONFIDENCE_SCORE]
        else:
            answer[ATTR_CONFIDENCE] = answer[ATTR_CONFIDENCE_SCORE]

    return sorted(answers, key=lambda d: d[ATTR_CONFIDENCE], reverse=True)


def get_answers(
    reader: dict,
    query: str,
    contexts: List[dict],
    settings: dict,
    apply_score_combination: bool = False,
) -> List[dict]:
    answers = []

    # Step 1: Establish connection to PrimeQA service
    try:
        # Step 1.a: Establish connection to PrimeQA readers service
        connect_primeqa_service(endpoint=settings[GENERIC.ATTR_SERVICE_ENDPOINT.value])

        # Step 1.b: Request answers
        answers_per_query = get_answers_rpc(reader, query, contexts)

        # Step 1.c: Calculate score as combination of answers[confidence_score] and contexts[confidence], if requested
        if apply_score_combination:
            answers = add_combination_score(
                documents=contexts,
                answers=answers_per_query[0],
                beta=settings[GENERIC.ATTR_READERS_BETA.value]
                if GENERIC.ATTR_READERS_BETA.value in settings
                and settings[GENERIC.ATTR_READERS_BETA.value]
                else 0.8,
            )
        else:
            answers = answers_per_query[0]
            # Step 1.d: Add "confidence" field required for downstream processing
            for answer in answers:
                answer[ATTR_CONFIDENCE] = answer[ATTR_CONFIDENCE_SCORE]

    except IndexError:
        _logger.error(ErrorMessages.PRIMEQA_FAILED_TO_FIND_ANSWER.value.strip())

    except KeyError as err:
        raise Error(ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT.value) from err

    return answers
