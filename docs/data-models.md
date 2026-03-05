# Data Models

All models use SQLAlchemy async ORM with Alembic migrations. PostgreSQL is the database.

## Core Tables

### users
The primary account table. Email auth is the baseline. Battle.net fields are nullable and only populated when a user opts to link.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK, auto-increment | |
| email | String(255) | UNIQUE, NOT NULL | Login identifier |
| password_hash | String(255) | NOT NULL | bcrypt or argon2id |
| display_name | String(50) | NOT NULL | Shown on posts, chat |
| email_verified | Boolean | NOT NULL, default False | Flipped via email confirmation |
| battle_net_id | Integer | NULLABLE, UNIQUE | Set when user links Battle.net |
| battletag | String(100) | NULLABLE | e.g., "Player#1234" |
| created_at | DateTime | NOT NULL, default utcnow | |
| last_login | DateTime | NULLABLE | Updated on each login |

### characters
Character records exist independently of users. Most are created by developer API fetches. `user_id` is set only for Battle.net-linked users who own the character.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| user_id | Integer | FK(users.id), NULLABLE | Only set for verified owners |
| name | String(50) | NOT NULL | |
| realm | String(100) | NOT NULL | |
| class_ | String(30) | NOT NULL | "class" is reserved — use `class_` in Python, `class` in DB column name |
| race | String(30) | NOT NULL | |
| level | Integer | NOT NULL | |
| faction | String(10) | NOT NULL | "Alliance" or "Horde" |
| guild_name | String(100) | NULLABLE | Denormalized for quick display |
| last_synced | DateTime | NOT NULL | When data was last fetched from Blizzard |

**UNIQUE constraint:** (name, realm) — one character per name per realm.

### character_snapshots
Historical snapshots of character state. A new snapshot is created each time data is refreshed from Blizzard. Never deleted — provides free progression tracking.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| character_id | Integer | FK(characters.id), NOT NULL | |
| gear_json | JSONB | NOT NULL | Equipped items with enchants, gems |
| talents_json | JSONB | NOT NULL | Talent tree allocation |
| stats_json | JSONB | NOT NULL | Character stats (str, agi, stamina, etc.) |
| arena_json | JSONB | NULLABLE | 2v2, 3v3, 5v5 ratings + team names |
| reputation_json | JSONB | NULLABLE | Faction standings |
| snapshot_at | DateTime | NOT NULL | When this snapshot was taken |

**Index:** (character_id, snapshot_at DESC) — for fetching latest snapshot.

### guilds

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| name | String(100) | NOT NULL | |
| realm | String(100) | NOT NULL | |
| faction | String(10) | NOT NULL | |
| member_count | Integer | NULLABLE | |
| progression_json | JSONB | NULLABLE | Raid boss kills per instance |
| last_synced | DateTime | NOT NULL | |

**UNIQUE constraint:** (name, realm)

## Attunement Tables

### attunement_graph
Static DAG definition. Seeded from `shared/tbc_data/attunements.json`. Rows are not modified at runtime.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| node_name | String(200) | NOT NULL, UNIQUE | e.g., "The Arcatraz Key" |
| node_type | String(30) | NOT NULL | "quest", "dungeon", "reputation", "key_item", "raid" |
| raid_target | String(50) | NULLABLE | Which raid this attunes for: "karazhan", "ssc", "tk", "hyjal", "bt" |
| description | Text | NULLABLE | Human-readable description of the step |
| prerequisites_json | JSONB | NOT NULL, default [] | Array of attunement_graph.id values |

### character_attunements
Per-character completion tracking.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| character_id | Integer | FK(characters.id), NOT NULL | |
| node_id | Integer | FK(attunement_graph.id), NOT NULL | |
| completed | Boolean | NOT NULL, default False | |
| completed_at | DateTime | NULLABLE | |

**UNIQUE constraint:** (character_id, node_id)

## Community Tables

### recruitment_posts

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| guild_id | Integer | FK(guilds.id), NOT NULL | |
| posted_by | Integer | FK(users.id), NOT NULL | Must be Battle.net-linked guild officer |
| classes_needed | JSONB | NOT NULL | Array of class strings |
| raid_schedule | String(500) | NULLABLE | Free text: "Tue/Thu 8-11pm EST" |
| description | Text | NOT NULL | |
| active | Boolean | NOT NULL, default True | Manual deactivation by poster |
| created_at | DateTime | NOT NULL | |

### profession_listings

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| character_id | Integer | FK(characters.id), NOT NULL | Must be verified owner |
| profession | String(50) | NOT NULL | e.g., "Leatherworking", "Enchanting" |
| skill_level | Integer | NOT NULL | 1-375 |
| notable_recipes_json | JSONB | NULLABLE | Array of recipe names the player can craft |
| available | Boolean | NOT NULL, default True | |
| realm | String(100) | NOT NULL | Denormalized for filtering |

### lfg_postings

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| character_id | Integer | FK(characters.id), NULLABLE | Nullable for unverified users |
| user_id | Integer | FK(users.id), NOT NULL | |
| content_type | String(50) | NOT NULL | "karazhan", "heroic_shattered_halls", "arena_2v2", etc. |
| role | String(20) | NOT NULL | "tank", "healer", "dps" |
| class_ | String(30) | NULLABLE | |
| availability_json | JSONB | NULLABLE | Structured availability windows |
| description | Text | NULLABLE | Free text |
| expires_at | DateTime | NOT NULL | Auto-calculated from configurable TTL |
| created_at | DateTime | NOT NULL | |

**Index:** (expires_at) — for cleanup job. **Index:** (content_type, role, expires_at) — for filtered queries.

### trade_postings

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | Integer | PK | |
| character_id | Integer | FK(characters.id), NULLABLE | |
| user_id | Integer | FK(users.id), NOT NULL | |
| service_type | String(50) | NOT NULL | "crafting", "enchanting", "boosting", etc. |
| description | Text | NOT NULL | |
| price_note | String(200) | NULLABLE | "Free with mats", "50g tip", etc. |
| expires_at | DateTime | NOT NULL | |
| created_at | DateTime | NOT NULL | |

## Future Tables (Phase 3)

### community_polls

| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK |
| question | Text | Poll question |
| options_json | JSONB | Array of option strings |
| created_by | Integer | FK(users.id) |
| created_at | DateTime | |
| closes_at | DateTime | NULLABLE — open-ended if null |

### poll_votes

| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK |
| poll_id | Integer | FK(community_polls.id) |
| user_id | Integer | FK(users.id) |
| selected_option | Integer | Index into options_json array |
| voted_at | DateTime | |

**UNIQUE constraint:** (poll_id, user_id) — one vote per user per poll.

### warcraft_logs_links

| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK |
| character_id | Integer | FK(characters.id) — must be verified owner |
| log_url | String(500) | WCL report URL |
| report_id | String(100) | WCL report ID for API queries |
| verified | Boolean | Whether character in log matches verified owner |
| uploaded_at | DateTime | |

### performance_metrics

| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK |
| character_id | Integer | FK(characters.id) |
| metric_type | String(50) | "parse_percentile", "arena_rating", "dps_ranking" |
| value | Float | The metric value |
| context_json | JSONB | e.g., {"raid": "ssc", "boss": "vashj", "spec": "fire"} |
| recorded_at | DateTime | |

## Migration Conventions

- One migration per model change. Name format: `YYYYMMDD_HHMM_description.py`
- Always include both `upgrade()` and `downgrade()`.
- Never modify a migration after it has been applied to any environment.
- Test migrations against a fresh database AND against the current schema.
