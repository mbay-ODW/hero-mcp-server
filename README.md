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

Der Server unterstützt zwei Betriebsmodi:

| Modus | Einsatz | Umgebungsvariable |
|-------|---------|-------------------|
| `stdio` | Claude Desktop (lokal) | `MCP_TRANSPORT=stdio` (Standard) |
| `sse` | claude.ai im Browser, Remote-Zugriff via HTTPS | `MCP_TRANSPORT=sse` |

---

## Option A: Lokale Installation (Claude Desktop)

Der einfachste und sicherste Weg. Claude Desktop startet den Server als lokalen Prozess – kein Netzwerkzugriff, keine offenen Ports.

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
```

`.env` öffnen und den API-Key eintragen:

```env
HERO_API_KEY=dein_api_key_hier
```

### 4. Claude Desktop konfigurieren

Datei öffnen:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Folgenden Block in `mcpServers` eintragen (Pfad anpassen):

```json
{
  "mcpServers": {
    "hero": {
      "command": "/absoluter/pfad/zum/hero-mcp-server/.venv/bin/hero-mcp-server",
      "env": {
        "HERO_API_KEY": "dein_api_key_hier"
      }
    }
  }
}
```

### 5. Claude Desktop neu starten

Der HERO-Server erscheint nun in Claude unter den verfügbaren Tools.

---

## Option B: Docker + Traefik (claude.ai im Browser)

Für den Einsatz mit claude.ai im Browser muss der Server via HTTPS erreichbar sein. Der Server wechselt dann in den SSE-Modus und wird über Traefik exponiert.

### Wie es funktioniert

```
claude.ai → HTTPS → Traefik → hero-mcp-server (SSE)
```

Die Authentifizierung erfolgt über ein **Secret-Token im URL-Pfad**:

```
https://deine-domain.de/t/{MCP_API_KEY}/sse
```

Nur wer die vollständige URL kennt, kann den Server ansprechen. Zusätzlich wird der Bearer-Token-Header unterstützt (für API-Clients und Claude Desktop im SSE-Modus).

### Portainer Stack

1. In Portainer: **Stacks → Add Stack**
2. Stack-Name: `hero-mcp-server`
3. Folgenden Inhalt einfügen und Werte anpassen:

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
      - MCP_API_KEY=langesZufaelligesPasswort123   # Secret-Token für die URL
      - PORT=8000
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
      - traefik.http.routers.hero-mcp.middlewares=middlewares-rate-limit@file,middlewares-secure-headers@file
    networks:
      - traefik

networks:
  traefik:
    external: true
```

4. **Deploy the stack** klicken

> Docker baut das Image direkt aus dem öffentlichen GitHub-Repo – kein Registry-Login nötig.

### claude.ai Connector einrichten

In claude.ai → **Settings → Integrations → Add custom connector**:

- **Name:** `Hero`
- **URL:** `https://hero-mcp.deine-domain.de/t/langesZufaelligesPasswort123/sse`

Kein OAuth nötig – der Token steckt in der URL.

### Automatische Updates

Jeder Push auf `main` triggert GitHub Actions und baut das Image neu. In Portainer **"Update the stack"** klicken, um das neueste Image zu laden.

---

## Sicherheit

### Aktive Schutzmaßnahmen

| Maßnahme | Beschreibung |
|----------|-------------|
| HTTPS/TLS | Traefik mit Let's Encrypt – Verbindung ist verschlüsselt |
| Secret-Token im Pfad | Ohne Token keine Antwort (401) |
| Bearer Token Header | Zusätzliche Auth-Option für API-Clients |
| Rate Limiting | Traefik-Middleware verhindert Brute-Force |
| Secure Headers | HSTS, X-Frame-Options etc. via Traefik |

### Warum kein IP-Whitelisting?

Da claude.ai von Anthropics Servern aus verbindet, würde ein lokales IP-Whitelist den Dienst für claude.ai blockieren. Für reine Claude Desktop Nutzung empfiehlt sich stattdessen **Option A (stdio)** – dort gibt es überhaupt keine Netzwerkexposition.

### Bewusste Entscheidungen

- **Kein Authelia** – Authelia zeigt eine Login-Seite, mit der claude.ai nicht umgehen kann
- **Kein OAuth** – für einen persönlichen Server unnötiger Aufwand; Token-im-Pfad bietet gleichwertigen Schutz
- **HERO API Key** – liegt nur in der Container-Umgebung, nie im Image oder Repository

---

## Projektstruktur

```
hero-mcp-server/
├── src/
│   └── hero_mcp_server/
│       ├── __init__.py
│       ├── server.py        # MCP-Server, Tool-Definitionen & SSE-Transport
│       └── client.py        # HERO API Client (REST + GraphQL)
├── .github/
│   └── workflows/
│       └── docker.yml       # Automatischer Docker-Build via GitHub Actions
├── .env.example             # Vorlage für API-Keys
├── claude_desktop_config.json  # Beispiel-Konfiguration für Claude Desktop
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API-Referenz

- [HERO Lead API](https://hero-software.de/api-doku/lead-api)
- [HERO GraphQL Guide](https://hero-software.de/api-doku/graphql-guide)
- [MCP Protokoll Dokumentation](https://modelcontextprotocol.io)
