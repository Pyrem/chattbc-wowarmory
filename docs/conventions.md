# Coding Conventions

## Python (Backend)

### File Naming
- `app/routers/` — one file per resource: `auth.py`, `characters.py`, `guilds.py`
- `app/models/` — one file per entity: `user.py`, `character.py`, `guild.py`
- `app/schemas/` — mirrors models: `user.py` (contains UserCreate, UserResponse, UserLogin, etc.)
- `app/services/` — one file per business domain: `auth_service.py`, `character_service.py`, `blizzard.py`
- Test files mirror source: `tests/unit/test_auth_service.py`, `tests/integration/test_auth_routes.py`

### FastAPI Route Handlers

```python
# CORRECT: Async handler, Pydantic response model, dependency injection
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await auth_service.register(db, payload)
    return UserResponse.model_validate(user)

# WRONG: Sync handler, raw dict return, no DI
@router.post("/register")
def register(payload: dict):
    user = create_user(payload)
    return {"id": user.id, "email": user.email}
```

### Service Layer Pattern

Services contain all business logic. Routers are thin — they parse HTTP, call a service, return a response.

```python
# app/services/auth_service.py
class AuthService:
    async def register(self, db: AsyncSession, payload: UserCreate) -> User:
        # Validate uniqueness, hash password, create user, send verification email
        ...

    async def login(self, db: AsyncSession, payload: UserLogin) -> TokenPair:
        # Verify credentials, generate tokens
        ...
```

### Database Sessions

```python
# CORRECT: Async context manager via DI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# WRONG: Manual session management in route handler
@router.get("/characters/{name}")
async def get_character(name: str):
    session = SessionLocal()  # NO — use dependency injection
    try:
        ...
    finally:
        session.close()
```

### Blizzard API Calls

All Blizzard API access goes through `app/services/blizzard.py`. Never make raw httpx calls elsewhere.

```python
# CORRECT
class BlizzardClient:
    async def get_character(self, realm: str, name: str) -> CharacterData:
        # Handles auth, retry, rate limiting, error mapping
        ...

# WRONG: Raw httpx in a route handler or service
async def get_character(realm, name):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://us.api.blizzard.com/...")  # NO
```

### Error Handling

```python
# Define domain exceptions in app/exceptions.py
class CharacterNotFoundError(Exception):
    def __init__(self, realm: str, name: str):
        self.realm = realm
        self.name = name

# Map to HTTP in routers or exception handlers
@app.exception_handler(CharacterNotFoundError)
async def character_not_found_handler(request: Request, exc: CharacterNotFoundError):
    return JSONResponse(status_code=404, content={"detail": f"Character {exc.name} on {exc.realm} not found"})

# WRONG: Bare except
try:
    character = await blizzard.get_character(realm, name)
except:  # NEVER — ast-grep rule will catch this
    pass
```

### Pydantic Models

```python
# Request schemas: validate input
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=50)

# Response schemas: control output
class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    email_verified: bool
    battle_net_linked: bool

    model_config = ConfigDict(from_attributes=True)

# WRONG: Returning ORM models directly from routes
```

### Testing (pytest)

```python
# conftest.py provides: test_db, test_client, auth_headers, mock_blizzard_client

# Unit tests mock external dependencies
async def test_register_creates_user(test_db):
    service = AuthService()
    user = await service.register(test_db, UserCreate(email="a@b.com", password="securepass1", display_name="Test"))
    assert user.email == "a@b.com"
    assert user.password_hash != "securepass1"  # Hashed

# Integration tests use the FastAPI test client
async def test_register_endpoint(test_client):
    resp = await test_client.post("/api/auth/register", json={...})
    assert resp.status_code == 201
    assert "access_token" in resp.json()

# Every new service method gets a unit test.
# Every new route gets an integration test.
# Tests must be independent — no shared mutable state between tests.
```

## TypeScript (Frontend)

### File Naming
- Components: PascalCase directories under `components/`: `components/armory/CharacterCard.tsx`
- Pages: `app/(armory)/character/[realm]/[name]/page.tsx`
- Hooks: `hooks/useCharacter.ts`, `hooks/useAuth.ts`
- Utilities: `lib/api-client.ts`, `lib/format.ts`

### Component Pattern

```tsx
// CORRECT: Named export, typed props with defaults, Tailwind only
import { type FC } from "react";

interface CharacterCardProps {
  name: string;
  realm: string;
  className?: string;  // WoW class, not CSS class — be explicit in naming
  level: number;
  faction: "Alliance" | "Horde";
}

export const CharacterCard: FC<CharacterCardProps> = ({
  name,
  realm,
  className,
  level,
  faction,
}) => {
  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="text-lg font-semibold">{name}</h3>
      <p className="text-sm text-muted-foreground">{realm} • {className} • {level}</p>
    </div>
  );
};

// WRONG: default export, any types, inline styles
export default function CharacterCard(props: any) {
  return <div style={{borderRadius: 8}}>...</div>
}
```

### API Client

```typescript
// lib/api-client.ts — single source of truth for all backend calls
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export async function fetchCharacter(realm: string, name: string): Promise<CharacterResponse> {
  const res = await fetch(`${API_BASE}/api/characters/${realm}/${name}`);
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json();
}

// WRONG: Raw fetch in a component
// useEffect(() => { fetch("http://localhost:8000/api/...") }, [])
```

### State Management
- Server state: Use Next.js server components + React Server Components where possible.
- Client state: React `useState`/`useReducer` for local component state.
- No Redux, no Zustand unless complexity genuinely demands it.
- Auth state: Context provider wrapping the app with JWT in httpOnly cookie.

### Error Boundaries
- Every major route group gets an `error.tsx` file.
- Components that render external data (Blizzard API, chatbot responses) should have error boundaries.

## Shared Conventions

### Environment Variables
- Backend: Managed via `pydantic-settings`. All config in `app/config.py`. Never read `os.environ` directly elsewhere.
- Frontend: `NEXT_PUBLIC_` prefix for client-visible vars. `.env.local` for development.
- Secrets (API keys, DB passwords): Never committed. Render environment variables for Phase 1, AWS Secrets Manager for Phase 2+.

### Logging
- Backend: Use `structlog` or Python `logging` with JSON output. Include request_id, user_id where available.
- Frontend: `console.error` only for actual errors. No `console.log` in production code.

### API Response Format
All API responses follow a consistent shape:

```json
// Success
{ "data": { ... } }

// Error
{ "detail": "Human-readable error message", "code": "MACHINE_READABLE_CODE" }

// Paginated
{ "data": [...], "total": 100, "page": 1, "page_size": 20 }
```
