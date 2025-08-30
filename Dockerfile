FROM python:3.12-slim

WORKDIR /code

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-install-project --no-dev

COPY ./l1nkzip /code/l1nkzip

CMD ["uv", "run", "uvicorn", "l1nkzip.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
