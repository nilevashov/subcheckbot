FROM python:3.10-slim

WORKDIR /subchecker_app

ENV POETRY_VERSION=1.8.2
ENV PYTHONUNBUFFERED=1
ENV EXEC_ENV=docker

RUN pip install --no-cache-dir poetry==$POETRY_VERSION

COPY src/ /subchecker_app
COPY poetry.lock pyproject.toml /subchecker_app
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

ENTRYPOINT ["/entrypoint.sh"]
