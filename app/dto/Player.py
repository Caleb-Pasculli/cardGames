from pydantic import BaseModel

from app.dto.Card import CardDTO


class PlayerDTO(BaseModel):
    name: str
    player_index: int
    hand: list[CardDTO]
    picked_up_card: CardDTO | None


class OpponentDTO(BaseModel):
    name: str
    player_index: int
    hand: list[CardDTO]
