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
from enum import Enum

PATTERN_ERROR_MESSAGE = re.compile("(E[0-9]{4,5}):(.*)")


class Error(Exception):
    pass


class ErrorMessages(str, Enum):

    # Discovery
    DISCOVERY_MISSING_SERVICE_ENDPOINT = (
        "E4001: Missing watson discovery service endpoint in settings."
    )
    DISCOVERY_UNSUPPORTED_CONNECTION_TYPE = (
        "E4002: Unsupported watson discovery connection type."
    )
    DISCOVERY_MISSING_AUTHENTICATION_CREDENTIALS = (
        "E4003: Missing authentical credentials for watson discovery instance."
    )

    # PrimeQA
    PRIMEQA_MISSING_SERVICE_ENDPOINT = (
        "E5001: Missing primeqa service endpoint in settings."
    )
    PRIMEQA_CONNECTION_ERROR = "E5002: Failed to establish connection."
    PRIMEQA_FAILED_TO_FIND_ANSWER = "E5003: Failed to find answer. {}"

    PRIMEQA_INVALID_ARGUMENT_ERROR = "E5098: {}"
    PRIMEQA_GENERIC_RPC_ERROR = (
        "E5099: Something went wrong. Please contact technical support."
    )

    # Generic
    INVALID_REQUEST = "E1001: Invalid Request. {}"

    # RETRIEVERS
    RETRIEVER_DOES_NOT_EXISTS = "E6001: {} retriever does not exists. Please make sure you are selecting one of the available retrievers."

    # READERS
    READER_DOES_NOT_EXISTS = "E7001: {} reader does not exists. Please make sure you are selecting one of the available readers."

    # PARAMETERS
    UNSUPPORTED_PARAMETER_TYPE = "E8001: Unsupport parameter type: {}"

    # NETWORK
    NETWORK_ERROR = "E9001: Failed to establish connection."

    # SQL DATABASE
    FAILED_TO_EXECUTE_COMMAND = "E2001: Failed to execute command. {}"
