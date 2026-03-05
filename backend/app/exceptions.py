class CharacterNotFoundError(Exception):
    def __init__(self, realm: str, name: str) -> None:
        self.realm = realm
        self.name = name
        super().__init__(f"Character {name} on {realm} not found")


class GuildNotFoundError(Exception):
    def __init__(self, realm: str, name: str) -> None:
        self.realm = realm
        self.name = name
        super().__init__(f"Guild {name} on {realm} not found")


class BlizzardApiUnavailableError(Exception):
    pass
