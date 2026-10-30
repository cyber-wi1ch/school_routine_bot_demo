FROM python:3.13-slim AS poetry

WORKDIR /app

ENV PYTHONUNBUFFERED=true \
    POETRY_VERSION=2.1.3 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update && apt-get -y upgrade && apt-get -y install git
RUN pip install poetry==${POETRY_VERSION} && poetry self add "poetry-dynamic-versioning[plugin]"

COPY pyproject.toml poetry.lock poetry.toml ./
RUN poetry install --only main --no-plugins --no-root --no-interaction --no-ansi -vv

COPY school_routine_bot/ ./school_routine_bot
COPY README.md ./
RUN poetry install --only-root --no-plugins --no-interaction --no-ansi

FROM python:3.13-slim AS runtime

ENV TZ=Europe/Moscow
WORKDIR /app

COPY --from=poetry /app/.venv /app/.venv
COPY --from=poetry /app/school_routine_bot /app/school_routine_bot

CMD [ ".venv/bin/python", "-m", "school_routine_bot" ]
