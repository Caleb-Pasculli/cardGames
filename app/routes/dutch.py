from fastapi import APIRouter, HTTPException
import uuid
from fastapi import Body
from app.dutch_game_logic import *

router = APIRouter(prefix="/dutch")

games: dict[str, Game] = {}

@router.post("/create")
def create_game(num_players: int = Body(..., embed=True)):
    players = [Player(id=i, hand = []) for i in range(num_players)]

    game = Game(
        deck = create_deck(),
        discard_pile=[],
        players=players,
        status="waiting"
    )

    start_game(game)

    game_id = str(uuid.uuid4())
    games[game_id] = game

    return{
        "game_id": game_id,
        "game": game
    }

@router.get("/{game_id}")
def get_game(game_id: str):
    if game_id not in games:
        raise HTTPException("Game not found")
    
    return games[game_id]

@router.post("/{game_id}/{player_id}/pickup/deck")
def pickup_deck(game_id: str, player_id: int):
    try:
        game = games[game_id]
        pick_up_from_deck(game, player_id)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/{game_id}/{player_id}/pickup/discard")
def pickup_discard(game_id: str, player_id: int):
    try:
        game = games[game_id]
        pick_up_from_discard(game, player_id)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/{game_id}/discard/hand")
def discard_hand(game_id: str, player_id: int, hand_index: int):
    try:
        game = games[game_id]
        discard_from_hand(player_id, hand_index, game)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))
    
@router.post("/{game_id}/discard/picked")
def discard_picked(game_id: str, player_id: int):
    try:
        game = games[game_id]
        discard_pick_up_card(player_id, game)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/{game_id}/call-dutch")
def call_dutch_route(game_id: str, player_id: int):
    try:
        game = games[game_id]
        call_dutch(game, player_id)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/{game_id}/winner")
def get_winner(game_id: str):
    game = games[game_id]

    if game.status != "finished":
        raise HTTPException(400, "Game not finished")

    winners, score = determine_winner(game)

    return {
        "winners": winners,
        "score": score
    }
