FROM python:3.11-slim

WORKDIR /usr/src/app

RUN pip install --upgrade pip

COPY pyproject.toml poetry.lock README.md ./

RUN pip install poetry

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8000

CMD ["uvicorn", "webservice.app:app", "--host", "0.0.0.0", "--port", "8000"]
