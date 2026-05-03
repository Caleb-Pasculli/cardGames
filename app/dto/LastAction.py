from enum import Enum

from pydantic import BaseModel

class GameActionsEnum(Enum):
   QUEEN_SWAP="queen_swap"
   JACK_VIEW="jack_view"
   TEN_ADD="ten_add"
   WRONG_MATCH="wrong_match"
   CORRECT_MATCH="correct_match"

   PICKUP_DECK="pickup_deck"
   PICKUP_DISCARD="pickup_discard"
   DISCARD_HAND="discard_hand"
   DISCARD_PICK_UP="discard_pick_up"

   END_TURN="end_turn"


class LastActionDTO(BaseModel):
   action_type: GameActionsEnum # see action types below
   player_id: int #external id of the player
   player_name: str #name of the player
   
   target_player_1: int | None = None#external id of the player
   target_card_index_1: int | None = None

   # only used for queen actions
   target_player_2: int | None = None #external id of the player
   target_card_index_2: int | None = None