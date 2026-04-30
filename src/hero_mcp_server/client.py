"""HERO API client – REST Lead API + GraphQL."""

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

LEAD_API_URL = "https://login.hero-software.de/api/v1/Projects/create"
GRAPHQL_URL = "https://login.hero-software.de/api/external/v7/graphql"


def _headers() -> dict[str, str]:
    api_key = os.getenv("HERO_API_KEY")
    if not api_key:
        raise ValueError("HERO_API_KEY ist nicht gesetzt. Bitte .env konfigurieren.")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def create_project_lead(payload: dict[str, Any]) -> dict[str, Any]:
    """Erstellt ein neues Projekt über die HERO Lead API."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(LEAD_API_URL, json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def graphql_query(
    query: str, variables: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Führt eine GraphQL-Abfrage gegen die HERO API aus."""
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GRAPHQL_URL, json=payload, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL Fehler: {data['errors']}")
        return data.get("data", {})


async def graphql_upload(
    query: str,
    variables: dict[str, Any],
    file_var_name: str,
    filename: str,
    content_type: str,
    file_data: bytes,
) -> dict[str, Any]:
    """GraphQL multipart file upload (graphql-multipart-request-spec).

    Builds the three-part multipart body required by servers that implement
    https://github.com/jaydenseric/graphql-multipart-request-spec:
      - operations: JSON {query, variables}  (file variable set to null)
      - map:        JSON {"0": ["variables.<file_var_name>"]}
      - 0:          actual file binary
    """
    # The file variable must be null in the operations JSON
    variables = {**variables, file_var_name: None}
    operations = json.dumps({"query": query, "variables": variables})
    map_ = json.dumps({"0": [f"variables.{file_var_name}"]})

    headers = _headers()
    # Remove Content-Type so httpx sets the correct multipart/form-data boundary
    headers.pop("Content-Type", None)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            GRAPHQL_URL,
            data={"operations": operations, "map": map_},
            files={"0": (filename, file_data, content_type)},
            headers=headers,
        )
        resp.raise_for_status()
        resp_data = resp.json()
        if "errors" in resp_data:
            raise RuntimeError(f"GraphQL Fehler: {resp_data['errors']}")
        return resp_data.get("data", {})
