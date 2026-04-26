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

## Lokale Installation (Claude Desktop)

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

## Docker-Deployment (Portainer)

Das Image wird bei jedem Push auf `main` automatisch über GitHub Actions gebaut und in der **GitHub Container Registry (ghcr.io)** veröffentlicht. Portainer kann es direkt von dort ziehen – kein manueller Build nötig.

### Image-URL

```
ghcr.io/your-github-user/hero-mcp-server:latest
```

### Deployment über Portainer (empfohlen)

1. In Portainer einloggen
2. **Stacks → Add Stack** öffnen
3. Stack-Name vergeben: `hero-mcp-server`
4. Folgenden Inhalt einfügen:

```yaml
services:
  hero-mcp-server:
    image: ghcr.io/your-github-user/hero-mcp-server:latest
    container_name: hero-mcp-server
    restart: unless-stopped
    environment:
      - HERO_API_KEY=dein_api_key_hier
    stdin_open: true
    tty: true
```

5. **Deploy the stack** klicken

> Das Image ist öffentlich über ghcr.io verfügbar – keine Authentifizierung beim Pull nötig.

### Mit Docker Compose starten (lokal)

```bash
export HERO_API_KEY=dein_api_key_hier
docker compose up -d
```

### Automatische Updates

Jeder Push auf `main` triggert den GitHub Actions Workflow (`.github/workflows/docker.yml`) und aktualisiert das Image auf `ghcr.io` automatisch. In Portainer kann man **"Re-pull image and redeploy"** nutzen, um das neueste Image zu holen.

---

## Projektstruktur

```
hero-mcp-server/
├── src/
│   └── hero_mcp_server/
│       ├── __init__.py
│       ├── server.py        # MCP-Server & Tool-Definitionen
│       └── client.py        # HERO API Client (REST + GraphQL)
├── .env.example             # Vorlage für API-Key
├── claude_desktop_config.json  # Beispiel-Konfiguration für Claude Desktop
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API-Referenz

- [HERO Lead API](https://hero-software.de/api-doku/lead-api)
- [HERO GraphQL Guide](https://hero-software.de/api-doku/graphql-guide)
- [MCP Protokoll Dokumentation](https://modelcontextprotocol.io)
