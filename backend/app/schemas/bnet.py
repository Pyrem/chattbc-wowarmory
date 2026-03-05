from pydantic import BaseModel


class BNetAuthorizeResponse(BaseModel):
    authorize_url: str
    state: str


class BNetStatusResponse(BaseModel):
    linked: bool
    battletag: str | None = None
    characters_linked: int = 0


class BNetLinkedCharacterResponse(BaseModel):
    name: str
    realm: str
    class_name: str
    level: int
    faction: str
