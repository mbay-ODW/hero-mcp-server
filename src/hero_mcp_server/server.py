"""HERO MCP Server – MCP-Tools für die HERO Handwerkersoftware."""

import json
import logging
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

import os

_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)

from .client import file_upload_rest, graphql_query  # noqa: E402

server = Server(
    "hero-mcp-server",
    instructions=(
        "MCP-Server für die HERO Handwerkersoftware (login.hero-software.de).\n\n"
        "Wichtige Hinweise zur Tool-Auswahl:\n"
        "- Datei-Uploads an Projekte: IMMER `hero_upload_document` verwenden – das ist ein "
        "einziger Aufruf, der intern den zweistufigen REST+GraphQL-Flow abwickelt. "
        "NICHT `hero_graphql` benutzen um den Upload manuell nachzubauen.\n"
        "- Projekte anlegen: `hero_create_project` (ruft die create_project_match-Mutation auf, "
        "benötigt customer_id + measure_id).\n"
        "- Kontakte anlegen: `hero_create_contact`.\n"
        "- Beliebige Queries/Mutations für Spezialfälle: `hero_graphql` als Fallback."
    ),
)


# ---------------------------------------------------------------------------
# Tool-Definitionen
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="hero_create_project",
            description=(
                "Legt ein neues Projekt in HERO an via create_project_match-Mutation. "
                "Benötigt customer_id und measure_id (IDs aus hero_get_contacts bzw. der API). "
                "Tipp: customer_id aus hero_get_contacts beziehen, measure_id über hero_graphql abfragen."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "ID des Kunden/Kontakts (nicht contact_id!)",
                    },
                    "measure_id": {
                        "type": "string",
                        "description": "ID des Gewerks (z.B. via hero_graphql: { measures { id name } })",
                    },
                    "name": {
                        "type": "string",
                        "description": "Projektname (optional)",
                    },
                    "type_id": {
                        "type": "string",
                        "description": "Projekttyp-ID (optional)",
                    },
                    "address_id": {
                        "type": "string",
                        "description": "Adress-ID für das Projekt (optional)",
                    },
                },
                "required": ["customer_id", "measure_id"],
            },
        ),
        types.Tool(
            name="hero_get_contacts",
            description="Listet Kontakte/Kunden aus HERO. Optional: Suchbegriff und Seitenanzahl.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Suchbegriff (Name, E-Mail, …)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Anzahl Ergebnisse",
                    },
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="hero_get_projects",
            description="Listet Projekte aus HERO. Optional: Suchbegriff und Seitenanzahl.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="hero_get_documents",
            description="Listet Dokumente (Angebote, Rechnungen, …) aus HERO.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="hero_get_calendar_events",
            description="Listet Termine aus dem HERO-Kalender.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="hero_create_contact",
            description="Erstellt einen neuen Kontakt in HERO.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "company_name": {"type": "string"},
                    "phone_home": {"type": "string", "description": "Festnetz"},
                    "phone_mobile": {"type": "string", "description": "Mobilnummer"},
                    "street": {"type": "string"},
                    "city": {"type": "string"},
                    "zipcode": {"type": "string"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="hero_add_logbook_entry",
            description="Fügt einen Protokoll-Eintrag zu einem HERO-Projekt hinzu.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID des Projekts"},
                    "message": {"type": "string", "description": "Protokoll-Text"},
                },
                "required": ["project_id", "message"],
            },
        ),
        types.Tool(
            name="hero_upload_document",
            description=(
                "Lädt eine Datei in die Dokumentenablage eines HERO-Projekts hoch. "
                "Dies ist EIN einziger Tool-Aufruf – nicht hero_graphql separat verwenden! "
                "Der Server erledigt intern automatisch beide HERO-API-Schritte: "
                "(1) REST-Upload an /app/v8/FileUploads/upload (x-auth-token Header), "
                "(2) GraphQL-Mutation upload_document mit der zurückgelieferten UUID. "
                "Verwende dieses Tool für JEDE Datei (PDF, Bild, etc.) die einem Projekt "
                "(project_match) angehängt werden soll. Andere Tools sind nicht nötig."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": (
                            "ID des HERO-Projekts (project_match.id, z.B. '10295003'). "
                            "Bekommt man via hero_get_projects."
                        ),
                    },
                    "filename": {
                        "type": "string",
                        "description": "Dateiname inklusive Erweiterung, z.B. 'angebot.pdf'",
                    },
                    "content_type": {
                        "type": "string",
                        "description": "MIME-Typ der Datei, z.B. 'application/pdf' oder 'image/jpeg'",
                    },
                    "data_base64": {
                        "type": "string",
                        "description": (
                            "Vollständiger Dateiinhalt als base64-kodierter String. "
                            "Bei Datei-Anhängen aus einem Chat-Kontext: den base64-Inhalt "
                            "der Originaldatei direkt durchreichen."
                        ),
                    },
                },
                "required": ["project_id", "filename", "content_type", "data_base64"],
            },
        ),
        types.Tool(
            name="hero_graphql",
            description=(
                "Führt eine beliebige GraphQL-Abfrage direkt gegen die HERO API aus. "
                "Für Experten und individuelle Abfragen."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "GraphQL Query oder Mutation",
                    },
                    "variables": {
                        "type": "object",
                        "description": "Optionale GraphQL-Variablen",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool-Handler
# ---------------------------------------------------------------------------


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
    except Exception as exc:
        result = {"error": str(exc)}
    return [
        types.TextContent(
            type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def _dispatch(name: str, args: dict[str, Any]) -> Any:
    if name == "hero_create_project":
        return await _create_project(args)
    if name == "hero_get_contacts":
        return await _get_contacts(args)
    if name == "hero_get_projects":
        return await _get_projects(args)
    if name == "hero_get_documents":
        return await _get_documents(args)
    if name == "hero_get_calendar_events":
        return await _get_calendar_events(args)
    if name == "hero_create_contact":
        return await _create_contact(args)
    if name == "hero_add_logbook_entry":
        return await _add_logbook_entry(args)
    if name == "hero_upload_document":
        return await _upload_document(args)
    if name == "hero_graphql":
        return await graphql_query(args["query"], args.get("variables"))
    raise ValueError(f"Unbekanntes Tool: {name}")


# ---------------------------------------------------------------------------
# Einzelne Implementierungen
# ---------------------------------------------------------------------------


async def _create_project(args: dict[str, Any]) -> dict[str, Any]:
    project_match_input: dict[str, Any] = {
        "customer_id": args["customer_id"],
        "measure_id": args["measure_id"],
    }
    for field in ("name", "type_id", "address_id"):
        if args.get(field):
            project_match_input[field] = args[field]

    query = """
    mutation CreateProjectMatch($project_match: ProjectMatchInput!) {
      create_project_match(project_match: $project_match) {
        id
        name
        project_nr
        display_id
      }
    }
    """
    return await graphql_query(query, {"project_match": project_match_input})


async def _get_contacts(args: dict[str, Any]) -> dict[str, Any]:
    query = """
    query GetContacts($limit: Int, $offset: Int) {
      contacts(first: $limit, offset: $offset) {
        id
        nr
        first_name
        last_name
        email
        phone_home
        phone_mobile
        company_name
        address {
          street
          city
          zipcode
        }
      }
    }
    """
    variables = {
        "limit": args.get("limit", 20),
        "offset": args.get("offset", 0),
    }
    return await graphql_query(query, variables)


async def _get_projects(args: dict[str, Any]) -> dict[str, Any]:
    query = """
    query GetProjects($limit: Int, $offset: Int) {
      project_matches(first: $limit, offset: $offset) {
        id
        name
        project_nr
        display_id
        measure { name }
        current_project_match_status { name }
        contact {
          first_name
          last_name
          email
          company_name
        }
        address {
          street
          city
          zipcode
        }
      }
    }
    """
    variables = {
        "limit": args.get("limit", 20),
        "offset": args.get("offset", 0),
    }
    return await graphql_query(query, variables)


async def _get_documents(args: dict[str, Any]) -> dict[str, Any]:
    query = """
    query GetDocuments($limit: Int, $offset: Int) {
      customer_documents(first: $limit, offset: $offset) {
        id
        nr
        date
        created
        type
        document_type { name }
        status_code
        status_name
        value
        vat
        currency
      }
    }
    """
    variables = {
        "limit": args.get("limit", 20),
        "offset": args.get("offset", 0),
    }
    return await graphql_query(query, variables)


async def _get_calendar_events(args: dict[str, Any]) -> dict[str, Any]:
    query = """
    query GetCalendarEvents($limit: Int, $offset: Int) {
      calendar_events(first: $limit, offset: $offset) {
        id
        title
        start_at
        end_at
        description
      }
    }
    """
    variables = {
        "limit": args.get("limit", 20),
        "offset": args.get("offset", 0),
    }
    return await graphql_query(query, variables)


async def _create_contact(args: dict[str, Any]) -> dict[str, Any]:
    contact_input: dict[str, Any] = {"email": args["email"]}
    for field in (
        "first_name",
        "last_name",
        "company_name",
        "phone_home",
        "phone_mobile",
    ):
        if args.get(field):
            contact_input[field] = args[field]
    if any(args.get(k) for k in ("street", "city", "zipcode")):
        contact_input["address"] = {
            "street": args.get("street", ""),
            "city": args.get("city", ""),
            "zipcode": args.get("zipcode", ""),
        }

    query = """
    mutation CreateContact($contact: ContactInput!) {
      create_contact(contact: $contact) {
        id
        nr
        email
        first_name
        last_name
      }
    }
    """
    return await graphql_query(query, {"contact": contact_input})


async def _add_logbook_entry(args: dict[str, Any]) -> dict[str, Any]:
    query = """
    mutation AddLogbookEntry($project_id: ID!, $message: String!) {
      add_logbook_entry(project_id: $project_id, message: $message) {
        id
        created_at
        message
      }
    }
    """
    return await graphql_query(
        query,
        {
            "project_id": args["project_id"],
            "message": args["message"],
        },
    )


async def _upload_document(args: dict[str, Any]) -> dict[str, Any]:
    """Two-step upload to HERO:

    1. POST file as multipart/form-data to /api/external/v1/file-uploads
       → returns {uuid, id}
    2. GraphQL mutation upload_document with file_upload_uuid + project_match_id
    """
    import base64

    file_data = base64.b64decode(args["data_base64"])

    # Step 1: REST file upload
    upload_resp = await file_upload_rest(
        filename=args["filename"],
        content_type=args["content_type"],
        file_data=file_data,
    )
    uuid = upload_resp.get("uuid")
    if not uuid:
        raise RuntimeError(f"file-uploads response missing 'uuid' field: {upload_resp}")

    # Step 2: attach uploaded file to project via GraphQL
    project_id = int(args["project_id"])
    mutation = """
    mutation UploadDocument($uuid: String!, $projectId: Int!) {
      upload_document(
        document: { project_match_id: $projectId, type: "file_upload" }
        file_upload_uuid: $uuid
        target: project_match
        target_id: $projectId
      ) {
        id
        nr
        type
      }
    }
    """
    return await graphql_query(
        mutation,
        {"uuid": uuid, "projectId": project_id},
    )


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------


def main() -> None:
    import asyncio
    import os

    if os.getenv("MCP_TRANSPORT", "stdio") == "sse":
        _run_sse()
    else:
        asyncio.run(mcp.server.stdio.run_server(server))


def _run_sse() -> None:
    import os
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Mount, Route

    import httpx as _httpx

    mcp_api_key = os.getenv("MCP_API_KEY", "")
    oidc_introspection_url = os.getenv("OIDC_INTROSPECTION_URL", "")
    oidc_client_id = os.getenv("OIDC_CLIENT_ID", "")
    oidc_client_secret = os.getenv("OIDC_CLIENT_SECRET", "")

    # Auth-Reihenfolge:
    # 1. Bearer {MCP_API_KEY}  → Claude Desktop / direkte API-Clients
    # 2. Bearer {JWT}          → Claude.ai via Authelia OIDC (Token Introspection)

    # Auth result: (ok, reason). `reason` is one of:
    #   None           – ok, no error
    #   "no_header"    – initial auth needed (no Bearer presented)
    #   "invalid_token" – token present but invalid/expired/wrong scheme;
    #                    triggers the OAuth refresh-token flow on the client
    async def _is_authorized(request: Request) -> tuple[bool, str | None]:
        logging.debug("Auth-Check: %s %s", request.method, request.url.path)
        if not mcp_api_key:
            logging.debug("Kein MCP_API_KEY konfiguriert – Auth übersprungen")
            return True, None

        auth = request.headers.get("Authorization", "")
        logging.debug(
            "Authorization-Header: %s",
            auth[:30] + "…" if len(auth) > 30 else auth or "(leer)",
        )

        if not auth:
            logging.warning(
                "Auth ABGELEHNT (no_header) für %s %s", request.method, request.url.path
            )
            return False, "no_header"

        # 1. Statischer Bearer Token (Claude Desktop)
        if auth == f"Bearer {mcp_api_key}":
            logging.info("Auth OK: statischer Bearer Token")
            return True, None

        if not auth.startswith("Bearer "):
            logging.warning(
                "Auth ABGELEHNT (wrong scheme) für %s %s",
                request.method,
                request.url.path,
            )
            return False, "invalid_token"

        # 2. JWT via Authelia OIDC Token Introspection (Claude.ai)
        if oidc_introspection_url and oidc_client_id and oidc_client_secret:
            jwt_token = auth[7:]
            logging.info(
                "JWT erhalten, starte Introspection gegen %s", oidc_introspection_url
            )
            try:
                async with _httpx.AsyncClient() as http:
                    resp = await http.post(
                        oidc_introspection_url,
                        data={"token": jwt_token},
                        auth=(oidc_client_id, oidc_client_secret),
                        timeout=5.0,
                    )
                    data = resp.json()
                    active = data.get("active", False)
                    logging.info(
                        "Introspection: HTTP %s, active=%s", resp.status_code, active
                    )
                    logging.debug("Introspection Response: %s", data)
                    if active:
                        return True, None
                    return False, "invalid_token"
            except Exception as e:
                logging.error("Introspection fehlgeschlagen: %s", e)
                return False, "invalid_token"
        else:
            logging.warning(
                "JWT empfangen aber OIDC nicht konfiguriert (OIDC_INTROSPECTION_URL fehlt?)"
            )
            return False, "invalid_token"

    def _unauthorized(reason: str | None) -> Response:
        """Build a proper 401.

        RFC 6750 §3: a `Bearer error="invalid_token"` challenge tells the
        OAuth client that its current token is no longer valid and that
        it should run the refresh-token flow before re-prompting the
        user. Without this header, Claude.ai cannot distinguish "token
        expired" from "no auth at all" and falls back to a full
        reconnect.

        However: when no Authorization header was sent at all, we
        deliberately omit WWW-Authenticate. Claude.ai's default OAuth
        discovery flow (which fetches /.well-known/oauth-authorization-
        server etc.) only kicks in when the 401 is a "naked" challenge
        without a Bearer realm hint. Sending `WWW-Authenticate: Bearer
        realm="…"` here makes the client treat the resource as plain
        Basic-Bearer and the discovery flow never runs.
        """
        if reason == "invalid_token":
            www = (
                'Bearer realm="hero-mcp", error="invalid_token", '
                'error_description="The access token expired or is invalid"'
            )
            return Response(
                "Unauthorized",
                status_code=401,
                headers={"WWW-Authenticate": www},
            )
        # no_header (or unknown) → no WWW-Authenticate, let the client
        # fall back to OAuth discovery as before.
        return Response("Unauthorized", status_code=401)

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        logging.debug("SSE-Verbindung eingehend von %s", request.client)
        ok, reason = await _is_authorized(request)
        if not ok:
            logging.warning("SSE abgewiesen – nicht autorisiert (%s)", reason)
            return _unauthorized(reason)
        logging.info("SSE-Verbindung akzeptiert")
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
        # Must return Response() – otherwise Starlette calls None() on disconnect
        # and logs "Exception in ASGI application" (MCP SDK ≥ 1.6 requirement)
        return Response()

    # Streamable-HTTP transport (current MCP spec). Modern Claude.ai sends
    # JSON-RPC over POST /sse (or POST /mcp) and expects STATEFUL session
    # handling – i.e. one `initialize` then many `tools/call` requests
    # sharing the same Mcp-Session-Id. A per-request stateless transport
    # rejects the second call with "Received request before
    # initialization was complete", which is what previously broke every
    # connector after the very first round-trip.
    #
    # StreamableHTTPSessionManager owns the long-lived task group and
    # session map. It must be entered exactly once per app via
    # `async with manager.run():` in a Starlette lifespan context.
    import contextlib
    from collections.abc import AsyncIterator

    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    class _AlreadySent(Response):
        """No-op response. Used when the underlying handler has already
        streamed a complete HTTP response via the raw ASGI `send` callable
        (e.g. StreamableHTTPSessionManager.handle_request). Returning a
        normal Response from a Starlette endpoint would make Starlette
        try to send a *second* response and raise:
            RuntimeError: Unexpected ASGI message 'http.response.start'
            sent, after response already completed.
        """

        def __init__(self) -> None:
            super().__init__(content=b"", status_code=200)

        async def __call__(self, scope, receive, send):  # noqa: D401
            return  # response was already written by the inner handler

    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=True,
    )

    async def handle_streamable_http(request: Request):
        ok, reason = await _is_authorized(request)
        if not ok:
            logging.warning(
                "Streamable-HTTP abgewiesen – nicht autorisiert (%s) reason=%s",
                request.url.path,
                reason,
            )
            return _unauthorized(reason)
        logging.debug(
            "Streamable-HTTP request eingehend (%s) von %s",
            request.url.path,
            request.client,
        )
        await session_manager.handle_request(
            request.scope, request.receive, request._send
        )
        return _AlreadySent()

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logging.info("StreamableHTTPSessionManager started")
            yield
            logging.info("StreamableHTTPSessionManager stopping")

    app = Starlette(
        routes=[
            # Streamable-HTTP (current spec) – Claude.ai uses this first.
            Route("/sse", endpoint=handle_streamable_http, methods=["POST"]),
            Route("/mcp", endpoint=handle_streamable_http, methods=["POST"]),
            # Classic SSE (Claude Desktop / older clients).
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
