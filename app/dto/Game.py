from enum import Enum

from pydantic import BaseModel

from app.dto.Card import CardDTO
from app.dto.LastAction import LastActionDTO
from app.dto.Player import OpponentDTO, PlayerDTO


class GameStatusEnum(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class GameDTO(BaseModel):
    game_id: str
    status: str
    max_players: int
    current_turn: int
    can_match: bool
    can_pickup: bool
    can_discard: bool

    special_card_active: str | None
    top_of_discard_pile: CardDTO | None

    player: PlayerDTO
    opponents: list[OpponentDTO]

    dutch_called_by: int | None
    turns_remaining: int | None

    last_action: LastActionDTO | None
    action_count: int
