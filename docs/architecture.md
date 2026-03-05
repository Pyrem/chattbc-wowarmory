# Architecture

## Overview

chattbc.gg is a TBC-era WoW armory + community platform shipping in 3 phases:
1. **Phase 1 (MVP):** Armory website — character/guild lookup, email auth, Blizzard API integration. Deployed to Render.
2. **Phase 2:** AI chatbot powered by AWS Bedrock Agents with TBC-specific tools (attunement guide, gear advisor, etc.).
3. **Phase 3:** Community features — guild recruitment, profession board, LFG/trade channels, Warcraft Logs, voting.

The long-term vision positions the chatbot as the homepage's central interface.

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Next.js 14+, React, TypeScript | App Router. SSR for armory pages (SEO). Client components for chatbot + interactive tools. |
| Styling | Tailwind CSS + shadcn/ui | No CSS modules. No styled-components. |
| Interactive Viz | React Flow (attunement graph), Recharts (charts) | |
| Backend API | Python 3.12+, FastAPI | Async-native. Pydantic for schemas. SQLAlchemy for ORM. |
| Auth (Primary) | Email/password, bcrypt, JWT | All users register with email. Access token (15min) + refresh token (7d). |
| Auth (Optional) | Battle.net OAuth 2.0 (Auth Code flow) | Confidential client. Server-side secret. For character ownership verification only. |
| Blizzard Data API | Client Credentials (separate developer key) | Server-side only. Fetches all armory data. Not tied to user sessions. |
| Database | PostgreSQL (Render → Aurora Serverless v2) | Alembic for migrations. Async SQLAlchemy sessions. |
| Cache | Redis (Render → ElastiCache) | Stale-while-revalidate. Data retained indefinitely. TTLs trigger re-fetch only. |
| AI Model | Claude via AWS Bedrock | Managed model access. Haiku for simple lookups, Sonnet for complex queries. |
| Agent Orchestration | AWS Bedrock Agents | Action groups backed by Lambda functions. |
| LLM Observability | Langfuse | Trace all agent invocations, tool calls, token usage. |
| Structural Analysis | ast-grep | Custom rules in `rules/`. Enforced in CI. |
| Security Scanning | Semgrep | OWASP + custom rules in `.semgrep/`. Enforced in CI. |
| Python Quality | Ruff (lint/format) + mypy (strict) + pytest | |
| TS Quality | ESLint + Prettier + Vitest | |
| E2E Testing | Playwright (Python) | Full user flow tests. |
| Deployment (MVP) | Render | Frontend + backend as separate Web Services. Render Postgres. |
| Deployment (Full) | AWS (ECS, Aurora, ElastiCache, Lambda) | Phase 2+ migration path. |
| CDN / DNS | Cloudflare | |
| CI/CD | GitHub Actions | Full quality chain on every PR. All checks blocking. |

## Authentication Architecture

### Three Separate Concerns

1. **Email Auth (Primary):** All users register with email + password. Bcrypt hashing. JWT access token (short-lived, 15min) + refresh token (httpOnly cookie, 7d). Email verification required. Password reset via email.

2. **Battle.net OAuth Linking (Optional):** Authenticated users can link their Battle.net account from their profile settings. Uses a separate Blizzard OAuth client (Authorization Code flow, confidential — secret stays server-side). Linking proves character ownership, enabling: guild officer privileges, verified profession listings, Warcraft Logs linking. Users without linking can still browse armory, use chatbot, post in LFG (flagged unverified).

3. **Blizzard Developer API Key (Server-Side):** A completely separate Client Credentials key used only for fetching armory data (characters, guilds, arena ladders). Lives only on the server. Never associated with any user session. This is what populates the entire armory.

### Auth Flow Summary

```
Registration:  email + password → bcrypt hash → JWT issued → email verification sent
Login:         email + password → verify hash → JWT access + refresh tokens
BNet Linking:  (must be logged in) → redirect to Blizzard OAuth → callback → store bnet_id + fetch characters → link to user
API Data:      server → Client Credentials token → Blizzard API → cache → DB (no user involvement)
```

## Caching & Data Retention

Data fetched from Blizzard is **retained indefinitely**. TTLs indicate staleness, not deletion.

| Data Type | Stale After | Notes |
|-----------|-------------|-------|
| Character stats/gear | 2 days | Background refresh on next access after TTL |
| Guild rosters | 2 days | |
| Static game data | Until patch | Items, spells, quests |
| Arena ladder snapshots | 6 hours | 4 snapshots/day |
| Battle.net OAuth tokens | Token expiry - buffer | Per-user, only for linked accounts |

Pattern: Serve cached data immediately → check TTL → if stale, trigger async background refresh → update cache + persist new snapshot to DB. Old snapshots kept for progression history.

## Bedrock Agent Architecture (Phase 2)

The chatbot is a Bedrock Agent with Claude as the foundation model. Action groups map to Lambda functions:

| Action Group | Lambda | What It Does |
|-------------|--------|-------------|
| CharacterLookup | chattbc-character-lookup | Query cached character data. Returns gear, stats, talents, ratings. |
| AttunementProgress | chattbc-attunement | Traverse attunement DAG for a character. Return next available steps. |
| GuildInfo | chattbc-guild-info | Guild roster, progression, recruitment status. |
| LFGSearch | chattbc-lfg-search | Structured + semantic search against LFG postings. |
| TradeSearch | chattbc-trade-search | Search profession services and crafting availability. |
| ReputationGuide | chattbc-rep-guide | Contextual rep advice based on character standings. |
| GearAdvisor | chattbc-gear-advisor | Phase-aware BiS recommendations from curated static data. |

Request flow: User message → FastAPI WebSocket → Bedrock InvokeAgent → Agent decides tools → Lambda executes → Response streams back → Frontend renders (text + inline tool result components).

## Attunement Graph

TBC attunements modeled as a directed acyclic graph (DAG). Stored in `shared/tbc_data/attunements.json` and seeded into `attunement_graph` table.

Chains: Karazhan, Serpentshrine Cavern, Tempest Keep (The Eye), Mount Hyjal, Black Temple.

Each node = quest, dungeon completion, reputation threshold, or key item. Edges = prerequisites. Per-character completion tracked in `character_attunements` table.

Frontend renders with React Flow: green (complete), gold (available next), gray (locked).

## Infrastructure Topology

### Phase 1 (Render)
```
Cloudflare CDN/DNS
    ↓
Render Web Service (Next.js frontend)
    ↓
Render Web Service (FastAPI backend)
    ↓
Render Postgres ←→ Render Redis (optional, can use in-memory cache for MVP)
    ↓
Blizzard API (Client Credentials)
```

### Phase 2+ (Render + AWS)
```
Cloudflare CDN/DNS
    ↓
Render Web Service (Next.js frontend)
    ↓
Render Web Service (FastAPI backend) ──→ AWS Bedrock Agent
    ↓                                       ↓
Aurora Serverless v2 ←──────── Lambda Action Groups
    ↓
ElastiCache Redis
    ↓
Blizzard API (Client Credentials)
```
