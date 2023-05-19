FROM python:3.9-slim-bullseye as python-base

# #############################################################################
FROM python-base as prep

WORKDIR /security/certs

# Ephemeral certificates
RUN mkdir -p ca/ server/ client/ && \
    # Generate CA key and CA cert
    openssl req -x509 -days 365 -nodes -newkey rsa:4096 \
    -subj "/C=US/ST=New York/L=Yorktown Heights/O=IBM/OU=Research/CN=example.com" \
    -keyout ca/ca.key -out ca/ca.crt && \
    # Generate Server key (without passphrase) and Server cert signing request
    openssl req -nodes -new -newkey rsa:4096 \
    -subj "/C=US/ST=New York/L=Yorktown Heights/O=IBM/OU=Research/CN=example.com" \
    -keyout server/server.key -out server/server.csr && \
    # Sign Server cert
    openssl x509 -req -days 365 \
    -in server/server.csr -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial \
    -out server/server.crt && \
    # Generate Client key (without passphrase) and Client cert signing request
    openssl req -nodes -new -newkey rsa:4096 \
    -subj "/C=US/ST=New York/L=Yorktown Heights/O=IBM/OU=Research/CN=example.com" \
    -keyout client/client.key -out client/client.csr && \
    # Sign Client cert
    openssl x509 -req -days 365 \
    -in client/client.csr -CA ca/ca.crt -CAkey ca/ca.key -CAserial ca/ca.srl \
    -out client/client.crt && \
    # Delete signing requests
    rm -rf server/server.csr && \
    rm -rf client/client.csr

WORKDIR /protos

# Process primeqa Protos
RUN mkdir primeqa
COPY ./orchestrator/integrations/primeqa/protos/*.proto ./primeqa/
RUN pip install grpcio-tools==1.48.1 && \
    python -m grpc_tools.protoc -I./primeqa --python_out=./primeqa --grpc_python_out=./primeqa ./primeqa/*.proto && \
    # the grpc_tools appears to use python2 style import statements, which fail in python3
    # https://github.com/grpc/grpc/issues/9575, we convert the import statements using the provided
    # 2to3 Python utility https://docs.python.org/3.9/library/2to3.html
    # 2to3 --fix=import --nobackups --write ./ && \
    # 2to3 failing to replace imports, switching to sed:
    sed -i 's/^import \([a-z_][a-zA-Z0-9_]*\) as \([a-z_][a-zA-Z0-9_]*\)$/from . import \1 as \2/' ./primeqa/*.py
# #############################################################################

FROM python-base as wheel

WORKDIR /app

COPY ./setup.py ./VERSION ./LICENSE ./MANIFEST.in ./README.md ./requirements.txt ./requirements_test.txt ./ 

COPY ./data ./data

COPY ./orchestrator ./orchestrator

COPY --from=prep /protos/primeqa/*.py ./orchestrator/integrations/primeqa/grpc_generated/

RUN python setup.py bdist_wheel --python-tag py3 

# #############################################################################

FROM python-base as base

RUN apt update && \
    DEBIAN_FRONTEND="noninteractive" TZ="America/New_York" \
    apt install -y ca-certificates tini && \
    rm -rf /var/lib/apt/lists

# Ephemeral certificates
COPY --from=prep /security/certs /opt/tls

RUN chmod -R 0664 /opt/tls/ca/* && \
    chmod -R 0664 /opt/tls/client/* && \
    chmod -R 0664 /opt/tls/server/*

# Set Python specific configurations
ENV PYTHONDONTWRITEBYTECODE true
ENV PYTHONFAULTHANDLER true

# Default configurations
USER root

# Expose server port
ENV port 50059
EXPOSE ${port}

# Create application user
RUN useradd -c "Application User" -U -u 2000 -d /app -m app

# Setup and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
## This automatically enables virtualenv for both, Docker RUN and CMD commands
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Setup work dir
WORKDIR /app

# Install application
COPY --from=wheel /app/dist/primeqa_orchestrator-*-py3-none-any.whl ./wheels/

# Install wheels
RUN pip install wheels/*.whl

# List packages
RUN pip list

# Set store location
ENV STORE_DIR=/store
RUN mkdir -p ${STORE_DIR} && chmod -R 777 ${STORE_DIR}

# Set default run command
CMD ["tini","run_orchestrator"]

# needed to mitigate CVE-2023-0361
RUN apt install libgnutls30>=3.7.1-5+deb11u3

# Change to application user
USER 2000
