<!---
Copyright 2022 PrimeQA Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

<!-- START sphinx doc instructions - DO NOT MODIFY next code, please -->
<div align="center">
    <img src="static/PrimeQA.png" width="150"/>
</div>
<!-- END sphinx doc instructions - DO NOT MODIFY above code, please -->

# Orchestrator REST Microservice

This toolkit provides an orchestrator microservice that integrates PrimeQA's retriever & reader modules as a REST Server and also other "search" capabilities e.g. IBM Watson Discovery.

Hence, using this orchestrator one can either integrate a neural retriever like ColBERT from PrimeQA or external search e.g. IBM Watson Discovery to fetch documents and then use PrimeQA's reader to extract answer spans from those relevant documents.
<br>

[![LICENSE|Apache2.0](https://img.shields.io/github/license/saltstack/salt?color=blue)](https://www.apache.org/licenses/LICENSE-2.0.txt)

<h3>✔️ Getting Started</h3>

- [Repository](https://github.com/primeqa/primeqa-orchestrator)

<h3>✅ Prerequisites</h3>

- [Python 3.9](https://www.python.org/downloads/)

<h2>⚙️ Setup </h2>

<h3>📓 Third-party dependencies</h3>

- [PrimeQA](https://github.com/primeqa/primeqa): If you don't have access to running PrimeQA instance, then please refer to PrimeQA repository for more details on setting and running a local one.
- [Watson Discovery](https://cloud.ibm.com/) (Optional): Follow instructions on IBM Cloud to configure Watson Discovery V2 service.

<h3>🧩 Setup Local Environment</h3>

- [Setup and activate a Virtual Environment](https://docs.python.org/3/tutorial/venv.html) (as shown below) or use [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

```shell
# Install virtualenv
pip3 install virtualenv

# Create a new virtual environment for this project. If using pyenv, path_to_python_3.9_executable will be ~/.pyenv/versions/3.9.x/bin/python
virtualenv --python=<path_to_python_3.9_executable> venv

# Activate virtual environment
source venv/bin/activate
```

- Install dependencies

```shell
pip install -r requirements.txt
pip install -r requirements_test.txt
```

🐛 `gprcio` and `grpcio-tools` has limited support on Apple Silicone (M1, M2). Please refer to [grpc github issue#25082](https://github.com/grpc/grpc/issues/25082) for details or download appropriate wheels from [here](https://github.com/pietrodn/grpcio-mac-arm-build).

<h3>📜 TLS and Certificate Management</h3>

Orchestrator service REST server supports mutual or two-way TLS authentication (also known as mTLS). Application's [`config.ini`](orchestrator/service/config/config.ini) file contains the default certificate paths, but they can be overridden using environment variables.

Self-signed certificates are generated and packaged with the Docker build.
Self-signed certs _may be_ required for local development and testing. If you want to generate them, follow the steps below:

```shell
#!/usr/bin/env bash

# Make neccessary directories
mkdir -p security/
mkdir -p security/certs/
mkdir -p security/certs/ca security/certs/server security/certs/client

# Generate CA key and CA cert
openssl req -x509 -days 365 -nodes -newkey rsa:4096 -subj "/C=US/ST=New York/L=Yorktown Heights/O=IBM/OU=Research/CN=example.com" -keyout security/certs/ca/ca.key -out security/certs/ca/ca.crt

# Generate Server key (without passphrase) and Server cert signing request
openssl req -nodes -new -newkey rsa:4096 -subj "/C=US/ST=New York/L=Yorktown Heights/O=IBM/OU=Research/CN=example.com" -keyout security/certs/server/server.key -out security/certs/server/server.csr

# Sign Server cert
openssl x509 -req -days 365 -in security/certs/server/server.csr -CA security/certs/ca/ca.crt -CAkey security/certs/ca/ca.key -CAcreateserial -out security/certs/server/server.crt

# Generate Client key (without passphrase) and Client cert signing request
openssl req -nodes -new -newkey rsa:4096 -subj "/C=US/ST=New York/L=Yorktown Heights/O=IBM/OU=Research/CN=example.com" -keyout security/certs/client/client.key -out security/certs/client/client.csr

# Sign Client cert
openssl x509 -req -days 365 -in security/certs/client/client.csr -CA security/certs/ca/ca.crt -CAkey security/certs/ca/ca.key -CAserial security/certs/ca/ca.srl -out security/certs/client/client.crt

# Delete signing requests
rm -rf security/certs/server/server.csr
rm -rf security/certs/client/client.csr
```

**IMPORTANT:**

- By default, the application tries to load certs from `/opt/tls`. You will need to update appropriate `tls_*` variables in [`config.ini`](orchestrator/service/config/config.ini) during local use.

- We recommend to generate certificates with official signing authority and use them via volume mounts in the application container.

<h2>🛠 Build & Deployment </h2>

<h3>💻 Local</h3>

- Open Python IDE & set the created virtual environment
- Open `orchestrator/services/config/config.ini`, set `require_ssl = True` (if you wish to use TLS authentication) & `rest_port`
- Generate GRPC:
  ```shell
  #!/usr/bin/env bash
  set -xeuo pipefail
  python -m grpc_tools.protoc -I ./orchestrator/integrations/primeqa/protos --python_out=orchestrator/integrations/primeqa/grpc_generated --grpc_python_out=orchestrator/integrations/primeqa/grpc_generated orchestrator/integrations/primeqa/protos/indexer.proto
  python -m grpc_tools.protoc -I ./orchestrator/integrations/primeqa/protos --python_out=orchestrator/integrations/primeqa/grpc_generated --grpc_python_out=orchestrator/integrations/primeqa/grpc_generated orchestrator/integrations/primeqa/protos/parameter.proto
  python -m grpc_tools.protoc -I ./orchestrator/integrations/primeqa/protos --python_out=orchestrator/integrations/primeqa/grpc_generated --grpc_python_out=orchestrator/integrations/primeqa/grpc_generated orchestrator/integrations/primeqa/protos/reader.proto
  python -m grpc_tools.protoc -I ./orchestrator/integrations/primeqa/protos --python_out=orchestrator/integrations/primeqa/grpc_generated --grpc_python_out=orchestrator/integrations/primeqa/grpc_generated orchestrator/integrations/primeqa/protos/retriever.proto
  2to3 --fix=import --nobackups --write orchestrator/integrations/primeqa/grpc_generated
  ```
- Open `application.py` and run/debug
- Go to <http://localhost:{rest_port}/docs>
- To be able to use `reader`, `indexer` and `retriever` services, be sure you have access to running instance of PrimeQA container

<h3>💻 Docker</h3>

- Open `config.ini` and set `rest_port`
- Open `Dockerfile` and set the same value to `port`
- Run `docker build -f Dockerfile -t primeqa-orchestrator:$(cat VERSION) .` (creates docker image)
- Run `docker run --rm --name primeqa-orchestrator -d -p <port>:<port> --mount type=bind,source="$(pwd)"/store,target=/store -e STORE_DIR=/store primeqa-orchestrator:$(cat VERSION)` (run docker container)
- Go to <http://{Container's public URL}:{rest_port}/docs>
- To be able to use `reader`, `indexer` and `retriever` services, be sure you have access to running instance of PrimeQA container

<h2>🚨 Configure </h2>

- Before first use, you will need to specify few neccessary configurations to connect to third-party depedencies.
- Execute `[GET] /settings` endpoint to fetch existing settings.
- Update service endpoint for `PrimeQA` to point to url (inclusive of port) of PrimeQA instance in `retriever` and `reader` sections in settings.
  ![Example](/static/primeqa_orchestrator_patch_settings.gif)

<!-- START sphinx doc instructions - DO NOT MODIFY next code, please -->
<!-- PrimeQA doc sync -->
<h2>📄 Documentation Sync</h2>

**Keep PrimeQA documentation reference sync**  
Anytime this README files is updated, it is necessary to open a PR on PrimeQA repository to update, with the same modifications, **[the associated file](https://github.com/primeqa/primeqa/blob/main/docs/orchestrator.md)** used on [documentation page](https://primeqa.github.io/primeqa/orchestrator.html).  
_Do not modify initial image path_

<!-- END sphinx doc instructions - DO NOT MODIFY above code, please -->
