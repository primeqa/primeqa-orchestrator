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

from enum import Enum


REST_SERVER_HOST = "REST_SERVER_PORT"
REST_SERVER_PORT = "REST_SERVER_PORT"


# JSON fields
ATTR_PARAMETERS = "parameters"
ATTR_APPLICATION_ID = "application_id"
ATTR_COLLECTION_ID = "collection_id"
ATTR_CONTEXT_INDEX = "context_index"
ATTR_PARAMETER_ID = "parameter_id"
ATTR_DOCUMENT = "document"
ATTR_ID = "id"
ATTR_DOCUMENT_ID = "document_id"
ATTR_NAME = "name"
ATTR_DESCRIPTION = "description"
ATTR_VALUE = "value"
ATTR_SETTINGS = "settings"
ATTR_TEXT = "text"
ATTR_URL = "url"
ATTR_TITLE = "title"
ATTR_CONTEXT = "context"
ATTR_PROVENANCE = "provenance"
ATTR_SCORE = "score"
ATTR_CONFIDENCE_SCORE = "confidence_score"
ATTR_CONFIDENCE = "confidence"
ATTR_QUESTION = "question"
ATTR_ANSWERS = "answers"
ATTR_ANSWER = "answer"
ATTR_START_CHAR_OFFSET = "start_char_offset"
ATTR_END_CHAR_OFFSET = "end_char_offset"
ATTR_ANSWER_START = "answer_start"


class RETRIEVER(str, Enum):
    ATTR_ID = "retriever_id"
    ATTR_PARAMETERS = "parameters"
    ATTR_ENGINE_TYPE = "engine_type"


class READER(str, Enum):
    ATTR_ID = "reader_id"
    ATTR_PARAMETERS = "parameters"


class ANSWER(str, Enum):
    ATTR_TEXT = "text"
    ATTR_START_CHAR_OFFSET = "start_char_offset"
    ATTR_END_CHAR_OFFSET = "end_char_offset"
    ATTR_CONFIDENCE = "confidence_score"
    ATTR_CONTEXT_INDEX = "context_index"


class PARAMETER(str, Enum):
    ATTR_ID = "parameter_id"
    ATTR_NAME = "name"
    ATTR_DESCRIPTION = "description"
    ATTR_TYPE = "type"
    ATTR_VALUE = "value"
    ATTR_OPTIONS = "options"
    ATTR_RANGE = "range"

    # parameter's types
    PARAMETER_TYPE_BOOLEAN = "Boolean"
    PARAMETER_TYPE_NUMERIC = "Numeric"
    PARAMETER_TYPE_STRING = "String"


class PRIMEQA(str, Enum):
    ATTR_INTEGRATION_ID = "PrimeQA"


class WATSON_DISCOVERY(str, Enum):
    ATTR_INTEGRATION_ID = "Watson Discovery"
    ATTR_SERVICE_PROJECT_ID = "service_project_id"


class GENERIC(str, Enum):
    # Service
    ATTR_SERVICE_ENDPOINT = "service_endpoint"
    ATTR_SERVICE_API_KEY = "service_api_key"
    ATTR_SERVICE_TOKEN = "service_token"
    ATTR_SERVICE_USERNAME = "service_username"
    ATTR_SERVICE_PASSWORD = "service_password"

    # Retrievers
    ATTR_RETRIEVERS = "retrievers"
    ATTR_RETRIEVERS_ALPHA = "alpha"

    # Readers
    ATTR_READERS = "readers"
    ATTR_READERS_BETA = "beta"


class FEEDBACK(str, Enum):
    FEEDBACK_ID = "feedback_id"
    USER_ID = "user_id"
    QUESTION = "question"
    CONTEXT = "context"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    ANSWER = "answer"
    START_CHAR_OFFSET = "start_char_offset"
    END_CHAR_OFFSET = "end_char_offset"
    APPLICATION = "application"


class FEEDBACK_RESPONSE_FORMAT(str, Enum):
    RAW = "raw"
    PRIMEQA = "primeqa"
