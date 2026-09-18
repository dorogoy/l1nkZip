FROM python:3.14-slim

# Pull in Debian security patches even when the official base tag has not
# been rebuilt after a Debian security release, and refresh the base Python
# tooling so scanners do not flag stale setuptools/msgpack shipped with it.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools msgpack

WORKDIR /code

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-install-project --no-dev

COPY ./l1nkzip /code/l1nkzip

CMD ["uv", "run", "uvicorn", "l1nkzip.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
