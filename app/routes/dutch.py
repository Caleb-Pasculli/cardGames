from pydantic import BaseModel, Field
import random
import string
import uuid

from fastapi import Body
from fastapi import APIRouter, HTTPException


from app.dto.Card import CardDTO
from app.dto.Game import GameDTO
from app.dto.Player import OpponentDTO, PlayerDTO
from app.services.dutch_game_logic import (
    Game,
    Player,
    call_dutch_logic,
    create_deck,
    determine_scores,
    discard_from_hand,
    discard_pick_up_card,
    end_viewing,
    jack_played,
    match,
    pick_up_from_deck,
    pick_up_from_discard,
    play_10,
    queen_played,
    start_game_logic,
)

router = APIRouter(prefix="/dutch")

games: dict[str, Game] = {}


class CreateGameRequest(BaseModel):
    max_players: int = Field(ge=2, le=4)
    name: str


@router.post("/create", tags=["Game Management"])
def create_game(request: CreateGameRequest):
    try:
        player = Player(name=request.name, player_number=0, id=str(uuid.uuid4()), hand=[])

        game = Game(
            deck=create_deck(),
            discard_pile=[],
            max_players=request.max_players,
            players=[player],
            players_dict={player.id: player},
            status="waiting",
        )

        characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        game_id = "".join(random.choices(characters, k=6))

        games[game_id] = game

        game_state = GameDTO(
            game_id=game_id,
            status="waiting",
            max_players=game.max_players,
            current_turn=0,
            can_match=False,
            can_discard=player.can_discard,
            can_pickup=player.can_pickup,
            special_card_active=None,
            top_of_discard_pile=None,
            player=PlayerDTO(name=request.name, player_index=0, hand=[], picked_up_card=None),
            opponents=[],
            dutch_called_by=None,
            turns_remaining=None,
            last_action=None,
            action_count=0,
        )

        game_state = game_state.model_dump()
        game_state["player_id"] = player.id

        if player.id not in games[game_id].players_dict:
            raise HTTPException(400, "Game not created correctly, please try again")

        return game_state
    
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/join", tags=["Game Management"])
def join_game(game_id: str, name: str = Body(..., embed=True)):
    try:
        if game_id not in games:
            raise HTTPException(404, "Game not found")
        if games[game_id].status != "waiting":
            raise HTTPException(402, "Game already started")
        if len(games[game_id].players) >= games[game_id].max_players:
            raise HTTPException(400, "Game is full")

        game = games[game_id]

        player = Player(
            name=name, player_number=len(game.players), id=str(uuid.uuid4()), hand=[]
        )
        game.players.append(player)
        game.players_dict[player.id] = player

        opponents = []
        for opponent in game.players:
            if opponent.id == player.id:
                continue

            opponent_dto = OpponentDTO(
                name=opponent.name,
                player_index=opponent.player_number,
                hand_length=len(opponent.hand),
            )
            opponents.append(opponent_dto)

        game_state = GameDTO(
            game_id=game_id,
            status="waiting",
            max_players=game.max_players,
            current_turn=0,
            can_match=False,
            can_discard=player.can_discard,
            can_pickup=player.can_pickup,
            special_card_active=None,
            top_of_discard_pile=None,
            player=PlayerDTO(name=name, player_index=0, hand=[], picked_up_card=None),
            opponents=opponents,
            dutch_called_by=None,
            turns_remaining=None,
            last_action=None,
            action_count=0,
        )

        game_state = game_state.model_dump()
        game_state["player_id"] = player.id

        if player.id not in games[game_id].players_dict:
            raise HTTPException(400, "Game not joined, please try again")

        return game_state
    
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/start", tags=["Game Management"])
def start_game(game_id: str, player_id: str):
    try:
        if game_id not in games:
            raise HTTPException(404, "Game not found")
        if games[game_id].status != "waiting":
            raise HTTPException(400, "Game already started")
        if player_id not in games[game_id].players_dict:
            raise HTTPException(403, "You are not part of this game")

        start_game_logic(games[game_id])

    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/{game_id}/{player_id}/get", tags=["Game Management"])
def get_game(game_id: str, player_id: str):
    try:
        if game_id not in games:
            raise HTTPException(404, "Game not found")

        game = games[game_id]

        if player_id not in game.players_dict:
            raise HTTPException(404, "Player not in this game")

        player = game.players_dict[player_id]

        player_hand = []
        for card in player.hand:
            if card.is_revealed:
                player_hand.append(CardDTO(suit=card.suit, rank=card.rank))
            else:
                player_hand.append(CardDTO(suit=None, rank=None))

        if player.picked_up_card:
            picked_up_card = CardDTO.model_validate(player.picked_up_card.model_dump())
        else:
            picked_up_card = None

        return_player = PlayerDTO(
            name=player.name,
            player_index=player.player_number,
            hand=player_hand,
            picked_up_card=picked_up_card,
        )

        opponents = []
        for opponent in game.players:
            if opponent.id == player_id:
                continue

            opponent_dto = OpponentDTO(
                name=opponent.name,
                player_index=opponent.player_number,
                hand_length=len(opponent.hand),
            )
            opponents.append(opponent_dto)

        if len(game.discard_pile) > 0:
            top_of_discard = CardDTO.model_validate(game.discard_pile[-1].model_dump())

        else:
            top_of_discard = None

        if game.dutch_called_by:
            dutch_called_by = game.players_dict[game.dutch_called_by].player_number
        else:
            dutch_called_by = None

        game_state = GameDTO(
            game_id=game_id,
            status=game.status,
            max_players=game.max_players,
            current_turn=game.current_turn,
            can_match=game.can_match,
            can_discard=player.can_discard,
            can_pickup=player.can_pickup,
            special_card_active=game.special_card_played,
            top_of_discard_pile=top_of_discard,
            player=return_player,
            opponents=opponents,
            dutch_called_by=dutch_called_by,
            turns_remaining=game.turns_remaining,
            last_action=game.last_action,
            action_count=game.action_count,
        )
        return game_state

    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/pickup/deck", tags=["Pick Up"])
def pickup_deck(game_id: str, player_id: str):
    try:
        game = games[game_id]
        pick_up_from_deck(game, player_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/pickup/discard", tags=["Pick Up"])
def pickup_discard(game_id: str, player_id: str):
    try:
        game = games[game_id]
        pick_up_from_discard(game, player_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/discard/hand", tags=["Discard"])
def discard_hand(
    game_id: str,
    player_id: str,
    hand_index: int = Body(..., embed=True),
):
    try:
        game = games[game_id]
        discard_from_hand(player_id, hand_index, game)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/discard/picked", tags=["Discard"])
def discard_picked(game_id: str, player_id: str):
    try:
        game = games[game_id]
        discard_pick_up_card(player_id, game)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/special/10", tags=["Special Card"])
def used_10(game_id: str, player_id: str, target_id: int = Body(..., embed=True)):
    game = games[game_id]
    try:
        play_10(game, player_id, target_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/special/jack", tags=["Special Card"])
def jack_additional_info(
    game_id: str,
    player_id: str,
    player_index: int = Body(..., embed=True),
    card_index: int = Body(..., embed=True),
):
    try:
        game = games[game_id]
        card = jack_played(player_index, card_index, player_id, game)
        card = card.model_dump()
        return CardDTO.model_validate(card)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/special/queen", tags=["Special Card"])
def queen_additional_info(
    game_id: str,
    player_id: str,
    player1_index: int = Body(..., embed=True),
    card1_index: int = Body(..., embed=True),
    player2_index: int = Body(..., embed=True),
    card2_index: int = Body(..., embed=True),
):
    try:
        game = games[game_id]
        return queen_played(
            player1_index, card1_index, player2_index, card2_index, game, player_id
        )
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/special/end", tags=["Special Card"])
def end_jack_viewing(game_id: str, player_id: str):
    try:
        game = games[game_id]
        end_viewing(player_id, game)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/match", tags=["General Game Action"])
def match_card(game_id: str, player_id: str, card_index: int = Body(..., embed=True)):
    try:
        game = games[game_id]
        return match(game, player_id, card_index)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/call-dutch", tags=["General Game Action"])
def call_dutch(game_id: str, player_id: str):
    try:
        game = games[game_id]
        call_dutch_logic(game, player_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/result/{game_id}", tags=["Game Management"])
def get_winner(game_id: str):
    try:
        game = games[game_id]
        if game.status != "finished":
            raise HTTPException(400, "Game not finished")

        winners, scores, hands, game_tied = determine_scores(game)

        return {
            "winners": winners,
            "scores": scores,
            "hands": hands,
            "game_tied": game_tied,
        }

    except Exception as e:
        raise HTTPException(400, str(e))
