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

from pathlib import Path
import pkg_resources
from setuptools import setup, find_packages


PROJECT_ROOT_DIR = Path(__file__).parent.resolve()


# Get the version for the project
with open(PROJECT_ROOT_DIR / "VERSION", "r", encoding="utf-8") as version_file:
    version = version_file.read().strip()

# Build long description based on README.md
with open(PROJECT_ROOT_DIR / "README.md", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

with open(
    PROJECT_ROOT_DIR / "requirements.txt", "r", encoding="utf-8"
) as requirements_file:
    requirements = [
        str(req) for req in pkg_resources.parse_requirements(requirements_file.read())
    ]

with open(
    PROJECT_ROOT_DIR / "requirements_test.txt", "r", encoding="utf-8"
) as requirements_file:
    requirements_test = [
        str(req) for req in pkg_resources.parse_requirements(requirements_file.read())
    ]

setup(
    name="primeqa_orchestrator",
    url="https://github.com/primeqa/primeqa-orchestrator",
    version=version,
    author="PrimeQA Team",
    author_email="primeqa@us.ibm.com",
    description="PrimeQA Orchestrator REST Microservice",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: MacOS",
        "Operating System :: POSIX:: Linux",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="Question Answering (QA), Machine Reading Comprehension (MRC), Information Retrieval (IR), microservices",
    python_requires=">=3.9.0, <3.10.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=requirements,
    include_package_data=True,
    tests_require=requirements_test,
    test_suite="tests",
    entry_points={
        "console_scripts": ["run_orchestrator=orchestrator.service.application:main"]
    },
)
