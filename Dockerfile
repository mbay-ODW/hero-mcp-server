FROM python:3.12-slim
# Docker-Secrets: NAME_FILE=/run/secrets/... wird beim Start zu NAME geladen
COPY --chmod=0755 env-secrets.sh /usr/local/bin/env-secrets

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

ENV HERO_API_KEY=""
ENV MCP_TRANSPORT=sse
ENV MCP_API_KEY=""
ENV PORT=8000

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/env-secrets"]
CMD ["hero-mcp-server"]
