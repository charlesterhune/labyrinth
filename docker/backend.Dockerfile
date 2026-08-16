##########################################################
# FIRST BUILD AND TEST ALGOLIBS FOR THE SOLVER LIBRARIES
##########################################################
FROM gcc:15 AS algolibs-base

WORKDIR /usr/src/algolibs

RUN apt-get update && apt-get install -y \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY algolibs/solvers ./solvers
COPY algolibs/CMakeLists.txt .


##########################################################
# ALGOLIB TEST BUILD
##########################################################
FROM algolibs-base AS algolibs-test

COPY algolibs/test ./test
COPY algolibs/graphbuilder ./graphbuilder
COPY algolibs/CMakeLists.txt.gtest .

RUN mkdir build

RUN cmake -S. -Bbuild \
    -DCMAKE_BUILD_TYPE=RELEASE \
    -DBUILD_TESTS=ON \
    -DBUILD_BENCHMARKS=OFF

RUN cmake --build build

WORKDIR /usr/src/algolibs/build/test/

RUN ctest -V

WORKDIR /usr/src/algolibs


##########################################################
# ALGOLIB RELEASE BUILD
##########################################################
FROM algolibs-base AS algolibs-release

RUN mkdir build

RUN cmake -S. -Bbuild \
    -DCMAKE_BUILD_TYPE=RELEASE \
    -DBUILD_TESTS=OFF \
    -DBUILD_BENCHMARKS=OFF

RUN cmake --build build


##########################################################
# BASE PYTHON APPLICATION
##########################################################
FROM python:3.12 AS base

WORKDIR /app

# Copy backend source
COPY backend/labyrinth ./labyrinth
COPY backend/instance ./instance

# Copy compiled solver libraries
RUN rm -rf instance/lib \
    && mkdir -p instance/lib

COPY --from=algolibs-release \
    /usr/src/algolibs/build/solvers/*.so \
    instance/lib/


##########################################################
# DEVELOPMENT IMAGE
##########################################################
FROM base AS dev

COPY backend/dev-requirements.txt ./

RUN pip install \
    --no-cache-dir \
    --retries 10 \
    --timeout 60 \
    -r dev-requirements.txt


##########################################################
# LINT
##########################################################
FROM dev AS lint

RUN flake8 . \
    --count \
    --max-line-length=120 \
    --max-complexity=10 \
    --show-source \
    --statistics \
    --exclude __pycache__,venv


##########################################################
# TEST
##########################################################
FROM dev AS test

COPY backend/pytest.ini backend/conftest.py ./
COPY backend/tests ./tests

RUN pytest .


##########################################################
# PRODUCTION RELEASE
##########################################################
FROM base AS release

# Install uWSGI with retries
RUN pip install \
    --no-cache-dir \
    --retries 10 \
    --timeout 60 \
    uwsgi

# Install Python runtime dependencies
COPY backend/requirements.txt ./

RUN pip install \
    --no-cache-dir \
    --retries 10 \
    --timeout 60 \
    -r requirements.txt

# Copy production startup files
COPY backend/labyrinth_main.py ./
COPY backend/uwsgi-docker.ini ./

# Generate application secret
RUN python instance/create_secret.py >> instance/config.py


##########################################################
# PORTS / RUNTIME
##########################################################

# uWSGI socket
EXPOSE 9112

# HTTP API
EXPOSE 9113

ENV INTERNAL_URL="http://localhost:9113"

CMD ["uwsgi", "uwsgi-docker.ini"]