"""HERO API client – REST Lead API + GraphQL."""

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


async def graphql_query(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
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
