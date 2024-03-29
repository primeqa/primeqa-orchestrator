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

import grpc
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Value

from orchestrator.constants import (
    READER,
    RETRIEVER,
    PARAMETER,
    ANSWER,
    EVIDENCE,
    ATTR_TEXT,
    ATTR_COLLECTION_ID,
    ATTR_NAME,
    ATTR_DESCRIPTION,
    ATTR_CONTEXT_INDEX,
)
from orchestrator.exceptions import Error, ErrorMessages

# PrimeQA-service gRPC connection
from orchestrator.integrations.primeqa.grpc_generated.parameter_pb2 import Parameter
from orchestrator.integrations.primeqa.grpc_generated.retriever_pb2_grpc import (
    RetrievingServiceStub,
)
from orchestrator.integrations.primeqa.grpc_generated.retriever_pb2 import (
    GetRetrieversRequest,
    RetrieveRequest,
    Retriever,
)

from orchestrator.integrations.primeqa.grpc_generated.reader_pb2_grpc import (
    ReadingServiceStub,
)
from orchestrator.integrations.primeqa.grpc_generated.reader_pb2 import (
    GetReadersRequest,
    GetAnswersRequest,
    Reader,
    Contexts,
)

from orchestrator.integrations.primeqa.grpc_generated.indexer_pb2_grpc import (
    IndexingServiceStub,
)
from orchestrator.integrations.primeqa.grpc_generated.indexer_pb2 import (
    GetIndexesRequest,
)


_logger = logging.getLogger(__name__)

# ------------------------------------ START -------------------------------------------------------
# --------------------------------------------------------------------------------------------------
#                            Golbal variables, Constants (PrimeQA gRPC Service)
# --------------------------------------------------------------------------------------------------
ACTIVE_ENDPOINT = None
MAX_SEND_MESSAGE_SIZE = 2e6

CHANNEL = None
RETRIEVER_STUB = None
INDEXER_STUB = None
READER_STUB = None


def build_grpc_parameters(parameters: list) -> List[Parameter]:
    grpc_parameters = []
    for parameter in parameters:
        if parameter[PARAMETER.ATTR_VALUE.value] is None:
            continue
        grpc_parameter = Parameter(parameter_id=parameter[PARAMETER.ATTR_ID.value])
        if (
            parameter[PARAMETER.ATTR_TYPE.value]
            == PARAMETER.PARAMETER_TYPE_STRING.value
        ):
            grpc_parameter.type = "String"
            grpc_parameter.value.CopyFrom(
                Value(string_value=parameter[PARAMETER.ATTR_VALUE.value])
            )
        elif (
            parameter[PARAMETER.ATTR_TYPE.value]
            == PARAMETER.PARAMETER_TYPE_NUMERIC.value
        ):
            grpc_parameter.type = "Numeric"
            grpc_parameter.value.CopyFrom(
                Value(number_value=parameter[PARAMETER.ATTR_VALUE.value])
            )
        elif (
            parameter[PARAMETER.ATTR_TYPE.value]
            == PARAMETER.PARAMETER_TYPE_BOOLEAN.value
        ):
            grpc_parameter.type = "Boolean"
            grpc_parameter.value.CopyFrom(
                Value(bool_value=parameter[PARAMETER.ATTR_VALUE.value])
            )
        else:
            _logger.debug(
                "%s",
                ErrorMessages.UNSUPPORTED_PARAMETER_TYPE.value.format(
                    type(parameter[PARAMETER.ATTR_VALUE.value])
                ),
            )
            _logger.debug("Skipping parameter: %s", parameter[PARAMETER.ATTR_ID.value])
            continue

        grpc_parameters.append(grpc_parameter)

    return grpc_parameters


def connect_primeqa_service(endpoint: str):
    if endpoint:
        global ACTIVE_ENDPOINT, CHANNEL, RETRIEVER_STUB, READER_STUB, INDEXER_STUB

        if ACTIVE_ENDPOINT != endpoint:
            if CHANNEL:
                # Close existing channel
                CHANNEL.close()

            # Open new channel
            CHANNEL = grpc.insecure_channel(endpoint)
            RETRIEVER_STUB = RetrievingServiceStub(CHANNEL)
            READER_STUB = ReadingServiceStub(CHANNEL)
            INDEXER_STUB = IndexingServiceStub(CHANNEL)

            # Set active endpoint
            ACTIVE_ENDPOINT = endpoint
    else:
        raise Error(ErrorMessages.PRIMEQA_MISSING_SERVICE_ENDPOINT.value)


# ------------------------------------------------------------------------------------------------
#                               Readers RPCs (PrimeQA gRPC Service)
# ------------------------------------------------------------------------------------------------
def get_readers():
    readers = []
    try:
        for reader in READER_STUB.GetReaders(GetReadersRequest()).readers:
            readers.append(
                MessageToDict(
                    reader,
                    preserving_proto_field_name=True,
                    including_default_value_fields=True,
                )
            )

        return readers
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            raise Error(ErrorMessages.PRIMEQA_CONNECTION_ERROR.value) from rpc_error
        else:
            raise Error(ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value) from rpc_error


def get_answers(reader: dict, query: str, documents: List[dict]):
    answers = []
    try:
        for answers_for_query in READER_STUB.GetAnswers(
            GetAnswersRequest(
                reader=Reader(
                    reader_id=reader[READER.ATTR_ID.value],
                    parameters=build_grpc_parameters(
                        reader[READER.ATTR_PARAMETERS.value]
                        if READER.ATTR_PARAMETERS.value in reader
                        and reader[READER.ATTR_PARAMETERS.value]
                        else []
                    ),
                ),
                queries=[query],
                contexts=[
                    Contexts(texts=[document[ATTR_TEXT] for document in documents])
                ],
            )
        ).query_answers:
            answers.append(
                [
                    MessageToDict(
                        answer,
                        preserving_proto_field_name=True,
                        including_default_value_fields=True,
                    )
                    for answers_per_context in answers_for_query.context_answers
                    for answer in answers_per_context.answers
                ]
            )

        # Re-adjust context indince to begin with zero, if present
        # NOTE: "proto3" syntax uses "0" as a default value for scalars, hence context indices are offset by "1"
        for answers_per_query in answers:
            for answer in answers_per_query:
                if (
                    ANSWER.ATTR_EVIDENCES.value in answer
                    and answer[ANSWER.ATTR_EVIDENCES.value]
                ):
                    for evidence in answer[ANSWER.ATTR_EVIDENCES.value]:
                        if EVIDENCE.ATTR_CONTEXT_INDEX.value in evidence:
                            evidence[EVIDENCE.ATTR_CONTEXT_INDEX.value] = (
                                evidence[EVIDENCE.ATTR_CONTEXT_INDEX.value] - 1
                            )

        return answers
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            raise Error(ErrorMessages.PRIMEQA_CONNECTION_ERROR.value) from rpc_error
        elif rpc_error.code() == grpc.StatusCode.INVALID_ARGUMENT:
            raise Error(
                ErrorMessages.PRIMEQA_INVALID_ARGUMENT_ERROR.value.format(
                    rpc_error.details()
                ).strip()
            ) from rpc_error
        else:
            raise Error(ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value) from rpc_error


# ------------------------------------------------------------------------------------------------
#                               Retrievers RPCs (PrimeQA gRPC Service)
# ------------------------------------------------------------------------------------------------
def get_retrievers():
    retrievers = []
    try:
        for retriever in RETRIEVER_STUB.GetRetrievers(
            GetRetrieversRequest()
        ).retrievers:
            retrievers.append(
                MessageToDict(
                    retriever,
                    preserving_proto_field_name=True,
                    including_default_value_fields=True,
                )
            )

        return retrievers
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            raise Error(ErrorMessages.PRIMEQA_CONNECTION_ERROR.value) from rpc_error
        else:
            raise Error(ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value) from rpc_error


def retrieve(retriever: dict, index_id: str, query: str):
    documents = list()
    try:
        for document in (
            RETRIEVER_STUB.Retrieve(
                RetrieveRequest(
                    retriever=Retriever(
                        retriever_id=retriever[RETRIEVER.ATTR_ID.value],
                        parameters=build_grpc_parameters(
                            retriever[RETRIEVER.ATTR_PARAMETERS.value]
                            if RETRIEVER.ATTR_PARAMETERS.value in retriever
                            and retriever[RETRIEVER.ATTR_PARAMETERS.value]
                            else []
                        ),
                    ),
                    index_id=index_id,
                    queries=[query],
                )
            )
            .hits[0]
            .hits
        ):
            documents.append(MessageToDict(document, preserving_proto_field_name=True))
    except IndexError as err:
        raise Error(ErrorMessages.PRIMEQA_FAILED_TO_FIND_ANSWER.value.strip()) from err
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            raise Error(ErrorMessages.PRIMEQA_CONNECTION_ERROR.value) from rpc_error
        elif rpc_error.code() == grpc.StatusCode.INVALID_ARGUMENT:
            raise Error(
                ErrorMessages.PRIMEQA_INVALID_ARGUMENT_ERROR.value.format(
                    rpc_error.details()
                ).strip()
            ) from rpc_error
        else:
            raise Error(ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value) from rpc_error

    # Return retrieved documents
    return documents


# ------------------------------------------------------------------------------------------------
#                               Indexer RPCs (PrimeQA gRPC Service)
# ------------------------------------------------------------------------------------------------
def get_indexes(engine_type: str):
    indexes = []
    try:
        for index in INDEXER_STUB.GetIndexes(
            GetIndexesRequest(engine_type=engine_type)
        ).indexes:
            index_information = {
                ATTR_COLLECTION_ID: index.index_id,
                ATTR_NAME: index.index_id,
                ATTR_DESCRIPTION: "",
            }
            if index.metadata:
                metadata = MessageToDict(
                    index.metadata, preserving_proto_field_name=True
                )
                if ATTR_NAME in metadata and metadata[ATTR_NAME]:
                    index_information[ATTR_NAME] = metadata[ATTR_NAME]

                if ATTR_DESCRIPTION in metadata and metadata[ATTR_DESCRIPTION]:
                    index_information[ATTR_DESCRIPTION] = metadata[ATTR_DESCRIPTION]

            indexes.append(index_information)

        return indexes
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            raise Error(ErrorMessages.PRIMEQA_CONNECTION_ERROR.value) from rpc_error
        elif rpc_error.code() == grpc.StatusCode.INVALID_ARGUMENT:
            raise Error(
                ErrorMessages.PRIMEQA_INVALID_ARGUMENT_ERROR.value.format(
                    rpc_error.details()
                ).strip()
            ) from rpc_error
        else:
            raise Error(ErrorMessages.PRIMEQA_GENERIC_RPC_ERROR.value) from rpc_error


# ------------------------------------ END -------------------------------------------------------
