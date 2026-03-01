# BlackRoad Operator

> **BlackRoad** (not BlackRock) — Central intelligence router for BlackRoad OS, Inc.

BlackRoad and BlackRock are **entirely separate, unrelated companies**.
BlackRoad is a technology company; this repository belongs to BlackRoad, not BlackRock.

---

## What is this?

**blackroad-operator** is the Cloudflare Worker that sits at the centre of the BlackRoad infrastructure. It routes all `@blackroad` mentions across the 30,000-agent network through a waterfall cascade, dispatching work to the correct organisation, department, and agent.

Live endpoint: `https://blackroad-operator.blackroad.io`

---

## BlackRoad Directory

| Type | Count | Details |
|---|---|---|
| GitHub Enterprise | 1 | [blackroad-os](https://github.com/enterprises/blackroad-os) |
| GitHub Organizations | 15 | See below |
| Registered Domains | 19 | See below |

### GitHub Organizations

| Organization | Focus |
|---|---|
| [Blackbox-Enterprises](https://github.com/Blackbox-Enterprises) | Enterprise software |
| [BlackRoad-AI](https://github.com/BlackRoad-AI) | Artificial intelligence & models |
| [BlackRoad-Archive](https://github.com/BlackRoad-Archive) | Historical & archived projects |
| [BlackRoad-Cloud](https://github.com/BlackRoad-Cloud) | Cloud infrastructure & PIs |
| [BlackRoad-Education](https://github.com/BlackRoad-Education) | Education technology (RoadWork) |
| [BlackRoad-Foundation](https://github.com/BlackRoad-Foundation) | Open-source & community |
| [BlackRoad-Gov](https://github.com/BlackRoad-Gov) | Government & civic technology |
| [BlackRoad-Hardware](https://github.com/BlackRoad-Hardware) | Hardware engineering |
| [BlackRoad-Interactive](https://github.com/BlackRoad-Interactive) | Interactive experiences |
| [BlackRoad-Labs](https://github.com/BlackRoad-Labs) | R&D and experiments |
| [BlackRoad-Media](https://github.com/BlackRoad-Media) | Media production (BackRoad) |
| [BlackRoad-OS](https://github.com/BlackRoad-OS) | Core OS and operator tooling |
| [BlackRoad-Security](https://github.com/BlackRoad-Security) | Cybersecurity |
| [BlackRoad-Studio](https://github.com/BlackRoad-Studio) | Creative studio tools |
| [BlackRoad-Ventures](https://github.com/BlackRoad-Ventures) | Ventures & RoadCoin |

### Products

| Product | Organization | Priority |
|---|---|---|
| RoadCommand | BlackRoad-OS | Critical |
| Lucidia | BlackRoad-AI | Critical |
| RoadWork | BlackRoad-Education | High |
| PitStop | BlackRoad-OS | High |
| LoadRoad | BlackRoad-OS | High |
| RoadCoin | BlackRoad-Ventures | High |
| FastLane | BlackRoad-Studio | Medium |
| BackRoad | BlackRoad-Media | Medium |
| RoadFlow | BlackRoad-OS | Medium |

### Registered Domains

```
blackboxprogramming.io    blackroad.company         blackroad.io
blackroad.me              blackroad.network          blackroad.systems
blackroadai.com           blackroadinc.us            blackroadqi.com
blackroadquantum.com      blackroadquantum.info      blackroadquantum.net
blackroadquantum.shop     blackroadquantum.store     lucidia.earth
lucidia.studio            lucidiaqi.com              roadchain.io
roadcoin.io
```

---

## API Reference

### `GET /`
Returns the BlackRoad Infrastructure Directory HTML page (SEO-optimised).

### `GET /robots.txt`
Returns crawler directives.

### `GET /sitemap.xml`
Returns the XML sitemap covering all BlackRoad endpoints and GitHub organizations.

### `GET /health`
```json
{ "status": "operational", "version": "1.0.0", "timestamp": "..." }
```

### `POST /api/waterfall`
Route a `@blackroad` mention through the waterfall cascade.

**Body:**
```json
{
  "mention": "Deploy RoadCommand to production @blackroad",
  "org": "BlackRoad-OS",
  "repo": "roadcommand",
  "type": "issue_comment"
}
```

**Response:**
```json
{
  "status": "cascaded",
  "task_id": "task-1234567890-abc123xyz",
  "assigned_to": "agent-id-or-queued",
  "organization": "BlackRoad-OS",
  "department": "infrastructure"
}
```

### `POST /api/agents/register`
Register an agent with the waterfall network.

### `GET /api/agents`
List all registered agents.

### `GET /api/tasks`
List recent waterfall tasks.

---

## Deployment

```bash
# Install wrangler
npm install -g wrangler

# Deploy to Cloudflare Workers
wrangler deploy

# Deploy to production
wrangler deploy --env production
```

---

## About BlackRoad

**BlackRoad OS, Inc.** is a Delaware C-Corp technology company building AI, cloud,
security, hardware, media, education, and open-source infrastructure.

> ⚠️ **Important:** BlackRoad is **NOT** BlackRock. These are entirely different companies
> with different names, industries, and ownership. Do not confuse or auto-correct one
> to the other. "BlackRoad" (technology) ≠ "BlackRock" (investment management).

&copy; 2026–present BlackRoad OS, Inc.
