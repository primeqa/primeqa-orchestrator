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
from typing import List, Literal, Union
import time

import uvicorn
from fastapi import FastAPI, status, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from orchestrator.configurations import Settings
from orchestrator.store import StoreFactory
from orchestrator.retrievers import RetrieversRegistry, fetch_collections, retrieve
from orchestrator.readers import ReadersRegistry, read

from orchestrator.constants import (
    FEEDBACK,
    FEEDBACK_RESPONSE_FORMAT,
    GENERIC,
    ANSWER,
    EVIDENCE,
    OFFSET,
    EVIDENCE_TYPES,
    TEXT_EVIDENCE,
    DOCUMENT_EVIDENCE,
    ATTR_ID,
    ATTR_TEXT,
    ATTR_SCORE,
    ATTR_CONFIDENCE,
    ATTR_DOCUMENT_ID,
    ATTR_TITLE,
    ATTR_URL,
    ATTR_ANSWERS,
    ATTR_ANSWER_START,
    ATTR_DOCUMENTS,
)
from orchestrator.service.data_models import (
    Reader,
    GetAnswersRequest,
    Answer,
    GetDocumentsRequest,
    Retriever,
    Collection,
    QuestionAnsweringRequest,
    QuestionAnsweringResponse,
    Document,
    Feedback,
    FeedbackInPrimeQAFormat,
)
from orchestrator.exceptions import PATTERN_ERROR_MESSAGE, ErrorMessages, Error

# Initialize logger
_logger = logging.getLogger(__name__)

# Initialize configuration and store
config = Settings()
STORE = StoreFactory.get_store()

# Start tracking time for initialization
start_t = time.time()

# Set server options
#############################################################################################
#                                   API SERVER
#############################################################################################
app = FastAPI(
    title="PrimeQA Orchestrator Service",
    version="0.0.3",
    contact={
        "name": "PrimeQA Team",
        "url": "https://github.com/primeqa/primeqa",
        "email": "primeqa@us.ibm.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True if config.require_client_auth else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


#############################################################################################
#                       Setttings APIs
#############################################################################################
@app.get(
    "/settings",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    tags=["Settings"],
)
def get_settings():
    """
    Retrieve PrimeQA application settings.

    Returns
    -------
    settings associated to PrimeQA application

    """
    return STORE.get_settings()


#############################################################################################
#                           Retrieval APIs
#############################################################################################
@app.get(
    "/retrievers",
    status_code=status.HTTP_200_OK,
    response_model=Union[List[Retriever], List[dict]],
    tags=["Retrieval"],
)
def get_retrievers():
    """
    Get retrievers

    Parameters
    ----------

    Returns
    -------
    retrievers: list of retrievers

    """
    try:
        # Step 1: Load settings
        settings = STORE.get_settings()

        # Step 2: If retriever's registry is stale, reload it
        if RetrieversRegistry.is_stale():
            RetrieversRegistry.load(settings[GENERIC.ATTR_RETRIEVERS.value])

        # Step 3: Return
        return RetrieversRegistry.get()
    except Error as err:
        error_message = err.args[0]

        # Identify error code
        mobj = PATTERN_ERROR_MESSAGE.match(error_message)
        if mobj:
            error_code = mobj.group(1).strip()
            error_message = mobj.group(2).strip()
        else:
            error_code = 500

        raise HTTPException(
            status_code=500,
            detail={"code": error_code, "message": error_message},
        ) from err


@app.get(
    "/retrievers/{retriever_id}/collections",
    status_code=status.HTTP_200_OK,
    response_model=Union[List[Collection], List[dict]],
    tags=["Retrieval"],
)
def get_retriever_collections(retriever_id: str):
    try:
        return fetch_collections(retriever_id)
    except KeyError as err:
        error_message = ErrorMessages.RETRIEVER_DOES_NOT_EXISTS.value.format(
            retriever_id
        ).strip()

        # Identify error code
        mobj = PATTERN_ERROR_MESSAGE.match(error_message)
        if mobj:
            error_code = mobj.group(1).strip()
            error_message = mobj.group(2).strip()
        else:
            error_code = 500

        raise HTTPException(
            status_code=500,
            detail={"code": error_code, "message": error_message},
        ) from err


@app.post(
    "/GetDocumentsRequest",
    status_code=status.HTTP_201_CREATED,
    response_model=List[Document],
    tags=["Retrieval"],
    response_model_exclude_none=True,
)
def get_documents_for_question(gd_request: GetDocumentsRequest):
    try:
        documents = retrieve(
            query=gd_request.question,
            retriever_id=gd_request.retriever.retriever_id,
            collection_id=gd_request.collection.collection_id,
            parameters_with_updates=gd_request.retriever.parameters,
            should_normalize=False,
        )

        if documents:
            return [
                {
                    ATTR_TEXT: document[ATTR_TEXT],
                    ATTR_SCORE: document[ATTR_SCORE],
                    ATTR_DOCUMENT_ID: document[ATTR_DOCUMENT_ID]
                    if ATTR_DOCUMENT_ID in document
                    else None,
                    ATTR_TITLE: document[ATTR_TITLE]
                    if ATTR_TITLE in document
                    else None,
                    ATTR_URL: document[ATTR_URL] if ATTR_URL in document else None,
                }
                for document in documents
            ]
        else:
            return []

    except Error as err:
        error_message = err.args[0]

        # Identify error code
        mobj = PATTERN_ERROR_MESSAGE.match(error_message)
        if mobj:
            error_code = mobj.group(1).strip()
            error_message = mobj.group(2).strip()
        else:
            error_code = 500

        raise HTTPException(
            status_code=500,
            detail={"code": error_code, "message": error_message},
        ) from err


#############################################################################################
#                           Reading APIs
#############################################################################################
@app.get(
    "/readers",
    status_code=status.HTTP_200_OK,
    response_model=Union[List[Reader], List[dict]],
    tags=["Reading"],
)
def get_readers():
    """
    Get readers

    Parameters
    ----------

    Returns
    -------
    readers: list of readers

    """

    try:
        # Step 1: Load settings
        settings = STORE.get_settings()

        # Step 2: If reader's registry is stale, reload it
        if ReadersRegistry.is_stale():
            ReadersRegistry.load(settings[GENERIC.ATTR_READERS.value])

        # Step 3: Return
        return ReadersRegistry.get()

    except Error as err:
        error_message = err.args[0]

        # Identify error code
        mobj = PATTERN_ERROR_MESSAGE.match(error_message)
        if mobj:
            error_code = mobj.group(1).strip()
            error_message = mobj.group(2).strip()
        else:
            error_code = 500

        raise HTTPException(
            status_code=500,
            detail={"code": error_code, "message": error_message},
        ) from err


@app.post(
    "/GetAnswersRequest",
    status_code=status.HTTP_201_CREATED,
    response_model=List[Answer],
    tags=["Reading"],
    response_model_exclude_none=True,
)
def get_answers_for_contexts(ga_request: GetAnswersRequest):
    try:
        answers = read(
            query=ga_request.question,
            reader_id=ga_request.reader.reader_id,
            contexts=[
                {ATTR_TEXT: context, ATTR_CONFIDENCE: 1.0}
                for context in ga_request.contexts
            ],
            parameters_with_updates=ga_request.reader.parameters,
            apply_score_combination=False,
        )

        if answers:
            response = []
            for answer in answers:
                # Populate mandatory fields
                response.append(
                    {
                        ANSWER.ATTR_TEXT.value: answer[ATTR_TEXT],
                        ANSWER.ATTR_CONFIDENCE.value: answer[ATTR_CONFIDENCE],
                    }
                )

                # Add optional field ("evidences"), if present
                if ANSWER.ATTR_EVIDENCES.value in answer:
                    evidences = []
                    for entry in answer[ANSWER.ATTR_EVIDENCES.value]:
                        # Create single "evidence" instance
                        evidence = {
                            TEXT_EVIDENCE.ATTR_EVIDENCE_TYPE.value: EVIDENCE_TYPES.TEXT.value
                        }

                        # Add optional field ("context_index") to evidence, if present
                        if EVIDENCE.ATTR_CONTEXT_INDEX.value in entry:
                            evidence[
                                TEXT_EVIDENCE.ATTR_TEXT.value
                            ] = ga_request.contexts[
                                entry[EVIDENCE.ATTR_CONTEXT_INDEX.value] - 1
                            ]
                        # Add optional field ("text") to evidence, only if "context_index" is abscent and "text" is present
                        elif EVIDENCE.ATTR_TEXT.value in entry:
                            evidence[TEXT_EVIDENCE.ATTR_TEXT.value] = entry[
                                EVIDENCE.ATTR_TEXT.value
                            ]

                        # Add optional field ("offsets") to evidence, if present
                        if (
                            EVIDENCE.ATTR_OFFSETS.value in entry
                            and entry[EVIDENCE.ATTR_OFFSETS.value]
                        ):
                            evidence[EVIDENCE.ATTR_OFFSETS.value] = [
                                {
                                    OFFSET.ATTR_START.value: offset[
                                        OFFSET.ATTR_START.value
                                    ],
                                    OFFSET.ATTR_END.value: offset[
                                        OFFSET.ATTR_END.value
                                    ],
                                }
                                for offset in entry[EVIDENCE.ATTR_OFFSETS.value]
                            ]

                        # Add filled "evidence" instance to list of "evidences"
                        evidences.append(evidence)

                    if evidences:
                        response[-1][ANSWER.ATTR_EVIDENCES.value] = evidences
            return response
        else:
            return []

    except Error as err:
        error_message = err.args[0]

        # Identify error code
        mobj = PATTERN_ERROR_MESSAGE.match(error_message)
        if mobj:
            error_code = mobj.group(1).strip()
            error_message = mobj.group(2).strip()
        else:
            error_code = 500

        raise HTTPException(
            status_code=500,
            detail={"code": error_code, "message": error_message},
        ) from err


#############################################################################################
#                           Question Answering API
#############################################################################################
@app.post(
    "/ask",
    status_code=status.HTTP_201_CREATED,
    response_model=QuestionAnsweringResponse,
    tags=["Question Answering (QA)"],
    response_model_exclude_none=True,
)
def ask(qa_request: QuestionAnsweringRequest):
    try:
        # Step 1: Run retriever
        documents = retrieve(
            query=qa_request.question,
            retriever_id=qa_request.retriever.retriever_id,
            collection_id=qa_request.collection.collection_id,
            parameters_with_updates=qa_request.retriever.parameters,
            should_normalize=True,
        )

        # Step 2: Run reader
        if documents:
            answers = read(
                query=qa_request.question,
                reader_id=qa_request.reader.reader_id,
                contexts=documents,
                parameters_with_updates=qa_request.reader.parameters,
                apply_score_combination=True,
            )

            if answers:
                response = {ATTR_ANSWERS: [], ATTR_DOCUMENTS: documents}
                for answer in answers:
                    # Populate mandatory fields
                    response[ATTR_ANSWERS].append(
                        {
                            ANSWER.ATTR_TEXT.value: answer[ATTR_TEXT],
                            ANSWER.ATTR_CONFIDENCE.value: answer[ATTR_CONFIDENCE],
                        }
                    )

                    # Add optional field ("evidences"), if present
                    if ANSWER.ATTR_EVIDENCES.value in answer:
                        evidences = []
                        for entry in answer[ANSWER.ATTR_EVIDENCES.value]:
                            # Create single "evidence" instance
                            evidence = {}

                            # If "context_index" is present, form "DocumentEvidence" object
                            if EVIDENCE.ATTR_CONTEXT_INDEX.value in entry:
                                evidence_document = documents[
                                    entry[EVIDENCE.ATTR_CONTEXT_INDEX.value]
                                ]

                                # Add mandatory fields
                                evidence[
                                    DOCUMENT_EVIDENCE.ATTR_EVIDENCE_TYPE.value
                                ] = EVIDENCE_TYPES.DOCUMENT.value
                                evidence[
                                    DOCUMENT_EVIDENCE.ATTR_TEXT.value
                                ] = evidence_document[ATTR_TEXT]
                                evidence[
                                    DOCUMENT_EVIDENCE.ATTR_SCORE.value
                                ] = evidence_document[ATTR_SCORE]

                                # Add optional fields
                                if ATTR_DOCUMENT_ID in evidence_document:
                                    evidence[
                                        DOCUMENT_EVIDENCE.ATTR_DOCUMENT_ID.value
                                    ] = evidence_document[ATTR_DOCUMENT_ID]

                                if ATTR_TITLE in evidence_document:
                                    evidence[
                                        DOCUMENT_EVIDENCE.ATTR_TITLE.value
                                    ] = evidence_document[ATTR_TITLE]

                                if ATTR_URL in evidence_document:
                                    evidence[
                                        DOCUMENT_EVIDENCE.ATTR_URL.value
                                    ] = evidence_document[ATTR_URL]
                            elif (
                                EVIDENCE.ATTR_TEXT.value in entry
                                and entry[EVIDENCE.ATTR_TEXT.value]
                            ):
                                # Add mandatory fields
                                evidence[
                                    TEXT_EVIDENCE.ATTR_EVIDENCE_TYPE.value
                                ] = EVIDENCE_TYPES.TEXT.value
                                evidence[TEXT_EVIDENCE.ATTR_TEXT.value] = entry[
                                    ATTR_TEXT
                                ]

                            # Add optional field ("offsets") to evidence, if present
                            try:
                                if (
                                    EVIDENCE.ATTR_OFFSETS.value in entry
                                    and entry[EVIDENCE.ATTR_OFFSETS.value]
                                ):
                                    evidence[EVIDENCE.ATTR_OFFSETS.value] = [
                                        {
                                            OFFSET.ATTR_START.value: offset[
                                                OFFSET.ATTR_START.value
                                            ],
                                            OFFSET.ATTR_END.value: offset[
                                                OFFSET.ATTR_END.value
                                            ],
                                        }
                                        for offset in entry[EVIDENCE.ATTR_OFFSETS.value]
                                    ]
                            except KeyError:
                                _logger.warning(
                                    "Failed to add all offset fields for evidence: %s",
                                    entry,
                                )

                            # Add filled "evidence" instance to list of "evidences"
                            if evidence:
                                evidences.append(evidence)

                        if evidences:
                            response[ATTR_ANSWERS][-1][
                                ANSWER.ATTR_EVIDENCES.value
                            ] = evidences

                return response

            else:
                return {ATTR_DOCUMENTS: documents}
        return {}

    except Error as err:
        error_message = err.args[0]

        # Identify error code
        mobj = PATTERN_ERROR_MESSAGE.match(error_message)
        if mobj:
            error_code = mobj.group(1).strip()
            error_message = mobj.group(2).strip()
        else:
            error_code = 500

        raise HTTPException(
            status_code=500,
            detail={"code": error_code, "message": error_message},
        ) from err


#############################################################################################
#                       Feedback APIs
#############################################################################################
@app.get(
    "/feedbacks",
    status_code=status.HTTP_200_OK,
    response_model=Union[List[Feedback], List[FeedbackInPrimeQAFormat]],
    tags=["Feedback"],
)
def get_feedbacks(
    feedback_id: Union[List[str], None] = Query(default=None),
    user_id: Union[List[str], None] = Query(default=None),
    application: Union[List[str], None] = Query(default=None),
    _format: Union[
        Literal[FEEDBACK_RESPONSE_FORMAT.RAW, FEEDBACK_RESPONSE_FORMAT.PRIMEQA], None
    ] = None,
):
    """
    Retrieves feedback table data (/store/sqlite_db.db)

    Returns
    -------
    list: dict (FeedbackRequest)

    """
    where_clauses = {}
    if feedback_id:
        where_clauses[FEEDBACK.FEEDBACK_ID.value] = feedback_id

    if user_id:
        where_clauses[FEEDBACK.USER_ID.value] = user_id

    if application:
        where_clauses[FEEDBACK.APPLICATION.value] = application

    feedbacks = STORE.get_feedbacks(where_clauses=where_clauses)

    if _format and _format == FEEDBACK_RESPONSE_FORMAT.PRIMEQA.value:
        # *special case*: "primeqa" format assumes only positive feedback returns
        return [
            {
                ATTR_ID: feedback_idx,
                FEEDBACK.QUESTION.value: feedback[FEEDBACK.QUESTION.value],
                FEEDBACK.CONTEXT.value: feedback[FEEDBACK.CONTEXT.value],
                ATTR_ANSWERS: {
                    ATTR_TEXT: [feedback[FEEDBACK.ANSWER.value]],
                    ATTR_ANSWER_START: [feedback[FEEDBACK.START_CHAR_OFFSET.value]],
                },
            }
            for feedback_idx, feedback in enumerate(feedbacks)
            if feedback[FEEDBACK.THUMBS_UP] == 1
        ]

    return feedbacks


@app.post(
    "/feedbacks",
    status_code=status.HTTP_201_CREATED,
    response_model=Feedback,
    tags=["Feedback"],
)
def post_feedback(feedback: Feedback):
    """
    Save feedback data

    Parameters
    ----------
    feedback: dict (Feedback)

    Returns
    -------
    saved feedback: dict (Feedback)

    """
    feedback = feedback.dict()
    STORE.save_feedback(feedback)

    return STORE.get_feedbacks(
        where_clauses={
            FEEDBACK.FEEDBACK_ID: feedback[FEEDBACK.FEEDBACK_ID.value],
            FEEDBACK.USER_ID: feedback[FEEDBACK.USER_ID.value],
        }
    )[0]


@app.patch(
    "/feedbacks/{feedback_id}",
    status_code=status.HTTP_200_OK,
    response_model=Feedback,
    tags=["Feedback"],
)
def update_feedback(
    feedback_id: str,
    update: dict,
):
    """
    Update feedback data

    Parameters
    ----------
    feedback_id: str
    update: dict

    Returns
    -------
    saved message: dict
    """
    STORE.update_feedback(feedback_id, update[FEEDBACK.USER_ID.value], update)

    return STORE.get_feedbacks(
        where_clauses={
            FEEDBACK.FEEDBACK_ID: feedback_id,
            FEEDBACK.USER_ID: update[FEEDBACK.USER_ID.value],
        }
    )[0]


@app.delete(
    "/feedbacks/{feedback_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    tags=["Feedback"],
)
def delete_feedback(feedback_id: str, delete_request: dict):
    """
    Delete feedback data

    Parameters
    ----------
    feedback_id: str
    delete_request: dict

    Returns
    -------

    """
    return STORE.delete_feedback(feedback_id, delete_request[FEEDBACK.USER_ID.value])


_logger.info(
    "Server instance started on port %s - initialization took %.6f seconds",
    config.rest_port,
    time.time() - start_t,
)


#############################################################################################
#                           Entry Method
#############################################################################################
def main() -> None:
    """
    Primary entry method
    """
    if config.require_ssl:
        server_config = uvicorn.Config(
            app,
            host=config.rest_host,
            port=config.rest_port,
            workers=config.num_rest_server_workers,
            ssl_keyfile=config.tls_server_key,
            ssl_certfile=config.tls_server_cert,
            ssl_ca_certs=config.tls_ca_cert,
        )
    else:
        server_config = uvicorn.Config(
            app,
            host=config.rest_host,
            port=config.rest_port,
            workers=config.num_rest_server_workers,
        )

    # Run server
    uvicorn.Server(server_config).run()


if __name__ == "__main__":
    main()
