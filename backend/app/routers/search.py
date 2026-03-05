from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.search import SearchResponse
from app.services.search_service import search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search_endpoint(
    q: str = Query(min_length=2, max_length=100, description="Search query"),
    result_type: str | None = Query(
        default=None,
        alias="type",
        pattern="^(character|guild)$",
        description="Filter by type",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Search characters and guilds by name."""
    results = await search(q, db, result_type=result_type)
    return {
        "results": results,
        "query": q,
        "total": len(results),
    }
