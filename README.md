# HERO MCP Server

MCP-Server (Model Context Protocol) für die [HERO Handwerkersoftware](https://hero-software.de). Ermöglicht KI-Assistenten wie Claude den direkten Zugriff auf Kontakte, Projekte, Dokumente und Kalender in HERO.

## Features

| Tool | Beschreibung |
|------|-------------|
| `hero_create_project` | Neues Projekt via Lead API anlegen |
| `hero_get_contacts` | Kontakte/Kunden abfragen & suchen |
| `hero_get_projects` | Projekte auflisten & suchen |
| `hero_get_documents` | Dokumente (Angebote, Rechnungen) abrufen |
| `hero_get_calendar_events` | Kalendertermine abrufen |
| `hero_create_contact` | Neuen Kontakt erstellen |
| `hero_add_logbook_entry` | Protokolleintrag zu Projekt hinzufügen |
| `hero_graphql` | Direkte GraphQL-Abfrage (Experten-Tool) |

## API-Key beantragen

Den API-Key erhältst du kostenlos beim HERO Support: [hero-software.de/api-doku](https://hero-software.de/api-doku)

---

## Transport-Modi

| Modus | Einsatz | Env-Variable |
|-------|---------|--------------|
| `stdio` | Claude Desktop (lokal, kein Netzwerk) | `MCP_TRANSPORT=stdio` (Standard) |
| `sse` | claude.ai im Browser, Remote via HTTPS | `MCP_TRANSPORT=sse` |

---

## Option A: Lokal mit Claude Desktop (stdio)

Einfachster und sicherster Weg. Claude Desktop startet den Server als lokalen Prozess – keine offenen Ports, kein Netzwerkzugriff.

### Voraussetzungen

- Python 3.11+
- [Claude Desktop](https://claude.ai/download)

### 1. Repository klonen

```bash
git clone https://github.com/your-github-user/hero-mcp-server.git
cd hero-mcp-server
```

### 2. Abhängigkeiten installieren

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. API-Key konfigurieren

```bash
cp .env.example .env
# HERO_API_KEY in .env eintragen
```

### 4. Claude Desktop konfigurieren

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hero": {
      "command": "/absoluter/pfad/zum/hero-mcp-server/.venv/bin/hero-mcp-server",
      "env": {
        "HERO_API_KEY": "dein_hero_api_key"
      }
    }
  }
}
```

### 5. Claude Desktop neu starten

Der HERO-Server erscheint automatisch unter den verfügbaren Tools.

---

## Option B: Docker + Traefik + Authelia OAuth (claude.ai im Browser)

Für den Einsatz mit claude.ai im Browser. Authentifizierung erfolgt über **Authelia OIDC OAuth** – kein Token in der URL nötig.

### Voraussetzungen

- Docker + Portainer
- Traefik als Reverse Proxy
- Authelia als OIDC-Provider mit konfiguriertem OAuth-Client

### Authelia: OIDC-Client anlegen

In der Authelia-Konfiguration (`configuration.yml`) einen Client für Claude hinzufügen:

```yaml
identity_providers:
  oidc:
    clients:
      - client_id: claude-mcp
        client_secret: 'dein_client_secret_hash'  # bcrypt-Hash
        authorization_policy: one_factor
        redirect_uris:
          - https://claude.ai/api/mcp/auth_callback
        scopes:
          - openid
          - profile
          - email
        grant_types:
          - authorization_code
        response_types:
          - code
        token_endpoint_auth_method: client_secret_post
```

### Portainer Stack

**Stacks → Add Stack**, dann folgenden Inhalt einfügen:

```yaml
services:
  hero-mcp-server:
    build:
      context: https://github.com/your-github-user/hero-mcp-server.git
      dockerfile: Dockerfile
    container_name: hero-mcp-server
    restart: unless-stopped
    environment:
      - HERO_API_KEY=dein_hero_api_key
      - MCP_TRANSPORT=sse
      - MCP_API_KEY=dein_statischer_fallback_token   # optional, für Claude Desktop im SSE-Modus
      - PORT=8000
      - OIDC_INTROSPECTION_URL=http://authelia:9091/api/oidc/introspection
      - OIDC_CLIENT_ID=claude-mcp
      - OIDC_CLIENT_SECRET=dein_client_secret_plaintext
    expose:
      - "8000"
    labels:
      - traefik.enable=true
      - traefik.docker.network=traefik
      - traefik.http.routers.hero-mcp.rule=Host(`hero-mcp.deine-domain.de`)
      - traefik.http.routers.hero-mcp.entrypoints=websecure
      - traefik.http.services.hero-mcp.loadbalancer.server.port=8000
      - traefik.http.routers.hero-mcp.tls.certresolver=mydnschallenge
      - traefik.http.routers.hero-mcp.tls=true
      # Kein middlewares-authelia@file – Authelia-ForwardAuth ist für Browser-Sessions,
      # nicht für Bearer-Token. JWT-Validierung läuft direkt im Server via Introspection.
      - traefik.http.routers.hero-mcp.middlewares=middlewares-rate-limit@file,middlewares-secure-headers@file
    networks:
      - traefik   # Authelia muss im selben Netzwerk erreichbar sein

networks:
  traefik:
    external: true
```

### claude.ai Connector einrichten

In claude.ai → **Settings → Integrations → Add custom connector**:

- **Name:** `Hero`
- **URL:** `https://hero-mcp.deine-domain.de/sse`
- **OAuth Client ID:** `claude-mcp`
- **OAuth Client Secret:** `dein_client_secret_plaintext`

Claude.ai übernimmt den kompletten OAuth-Flow mit Authelia automatisch.

### Automatische Updates

GitHub Actions baut bei jedem Push auf `main` ein neues Image. In Portainer **"Update the stack"** klicken, um die neueste Version zu laden.

---

## Authentifizierung: Wie es funktioniert

### claude.ai (Browser) via OAuth

```
claude.ai → OAuth-Flow → Authelia → JWT Access Token
         → Bearer {JWT} → Traefik → hero-mcp-server
                                   → OIDC Introspection → Authelia
                                   → active: true → Zugriff erlaubt
```

### Claude Desktop (lokal)

```
Claude Desktop → startet Prozess lokal (stdio) → kein Netzwerk
```

### Claude Desktop im SSE-Modus (optional)

```
Claude Desktop → Bearer {MCP_API_KEY} → Traefik → hero-mcp-server → Zugriff erlaubt
```

---

## Sicherheit

| Maßnahme | Beschreibung |
|----------|-------------|
| HTTPS/TLS | Traefik mit Let's Encrypt |
| Authelia OIDC OAuth | Industrie-Standard, kein Token in der URL |
| JWT Introspection | Server validiert jeden Token live gegen Authelia |
| Rate Limiting | Traefik-Middleware verhindert Brute-Force |
| Secure Headers | HSTS, X-Frame-Options etc. via Traefik |
| HERO API Key | Nur in Container-Umgebung, nie im Image/Repo |

### Warum kein `middlewares-authelia@file` im Traefik-Label?

Authelias ForwardAuth-Middleware ist für **Browser-Sessions (Cookies)** ausgelegt. Claude.ai sendet nach dem OAuth-Flow einen **Bearer JWT Access Token** – den kennt ForwardAuth nicht und blockt mit 401. Die JWT-Validierung erfolgt daher direkt im Server via Token Introspection gegen Authelias OIDC-Endpunkt.

---

## Projektstruktur

```
hero-mcp-server/
├── src/
│   └── hero_mcp_server/
│       ├── __init__.py
│       ├── server.py        # MCP-Server, Tools & SSE/OAuth-Transport
│       └── client.py        # HERO API Client (REST Lead API + GraphQL)
├── .github/
│   └── workflows/
│       └── docker.yml       # Automatischer Docker-Build via GitHub Actions
├── .env.example
├── claude_desktop_config.json
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API-Referenz

- [HERO Lead API](https://hero-software.de/api-doku/lead-api)
- [HERO GraphQL Guide](https://hero-software.de/api-doku/graphql-guide)
- [MCP Protokoll Dokumentation](https://modelcontextprotocol.io)
- [Authelia OIDC Konfiguration](https://www.authelia.com/configuration/identity-providers/openid-connect/provider/)
