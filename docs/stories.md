# Story Backlog

Jira project key: CTBC. Stories are organized by epic and phase. Points use Fibonacci (1, 2, 3, 5, 8, 13).

## Phase 1: MVP Armory

### CTBC-E1: Project Scaffolding & CI/CD (18 pts)

| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E1-S1 | Initialize monorepo structure | 3 | Directory structure, Makefile, docker-compose.yml (Postgres + Redis), .gitignore, README. | docker-compose up starts Postgres + Redis. Makefile targets work. |
| E1-S2 | Scaffold Next.js frontend | 3 | Next.js 14+ with App Router, TypeScript, Tailwind, shadcn/ui. Placeholder homepage. | npm run dev serves homepage. Tailwind renders. TS compiles. |
| E1-S3 | Scaffold FastAPI backend | 3 | FastAPI with pyproject.toml, pydantic-settings, health endpoint, async SQLAlchemy, Alembic init. | GET /health returns 200. Alembic generates migrations. pytest runs. |
| E1-S4 | CI pipeline (GitHub Actions) | 3 | Full quality chain on PR: Ruff + ESLint → mypy → ast-grep → Semgrep → pytest + Vitest. All blocking. | PR triggers CI. Any failure blocks merge. Fast-fail ordering. |
| E1-S5 | Render deployment | 2 | render.yaml Blueprint. Frontend + backend as separate services. Render Postgres. | Push to main deploys. Health endpoint responds on prod URL. |
| E1-S6 | Code quality toolchain setup | 5 | Configure Ruff, mypy, ESLint, Prettier, ast-grep, Semgrep. Initial ast-grep rules + Semgrep custom rules. Pre-commit hooks. Makefile targets. | make quality passes on scaffold. Pre-commit hooks fire. Rules catch test violations. |

### CTBC-E2: Email Authentication (21 pts)

| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E2-S1 | User model + migration | 2 | SQLAlchemy User model (see docs/data-models.md). Alembic migration. | Migration runs. Model queryable via fixture. |
| E2-S2 | Registration endpoint | 3 | POST /api/auth/register. Email, password, display_name. Bcrypt hash. Returns JWT. | Unique email enforced. Password hashed. JWT returned. Dup = 409. |
| E2-S3 | Login endpoint | 2 | POST /api/auth/login. Returns JWT access + refresh tokens. | Valid creds → tokens. Invalid → 401. Rate limited 5/min. |
| E2-S4 | JWT middleware + refresh | 3 | Auth dependency for protected routes. Short-lived access (15min) + refresh (7d). | Protected routes 401 without token. Refresh works. Invalid refresh → 401. |
| E2-S5 | Email verification | 3 | Verification email on register. Confirm endpoint. Resend endpoint. | Token works. email_verified flips. Expired token → error. |
| E2-S6 | Password reset | 3 | Forgot password sends email. Reset endpoint accepts token + new password. | Email sent. Token time-limited. Password updates. |
| E2-S7 | Frontend auth pages | 3 | Login, Register, Forgot Password, Reset Password pages with form validation. | Forms submit. Validation inline. Auth state persists. |
| E2-S8 | Auth E2E tests | 2 | Playwright tests for register, login, logout, password reset. | All flows pass headless. Happy path + errors covered. |

### CTBC-E3: Blizzard API Integration Layer (21 pts)

| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E3-S1 | Blizzard API client | 5 | Async httpx client. Client Credentials auth + auto-refresh. Retry with backoff. | Auth works. Token refreshes. 429 triggers retry. |
| E3-S2 | Cache service layer | 5 | Stale-while-revalidate. Redis-backed. Per-key TTLs. Background refresh. Redis failure fallback. | Stale served instantly. Background refresh works. TTLs configurable. Graceful Redis failure. |
| E3-S3 | Character data model + migration | 3 | Character + CharacterSnapshot models (see docs/data-models.md). | Migration runs. JSON fields serialize/deserialize. |
| E3-S4 | Guild data model + migration | 2 | Guild model with progression_json. | Migration runs. Guild data queryable. |
| E3-S5 | Character fetch + cache pipeline | 3 | Fetch from Blizzard → cache in Redis (2-day TTL) → persist snapshot to DB. | First req hits API. Second serves cache. Snapshot persisted. |
| E3-S6 | Guild fetch + cache pipeline | 2 | Same pattern for guild data. | Guild cached and persisted. |
| E3-S7 | Unit tests | 3 | Mocked httpx. Test token refresh, retry, cache hit/miss/stale, Redis down. | All cache scenarios covered. |

### CTBC-E4: Character Lookup & Display (21 pts)

| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E4-S1 | Character API endpoints | 3 | GET /api/characters/{realm}/{name}. Triggers cache pipeline. | Full data returned. Cache hit fast. 404 for unknown. |
| E4-S2 | Character profile page (SSR) | 5 | /character/[realm]/[name]. SSR. Name, level, class, race, faction, guild. | Renders with data. SEO meta tags. Loading state. |
| E4-S3 | Gear display component | 5 | Visual gear layout, 16+ slots, item tooltips, quality colors. | All slots rendered. Quality colors. Tooltips show details. |
| E4-S4 | Talent tree display | 3 | TBC 41-point talent trees. Active spec highlighted. | Points shown per tree. Correct names. |
| E4-S5 | Arena & PvP section | 2 | 2v2, 3v3, 5v5 ratings, team names, HKs. | Ratings displayed. Missing data handled. |
| E4-S6 | Reputation display | 2 | Faction rep bars with standings. | All reps shown. Color-coded. |
| E4-S7 | Character lookup E2E | 1 | Playwright: search → verify profile loads. | E2E passes. |

### CTBC-E5: Guild Pages (11 pts)

| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E5-S1 | Guild API endpoints | 2 | GET /api/guilds/{realm}/{name}. | Returns guild + roster. |
| E5-S2 | Guild profile page (SSR) | 3 | /guild/[realm]/[name]. Name, faction, members, progression. | Renders. SSR. Meta tags. |
| E5-S3 | Guild roster component | 3 | Sortable member list. Click-through to character. | Sort works. Links work. |
| E5-S4 | Guild progression display | 2 | Raid progression per instance. | Per-raid display. Boss kills correct. |
| E5-S5 | Guild E2E | 1 | Playwright: guild page, roster, progression. | E2E passes. |

### CTBC-E6: Search & Navigation (8 pts)

| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E6-S1 | Search API | 3 | GET /api/search?q=...&type=character\|guild. | Results returned. Filters work. Partial match. |
| E6-S2 | Search UI + autocomplete | 3 | Header search bar. Debounced autocomplete. | Results after 2+ chars. 300ms debounce. Click navigates. |
| E6-S3 | Realm browser | 2 | Realm list with type, population, region. | Realms listed. Filterable. |

### CTBC-E7: Battle.net OAuth Linking (14 pts)

| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E7-S1 | OAuth endpoints | 5 | Authorize redirect + callback. Requires auth session. | Redirect works. Code exchanged. bnet_id stored. CSRF validated. |
| E7-S2 | Character ownership sync | 3 | Fetch char list from Profile API. Set character.user_id. | Characters linked. Multi-char supported. Unlink works. |
| E7-S3 | Profile settings UI | 3 | Settings page. Link/unlink button. Verified characters list. | Link initiates OAuth. Characters shown. Unlink works. |
| E7-S4 | Verified badge | 1 | "Verified Owner" badge on character pages. | Badge for owner only. |
| E7-S5 | Linking E2E | 2 | Playwright with mocked Blizzard OAuth. | E2E passes. |

## Phase 2: AI Chatbot

### CTBC-E8: Bedrock Agent Setup (19 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E8-S1 | CDK stack | 5 | Bedrock Agent + Claude model + action group skeletons + IAM. | cdk deploy creates agent. Agent responds to basic prompt. |
| E8-S2 | CharacterLookup Lambda | 3 | Queries character cache/DB. | Returns data. Handles not-found. |
| E8-S3 | Agent instruction prompt | 3 | TBC context, abbreviation dict, tool routing. | Agent interprets TBC terms. Routes to correct tools. |
| E8-S4 | FastAPI Bedrock integration | 5 | boto3 InvokeAgent. Session mgmt. Streaming. | Invoke + stream works. Session maintained. |
| E8-S5 | Agent integration tests | 3 | Mocked Bedrock + optional live test. | Unit tests pass. |

### CTBC-E9: Chatbot UI (15 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E9-S1 | Chat window component | 5 | Expandable panel. Message input. Streaming display. | Open/close. Send/receive. Streaming renders. |
| E9-S2 | WebSocket connection | 3 | WS to /ws/chat. Reconnection. Auth token. | Connects. Round-trips. Reconnects. |
| E9-S3 | Tool result rendering | 5 | Inline components for structured tool results. | Character cards, graph previews render inline. |
| E9-S4 | Session management | 2 | Per-session history. New conversation. Persists across nav. | History preserved. Clear works. |

### CTBC-E10: Attunement Graph Tool (24 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E10-S1 | Attunement DAG data model | 3 | Tables + seed script from attunements.json. | Seeded. All chains queryable. |
| E10-S2 | Attunement progress service | 5 | Traverse DAG, find next steps for a character. | Correct next steps. Handles complete + zero-progress. |
| E10-S3 | AttunementProgress Lambda | 3 | Agent action group. Structured output. | Callable by agent. Correct data. |
| E10-S4 | React Flow graph component | 8 | Interactive graph. Green/gold/gray nodes. Zoom/pan. | All attunements rendered. Colors correct. Interactive. |
| E10-S5 | Standalone attunement page | 3 | /attunement. Character selector for linked users. Generic view. | Renders. Selector works. Generic available. |
| E10-S6 | Attunement E2E | 2 | Playwright: chatbot → attunement → graph renders. | E2E passes. |

### CTBC-E11: Remaining Agent Action Groups (14 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E11-S1 | GuildInfo Lambda | 3 | Roster, progression, recruitment. | Agent answers guild queries. |
| E11-S2 | ReputationGuide Lambda | 3 | Rep advice based on character standings. | Phase-appropriate recommendations. |
| E11-S3 | GearAdvisor Lambda | 5 | Phase-aware BiS from curated data. | Correct BiS. Sources cited. |
| E11-S4 | Cost tracking + Langfuse | 3 | Token, latency, tool call traces. | Traces visible. Counts accurate. |

## Phase 3: Community & Advanced

### CTBC-E12: Guild Recruitment (13 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E12-S1 | Recruitment data model | 2 | Table + migration. | CRUD works. |
| E12-S2 | Recruitment API | 5 | CRUD. Officer check (BNet linked). Filters. | Officer enforced. Filters correct. |
| E12-S3 | Recruitment board UI | 3 | Browse/filter cards. | Posts displayed. Filters work. |
| E12-S4 | Chatbot recruitment search | 3 | Natural language guild search. | "guilds needing holy paladin on Faerlina" works. |

### CTBC-E13: Profession Board (8 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E13-S1 | Profession model + API | 3 | CRUD. Verified character required. | Verified enforced. Searchable. |
| E13-S2 | Profession board UI | 3 | Browse by realm. Filter by profession/recipe. | Filters work. |
| E13-S3 | Chatbot profession search | 2 | "find leatherworker with Drums of Battle on Benediction" | Returns matches. |

### CTBC-E14: LFG & Trade Channels (22 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E14-S1 | LFG/Trade data models | 2 | Tables with expires_at. | Expiry queryable. |
| E14-S2 | Posting API + cleanup | 5 | CRUD + background expiry job. | TTL works. Cleanup runs. |
| E14-S3 | LFG board UI | 5 | Browse, filter, near-realtime. | Filters work. New posts appear. |
| E14-S4 | Trade board UI | 3 | Browse, filter by profession/service. | Filters work. |
| E14-S5 | NLP-powered LFG matching | 5 | Structured + optional pgvector semantic. | "warlock for Friday Kara" returns matches. |
| E14-S6 | LFG E2E | 2 | Post → chatbot search → match. | Full flow passes. |

### CTBC-E15: Warcraft Logs Integration (13 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E15-S1 | WCL API client | 5 | v2 GraphQL client. | Fetches reports. Rate limits understood. |
| E15-S2 | Log linking model + API | 3 | Link reports to verified characters. | Metrics extracted. Verification works. |
| E15-S3 | Performance display | 3 | Parse percentiles on character page. | Metrics shown. Color-coded. |
| E15-S4 | Top performer identification | 2 | Top 10% arena, highest parsers. | Correct players. Thresholds configurable. |

### CTBC-E16: Community Voting & Expert Sourcing (14 pts)
| ID | Title | Points | Description | Acceptance Criteria |
|----|-------|--------|-------------|-------------------|
| E16-S1 | Polls model + API | 3 | CRUD. One vote/user/poll. | Dup vote prevented. |
| E16-S2 | Polls UI + charts | 3 | Create, vote, Recharts results. | Real-time chart updates. |
| E16-S3 | Expert sourcing pipeline | 5 | Surface top player input contextually. | Experts identified. Opt-in. |
| E16-S4 | Community dashboard | 3 | Aggregate charts. | Charts from real data. |

## Execution Order

Start with E1 (scaffolding), then work E2 (auth) and E3 (Blizzard API) in parallel. E4-E7 depend on E3 and/or E2. Phase 2 begins after Phase 1 ships. Phase 3 after Phase 2 chatbot is functional.

```
E1 ──→ E2 (auth) ──────→ E7 (BNet linking) ──→ E12, E13 (community)
  └──→ E3 (Blizzard) ──→ E4 (characters) ──→ E6 (search)
                    └──→ E5 (guilds) ──────→ E6
                    └──→ E8 (Bedrock) ──→ E9 (chat UI) ──→ E10, E11 (tools)
                                                      └──→ E14 (LFG/trade)
E7 + E15 (WCL) → E16 (voting/experts)
```
