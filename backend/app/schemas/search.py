from pydantic import BaseModel


class SearchResult(BaseModel):
    """A single search result (character or guild)."""

    type: str
    name: str
    realm: str
    url: str
    detail: str


class SearchResponse(BaseModel):
    """Search endpoint response."""

    results: list[SearchResult]
    query: str
    total: int
