FROM python:3.9.5-alpine@sha256:f189f7366b0d381bf6186b2a2c3d37f143c587e0da2e8dcc21a732bddf4e6f7b
ENV POETRY_HOME=/opt/poetry \
    PIP_DISABLE_PIP_VERSION_CHECK=yes \
    PIP_NO_CACHE_DIR=yes
ENV PATH="${POETRY_HOME}/bin:${PATH}"

poetry:
  ARG POETRY_REF=1.1.6
  RUN mkdir -p "${POETRY_HOME}" \
   && wget -q -O- "https://raw.githubusercontent.com/python-poetry/poetry/${POETRY_REF}/get-poetry.py" \
    | python -

  WORKDIR /work
  COPY poetry.lock pyproject.toml ./
  RUN apk add --no-cache \
        g++ \
        gcc \
        libffi-dev \
        libjpeg-turbo-dev \
        libxml2-dev \
        libxslt-dev \
        musl-dev \
        py3-lxml \
        qpdf-dev \
        zlib-dev \
   && poetry install

project:
  FROM +poetry
  COPY pdf_crypt.py ./

check:
  FROM +project
  RUN poetry run black --check .

dist:
  FROM +project
  RUN poetry run pyinstaller pdf_crypt.py -w --onefile
  SAVE ARTIFACT dist/
