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

from unittest.mock import MagicMock
import pytest

from orchestrator.utils import (
    load_json,
    min_max_normalization,
    normalize,
    save_json,
    to_bool,
    update_dict,
)


class TestUtils:
    @pytest.fixture
    def mock_open(self, mocker) -> MagicMock:
        return mocker.patch("orchestrator.utils.open")

    @pytest.fixture
    def mock_json(self, mocker) -> MagicMock:
        return mocker.patch("orchestrator.utils.json")

    def test_load_json(self, mock_open, mock_json):
        load_json(file_path="test file path")
        mock_open.assert_called_once_with("test file path", "r", encoding="utf-8")
        mock_json.load.assert_called_once()

    def test_save_json(self, mocker, mock_open, mock_json):
        mock_os_mkdir = mocker.patch("orchestrator.utils.os.mkdir")
        save_json(item={"key": "value"}, file_path="test file path")
        mock_os_mkdir.assert_called_once()
        mock_open.assert_called_once_with("test file path", "w", encoding="utf-8")
        mock_json.dump.assert_called_once()

    def test_to_bool(self):
        # True conditions
        assert to_bool(True)
        assert to_bool("1")
        assert to_bool("t")
        assert to_bool("true")
        with pytest.raises(
            ValueError, match="Invalid literal for boolean. Not a string."
        ):
            assert to_bool(1)

        # False conditions
        assert not to_bool(False)
        assert not to_bool("0")
        assert not to_bool("f")
        assert not to_bool("false")
        with pytest.raises(
            ValueError, match="Invalid literal for boolean. Not a string."
        ):
            assert not to_bool(0)

        # Invalid literal
        with pytest.raises(ValueError, match="Invalid literal for boolean: random"):
            assert to_bool("random")

    def test_update_dict(self):
        data = {"key 1": "value 1", "key 2": {"key 3": "value 3"}}
        update = {"key 2": {"key 3": "value x"}, "key 4": "value 4"}
        update_dict(data, update)

        assert data["key 4"] == "value 4"
        assert data["key 2"]["key 3"] == "value x"

    def test_min_max_normalization(self):
        normalized_scores = min_max_normalization(scores=[5, 4, 3, 1, 0])
        assert normalized_scores[0] == 1.0
        assert normalized_scores[1] < 1.0

        normalized_scores = min_max_normalization(scores=[10, 10])
        assert normalized_scores[0] == 1.0
        assert normalized_scores[1] == 1.0

    def test_normalize(self):
        data_1 = [{"value": 5}, {"value": 4}, {"value": 3}, {"value": 2}, {"value": 1}]
        normalize(data_1, field="value")
        assert data_1[0]["confidence"] == 1.0
        assert data_1[1]["confidence"] == 0.75

        data_2 = [{"value": 5}]
        normalize(data_2, field="value")
        assert data_2[0]["confidence"] == 1.0
