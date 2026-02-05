import uuid

from fastapi import Body
from fastapi import APIRouter, HTTPException

from app.dutch_game_logic import *
from app.storage import save_data, load_data

router = APIRouter(prefix="/dutch")

games: dict[str, Game] = {}

@router.post("/create")
def create_game(max_players: int = Body(..., embed=True)):
    player_number = 0
    player_id = str(uuid.uuid4())
    players = [Player(player_number = player_number, id = player_id, hand=[])]

    game = Game(
        deck = create_deck(),
        discard_pile=[],
        max_players=max_players,
        players=players,
        players_dict= {player_id: Player(player_number = player_number, id = player_id, hand=[])},
        status="waiting"
    )

    game_id = str(uuid.uuid4())
    games[game_id] = game

    return{
        "game_id": game_id,
        "player_id": player_id,
        "game": game
    }


@router.post("/{game_id}/join")
def join_game(game_id: str):
    if game_id not in games:
        raise HTTPException("Game not found")
    if games[game_id].status != "waiting":
        raise HTTPException("Game already started")
    

    game = games[game_id]

    player_number = len(game.players) - 1
    player_id = str(uuid.uuid4())
    player = Player(player_number = player_number, id = player_id, hand=[])
    game.players.append(player)
    game.players_dict[player_id] = player


    return {
        "game_id": game_id,
        "player_id": player_id,
        "game": game
    }


@router.post("/{game_id}/start")
def start_game(game_id: str):
    if game_id not in games:
        raise HTTPException("Game not found")
    if games[game_id].status != "waiting":
        raise HTTPException("Game already started")
    
    start_game_logic(games[game_id])

    return {
        "game": games[game_id]
    }


@router.get("/{game_id}/{player_id}/get")
def get_game(game_id: str, player_id: str):
    if game_id not in games:
        raise HTTPException("Game not found")
    
    game = games[game_id]

    opponent_hand_size = None
    for i in range(len(game.players)):
        if(game.players[i].id != player_id):
            opponent_hand_size = len(game.players[i].hand)
        

    return {
        "game_id": game_id,
        "status": game.status,
        "player_turn": game.current_turn,
        "opponent_hand_size": opponent_hand_size,
        "hand": game.players_dict[player_id].hand,
        "discard_pile": game.discard_pile,
        "picked_up_card": game.picked_up_card,
        "dutch_called_by": game.dutch_called_by,
        "turns_remaining": game.turns_remaining
    }


@router.post("/{game_id}/{player_id}/pickup/deck")
def pickup_deck(game_id: str, player_id: str):
    try:
        game = games[game_id]
        pick_up_from_deck(game, player_id)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/pickup/discard")
def pickup_discard(game_id: str, player_id: str):
    try:
        game = games[game_id]
        pick_up_from_discard(game, player_id)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/discard/hand")
def discard_hand(game_id: str, player_id: str = Body(..., embed=True), hand_index: int = Body(..., embed=True)):
    try:
        game = games[game_id]
        discard_from_hand(player_id, hand_index, game)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))
    

@router.post("/{game_id}/discard/picked")
def discard_picked(game_id: str, player_id: str = Body(..., embed=True)):
    try:
        game = games[game_id]
        discard_pick_up_card(player_id, game)
        return game
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/call-dutch")
def call_dutch(game_id: str, player_id: str):
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
