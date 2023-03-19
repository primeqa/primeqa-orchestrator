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

from typing import List, Dict, Union, Literal
from pydantic import BaseModel

from orchestrator.constants import PARAMETER, EVIDENCE_TYPES


#############################################################################################
#                       Parameter
#############################################################################################
class Parameter(BaseModel):
    parameter_id: str
    name: Union[str, None] = None
    description: Union[str, None] = None
    type: Union[
        Literal[
            PARAMETER.PARAMETER_TYPE_BOOLEAN,
            PARAMETER.PARAMETER_TYPE_NUMERIC,
            PARAMETER.PARAMETER_TYPE_STRING,
        ],
        None,
    ] = None
    value: Union[int, float, bool, str, None]
    options: Union[List[bool], List[str], None] = None
    range: Union[List[int], List[float], None] = None


#############################################################################################
#                       Document
#############################################################################################
class Document(BaseModel):
    text: str
    score: float
    confidence: Union[float, None] = None
    document_id: Union[str, None] = None
    title: Union[str, None] = None
    url: Union[str, None] = None


#############################################################################################
#                       Evidence
#############################################################################################
class Offset(BaseModel):
    start: int
    end: int


class DocumentEvidence(BaseModel):
    evidence_type: str = EVIDENCE_TYPES.DOCUMENT.value
    text: str
    score: float
    document_id: Union[str, None] = None
    title: Union[str, None] = None
    url: Union[str, None] = None
    offsets: Union[List[Offset], None] = None


class TextEvidence(BaseModel):
    evidence_type: str = EVIDENCE_TYPES.TEXT.value
    text: str
    offsets: Union[List[Offset], None] = None


#############################################################################################
#                       Reader
#############################################################################################
class Reader(BaseModel):
    reader_id: str
    parameters: Union[List[Parameter], None] = None
    provenance: Union[str, None] = None


#############################################################################################
#                       Retriever
#############################################################################################
class Retriever(BaseModel):
    retriever_id: str
    parameters: Union[List[Parameter], None] = None
    provenance: Union[str, None] = None


#############################################################################################
#                       Collection
#############################################################################################
class Collection(BaseModel):
    collection_id: str
    name: Union[str, None] = None
    description: Union[str, None] = None


#############################################################################################
#                       Reading
#############################################################################################


class GetAnswersRequest(BaseModel):
    question: str
    contexts: List[str]
    reader: Reader


class Answer(BaseModel):
    text: str
    confidence_score: float
    evidences: Union[List[DocumentEvidence], List[TextEvidence], None] = None


#############################################################################################
#                       Retrieval
#############################################################################################
class GetDocumentsRequest(BaseModel):
    question: str
    retriever: Retriever
    collection: Collection


#############################################################################################
#                       Question Answering
#############################################################################################
class QuestionAnsweringRequest(BaseModel):
    question: str
    retriever: Retriever
    collection: Collection
    reader: Reader


class QuestionAnsweringResponse(BaseModel):
    answers: Union[List[Answer], None] = None
    documents: Union[List[Document], None] = None


#############################################################################################
#                       Feedback
#############################################################################################
class Feedback(BaseModel):
    feedback_id: str
    user_id: str
    question: str
    answer: str
    thumbs_up: bool
    thumbs_down: bool
    context: Union[str, None] = None
    start_char_offset: Union[int, None] = None
    end_char_offset: Union[int, None] = None
    application: Union[str, None] = None


class FeedbackInPrimeQAFormat(BaseModel):
    id: str
    question: str
    context: str
    answers: Dict[str, Union[List[int], List[str]]]
