from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import CharacterNotFoundError, GuildNotFoundError
from app.routers import auth, health

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)


@app.exception_handler(CharacterNotFoundError)
async def character_not_found_handler(
    request: Request, exc: CharacterNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Character {exc.name} on {exc.realm} not found"},
    )


@app.exception_handler(GuildNotFoundError)
async def guild_not_found_handler(request: Request, exc: GuildNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Guild {exc.name} on {exc.realm} not found"},
    )
