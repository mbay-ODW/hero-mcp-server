FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

ENV HERO_API_KEY=""

CMD ["hero-mcp-server"]
