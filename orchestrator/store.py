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

from typing import List
import logging
import os
from pathlib import Path
import shutil
import sqlite3

from pkg_resources import resource_filename
from orchestrator.exceptions import ErrorMessages
from orchestrator.utils import update_dict, load_json, save_json
from orchestrator.constants import ATTR_SETTINGS, FEEDBACK


_PRIMEQA_APPLICATION_FILE = resource_filename("data", "primeqa.json")


#############################################################################################
# store/
#        primqa.json
#        sqlite_db.db
#############################################################################################
class StoreFactory:
    __store = None

    @staticmethod
    def get_store():
        if StoreFactory.__store is None:
            StoreFactory.__store = Store()

        return StoreFactory.__store


class Store:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.root_dir = os.getenv(
            "STORE_DIR", os.path.join(Path(__file__).parent.parent, "store")
        )
        if not os.path.exists(self.root_dir):
            # Step 1: Make empty directory
            os.makedirs(self.root_dir)

        if not os.path.exists(os.path.join(self.root_dir, "primeqa.json")):
            # Copy over default primeqa application JSON
            shutil.copy(_PRIMEQA_APPLICATION_FILE, self.root_dir)

        # if no db file, create and add feedback table
        if not os.path.exists(os.path.join(self.root_dir, "sqlite_db.db")):
            conn = sqlite3.connect(self.root_dir + "/sqlite_db.db")
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS feedback_table (feedback_id VARCHAR, user_id VARCHAR, question VARCHAR, answer VARCHAR, thumbs_up BOOLEAN, thumbs_down BOOLEAN, context VARCHAR, start_char_offset INTEGER, end_char_offset INTEGER)"
            )
            conn.commit()
            conn.close()

    #############################################################################################
    #                       Settings
    #############################################################################################
    def get_settings(self) -> dict:
        """
        Retrieves settings associated to primeqa application

        Returns
        -------
        list: dict
            applications associated with the playground
        """
        application = load_json(os.path.join(self.root_dir, "primeqa.json"))
        return application[ATTR_SETTINGS]

    def update_settings(self, update: dict) -> dict:
        # Load existing settings
        application = load_json(os.path.join(self.root_dir, "primeqa.json"))

        # Update settings
        update_dict(application[ATTR_SETTINGS], update)

        # Save updated settings
        save_json(application, os.path.join(self.root_dir, "primeqa.json"))

        return application[ATTR_SETTINGS]

    #############################################################################################
    #                       Feedback
    #############################################################################################
    def get_feedbacks(
        self,
        where_clauses: dict = None,
        select_clauses: List[str] = None,
    ) -> list:
        """
        Retrieves feedback table data (/store/sqlite_db.db)
        Returns
        -------
        list: dict (FeedbackRequest)

        """
        # Step 1: Build where clause
        sql_command = (
            f"SELECT {', '.join(select_clauses)} FROM feedback_table"
            if select_clauses
            else "SELECT * FROM feedback_table"
        )
        if where_clauses:
            where_clauses_in_str = " WHERE "
            for field_name, field_value in where_clauses.items():
                if isinstance(field_value, list):
                    field_values_in_str = '"' + '","'.join(field_value) + '"'
                    where_clauses_in_str += (
                        f"{field_name} IN ({field_values_in_str}) AND "
                    )
                elif isinstance(field_value, str):
                    field_value_in_str = '"' + field_value + '"'
                    where_clauses_in_str += f"{field_name}={field_value_in_str} AND "
                else:
                    where_clauses_in_str += f"{field_name}={field_value} AND "

            # Strip away last "AND" condition
            where_clauses_in_str = where_clauses_in_str.rstrip(" AND ")

            sql_command += where_clauses_in_str

        try:
            conn = sqlite3.connect(self.root_dir + "/sqlite_db.db")
            cur = conn.cursor()
            cur.execute(sql_command)
            rows = cur.fetchall()

            # Step 2.d: Iterate over results
            return [
                {
                    FEEDBACK.FEEDBACK_ID.value: row[0],
                    FEEDBACK.USER_ID.value: row[1],
                    FEEDBACK.QUESTION.value: row[2],
                    FEEDBACK.ANSWER.value: row[3],
                    FEEDBACK.THUMBS_UP.value: row[4],
                    FEEDBACK.THUMBS_DOWN.value: row[5],
                    FEEDBACK.CONTEXT.value: row[6],
                    FEEDBACK.START_CHAR_OFFSET.value: row[7],
                    FEEDBACK.END_CHAR_OFFSET.value: row[8],
                }
                for row in rows
            ]

        except sqlite3.Error as error:
            self.logger.warning(
                ErrorMessages.FAILED_TO_EXECUTE_COMMAND.value.format(
                    error.args[0]
                ).strip()
            )
            return []
        finally:
            if conn:
                conn.close()

    def save_feedback(self, feedback: dict) -> dict:
        """
        Save feedback data

        Parameters
        ----------
        feedback: dict (Feedback)

        Returns
        -------
        saved feedback: dict (Feedback)

        """
        try:
            conn = sqlite3.connect(self.root_dir + "/sqlite_db.db")
            cur = conn.cursor()
            # check existing feedback associated to user request
            cur.execute(
                "SELECT * FROM feedback_table WHERE feedback_id=? AND user_id=?",
                (
                    feedback[FEEDBACK.FEEDBACK_ID.value],
                    feedback[FEEDBACK.USER_ID.value],
                ),
            )
            rows = cur.fetchall()
            # if feedback for the same item & category already exists and it was saved by same user,
            # update with new data (only thumbs props is updated)
            # else, save as new item
            if len(rows) > 0:
                self.update_feedback(
                    feedback[FEEDBACK.FEEDBACK_ID.value],
                    feedback[FEEDBACK.USER_ID.value],
                    feedback,
                )
            else:
                cur.execute(
                    "INSERT INTO feedback_table VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    list(feedback.values()),
                )
            conn.commit()
            cur.close()
        except sqlite3.Error as error:
            print("Failed to save column of sqlite table", error)
        finally:
            if conn:
                conn.close()
                print("sqlite connection is closed")

    def update_feedback(self, feedback_id: str, user_id: str, update: dict) -> dict:
        """
        Update feedback data

        Parameters
        ----------
        feedback_id: str
        user_id: str
        update: dict

        Returns
        -------
        saved message: dict

        """
        try:
            conn = sqlite3.connect(self.root_dir + "/sqlite_db.db")
            cur = conn.cursor()
            # Step 2: Collect all field names with updates
            fields_to_be_updated = {
                field: value
                for field, value in update.items()
                if field != FEEDBACK.FEEDBACK_ID.value
                and field != FEEDBACK.USER_ID.value
            }
            # Step 3: If fields with updates exists,
            if fields_to_be_updated:
                cur.execute(
                    "UPDATE feedback_table SET "
                    + "=?,".join(fields_to_be_updated.keys())
                    + "=?"
                    + "WHERE feedback_id=? AND user_id=?",
                    [*list(fields_to_be_updated.values()), feedback_id, user_id],
                )
                conn.commit()
                cur.close()
            return {"OK": True}
        except sqlite3.Error as error:
            print("Failed to update multiple columns of sqlite table", error)
        finally:
            if conn:
                conn.close()
                print("sqlite connection is closed")

    def delete_feedback(self, feedback_id: str, user_id: str) -> dict:
        """
        Delete feedback data

        Parameters
        ----------
        feedback_id: str
        user_id: str

        Returns
        -------

        """
        try:
            conn = sqlite3.connect(self.root_dir + "/sqlite_db.db")
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM feedback_table WHERE feedback_id=? AND user_id=?",
                (
                    feedback_id,
                    user_id,
                ),
            )
            conn.commit()
            return {"OK": True}
        except sqlite3.Error as error:
            print("Failed to delete column of sqlite table", error)
        finally:
            if conn:
                conn.close()
                print("sqlite connection is closed")
