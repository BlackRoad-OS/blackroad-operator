# 🛣️ BlackRoad Operator

> **The Central Routing Layer** - Routes requests to the right tool at the right time.

## Core Thesis

BlackRoad is a **routing company, not an AI company.** We don't train models or buy GPUs. We connect users to intelligence that already exists through this orchestration layer.

## Architecture

```
[User Request] → [Operator] → [Route to Right Tool] → [Answer]
                     │
                     ├── Physics question? → NumPy/SciPy
                     ├── Language task? → Claude/GPT API
                     ├── Customer lookup? → Salesforce API
                     ├── Legal question? → Legal database
                     └── Fast inference? → Hailo-8 local
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn operator.main:app --reload --port 8000

# Or with Docker
docker build -t blackroad-operator .
docker run -p 8000:8000 blackroad-operator
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /route` | Main routing endpoint - analyzes request and routes to best provider |
| `POST /chat` | Direct chat interface with automatic provider selection |
| `GET /providers` | List available providers and their status |
| `GET /health` | Health check for all connected services |
| `POST /physics/{operation}` | Physics calculations (NumPy/SciPy) |
| `POST /language/{task}` | Language tasks (Claude/GPT) |
| `POST /data/{operation}` | Data operations (Salesforce/DB) |

## Provider Registry

The Operator maintains a registry of available providers:

- **Claude** - Anthropic's Claude API (primary language model)
- **GPT** - OpenAI's GPT API (fallback)
- **NumPy** - Local numerical computations
- **SciPy** - Scientific computing
- **Salesforce** - CRM data access
- **Hailo** - Local edge inference (26 TOPS)

## Configuration

```yaml
# config.yaml
providers:
  claude:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-20250514
    priority: 1
  gpt:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
    priority: 2
  hailo:
    endpoint: http://octavia.local:8080
    priority: 0  # Fastest for edge inference
```

## Routing Logic

The Operator uses keyword matching and intent classification to route requests:

1. **Intent Detection** - Classify the type of request
2. **Provider Selection** - Choose the best provider based on:
   - Request type (physics, language, data)
   - Provider availability
   - Cost optimization
   - Latency requirements
3. **Execution** - Forward to selected provider
4. **Logging** - Audit trail for all operations

## Deployment

### Cloudflare Workers
```bash
wrangler deploy
```

### Railway
```bash
railway up
```

### Pi Cluster
```bash
ssh alice.local "cd /opt/blackroad-operator && docker-compose up -d"
```

## License

BlackRoad OS, Inc. - Proprietary
