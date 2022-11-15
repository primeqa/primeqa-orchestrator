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

from typing import List, Union
import json
import os
import collections.abc as abc
from orchestrator.constants import ATTR_CONFIDENCE


def load_json(file_path: str, encoding: str = "utf-8"):
    """
    Load JSON file from the filesystem.

    Parameters
    ----------
    file_path: str
        path from where JSON file has to be loaded.
    encoding: str
        encoding used to load file (default: "utf-8")

    Returns
    -------

    """
    with open(file_path, "r", encoding=encoding) as file:
        item = json.load(file)
        return item


def save_json(item, file_path: str, encoding: str = "utf-8"):
    """
    Save an object to a JSON file.

    Parameters
    ----------
    item: object
        data to be stored into a JSON file.

    file_path: str
        path to JSON file

    encoding: str
        encoding used to save file (default: "utf-8")

    Returns
    -------

    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding=encoding) as file:
        json.dump(item, file, indent=4)


def to_bool(value: str):
    valid = {
        "true": True,
        "t": True,
        "1": True,
        "false": False,
        "f": False,
        "0": False,
    }

    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        raise ValueError("Invalid literal for boolean. Not a string.")

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError(f"Invalid literal for boolean: {value}")


def update_dict(dictionary: dict, update: dict) -> dict:
    for key, value in update.items():
        if isinstance(value, abc.Mapping):
            dictionary[key] = update_dict(dictionary.get(key, {}), value)
        else:
            dictionary[key] = value
    return dictionary


def min_max_normalization(scores: List[Union[int, float]]):
    low = min(scores)
    high = max(scores)
    width = high - low
    if width == 0:
        return [1.0] * len(scores)
    return [(s - low) / width for s in scores]


def normalize(hits: List[dict], field: str):
    if hits:
        # Check if single hit, set confidence to "1.0"
        if len(hits) == 1:
            hits[0][ATTR_CONFIDENCE] = 1.0
        else:
            # If more than one hit
            for idx, confidence in enumerate(
                min_max_normalization([hit[field] for hit in hits])
            ):
                hits[idx][ATTR_CONFIDENCE] = confidence
