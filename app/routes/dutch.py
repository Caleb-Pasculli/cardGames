import uuid

from fastapi import Body
from fastapi import APIRouter, HTTPException

from app.dutch_game_logic import *
from app.storage import save_data, load_data

router = APIRouter(prefix="/dutch")

games: dict[str, Game] = {}

@router.post("/create")
def create_game(max_players: int = Body(..., embed=True), name: str = Body(..., embed=True)):
    player_number = 0
    player_id = str(uuid.uuid4())
    players = [Player(name = name, player_number = player_number, id = player_id, hand=[])]

    game = Game(
        deck = create_deck(),
        discard_pile=[],
        max_players=max_players,
        players=players,
        players_dict= {player_id: Player(name = name, player_number = player_number, id = player_id, hand=[])},
        status="waiting"
    )

    game_id = str(uuid.uuid4())
    games[game_id] = game

    return{
        "game_id": game_id,
        "player_id": player_id,
        "player_number": player_number
    }


@router.post("/{game_id}/join")
def join_game(game_id: str, name: str = Body(..., embed=True)):
    if game_id not in games:
        raise HTTPException("Game not found")
    if games[game_id].status != "waiting":
        raise HTTPException("Game already started")
    

    game = games[game_id]

    player_number = len(game.players)
    player_id = str(uuid.uuid4())
    player = Player(name = name, player_number = player_number, id = player_id, hand=[])
    game.players.append(player)
    game.players_dict[player_id] = player


    return {
        "game_id": game_id,
        "player_id": player_id,
        "player_number": player_number
    }


@router.post("/{game_id}/start")
def start_game(game_id: str):
    if game_id not in games:
        raise HTTPException("Game not found")
    if games[game_id].status != "waiting":
        raise HTTPException("Game already started")
    
    start_game_logic(games[game_id])

    return


@router.get("/{game_id}/{player_id}/get")
def get_game(game_id: str, player_id: str):
    if game_id not in games:
        raise HTTPException("Game not found")
    
    game = games[game_id]
    opponent_name = ""
    opponent_hand_size = None
    for i in range(len(game.players)):
        if(game.players[i].id != player_id):
            opponent_name = game.players[i].name
            opponent_hand_size = len(game.players[i].hand)

    current_player = game.players_dict[player_id]

    player_name: str = current_player.name
    player_picked_up_card: Card = current_player.picked_up_card
    player_first_turn: bool = current_player.first_turn
    first_turn_cards: list[Card] | None
    if(player_first_turn and game.status == 'playing'):
        first_turn_cards = [current_player.hand[-2], current_player.hand[-1]]
    else:
        first_turn_cards = None

    return {
        "game_id": game_id,
        "status": game.status,
        "player_name": player_name,
        "player_turn": game.current_turn,
        "player_first_turn": player_first_turn,
        "player_first_turn_cards": first_turn_cards,
        "player_hand_size": len(game.players_dict[player_id].hand),
        "opponent_name": opponent_name,
        "opponent_hand_size": opponent_hand_size,
        "discard_pile": game.discard_pile,
        "picked_up_card": player_picked_up_card,
        "dutch_called": game.dutch_called,
        "dutch_called_by": game.dutch_called_by,
        "turns_remaining": game.turns_remaining,
        "can_match": game.can_match,
        "special_activated": game.players_dict[player_id].special_activated,
        "special_card_played": game.players_dict[player_id].special_card_played,
        "current_turn": game.current_turn
    }


@router.post("/{game_id}/{player_id}/pickup/deck")
def pickup_deck(game_id: str, player_id: str):
    try:
        game = games[game_id]
        pick_up_from_deck(game, player_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/pickup/discard")
def pickup_discard(game_id: str, player_id: str):
    try:
        game = games[game_id]
        pick_up_from_discard(game, player_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/discard/hand")
def discard_hand(game_id: str, player_id: str = Body(..., embed=True), hand_index: int = Body(..., embed=True)):
    try:
        game = games[game_id]
        discard_from_hand(player_id, hand_index, game)
        return
    except Exception as e:
        raise HTTPException(400, str(e))
    

@router.post("/{game_id}/discard/picked")
def discard_picked(game_id: str, player_id: str = Body(..., embed=True)):
    try:
        game = games[game_id]
        discard_pick_up_card(player_id, game)
        return
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/{game_id}/{player_id}/special/10")
def used_10(game_id: str, player_id: str, target_id: str = Body(..., embed=True)):
    game = games[game_id]
    if target_id == "0":
        for id in game.players_dict:
            if id != player_id:
                target_id = id
                break
    try:
        play_10(game, player_id, target_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/special/jack")
def jack_additional_info(game_id: str, player_id: str, player_index: int = Body(..., embed=True), card_index: int = Body(..., embed=True)):
    try:
        game = games[game_id]
        return jack_played(player_index, card_index, player_id, game)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/special/queen")
def queen_additional_info(game_id: str, player_id: str,
                          player1_index: int = Body(..., embed=True), card1_index: int = Body(..., embed=True),
                          player2_index: int = Body(..., embed=True), card2_index: int = Body(..., embed=True)):
    try:
        game = games[game_id]
        return queen_played(player1_index, card1_index, player2_index, card2_index, game, player_id)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/special/end")
def end_jack_viewing(game_id: str, player_id: str):
    try:
        game = games[game_id]
        end_viewing(player_id, game)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/{player_id}/match")
def match_card(game_id: str, player_id: str, card_index: int = Body(..., embed=True)):
    try:
        game = games[game_id]
        return match(game, player_id, card_index)
    except Exception as e:
        raise HTTPException(400, str(e))
    

@router.post("/{game_id}/call-dutch")
def call_dutch(game_id: str, player_id: str = Body(..., embed=True)):
    try:
        game = games[game_id]
        print(type(list(games.keys())[0]))
        call_dutch_logic(game, player_id)
        return
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/result/{game_id}")
def get_winner(game_id: str):
    game = games[game_id]
    if game.status != "finished":
        raise HTTPException(400, "Game not finished")

    winners, scores, hands, game_tied = determine_scores(game)

    return {
        "winners": winners,
        "scores": scores,
        "hands": hands,
        "game_tied": game_tied
    }
