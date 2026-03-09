from enum import Enum
import random
from pydantic import BaseModel

class Card(BaseModel): 
    suit: str = None
    rank: str = None
    value: int = None
    is_revealed: bool = False


class Player(BaseModel):
    player_number: int
    first_turn: bool = True
    name: str
    id: str
    hand: list[Card]
    picked_up_card: Card | None = None
    special_card_played: str | None = None
    special_activated: bool = False


class Game(BaseModel):
    deck: list[Card]
    discard_pile: list[Card]
    
    max_players: int = 2
    players: list[Player]
    players_dict: dict[str, Player]
    current_turn: int = 1

    status: str
    can_match: bool = True
    jack_viewed: bool = False
    dutch_called: bool = False
    dutch_called_by: str | None = None
    turns_remaining: int | None = None


def create_deck():
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
    values = {'Ace': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
     '10': 10,'Jack': 10, 'Queen': 10}
    deck = []
    value = 0

    for suit in suits:
        for rank in ranks:
            if rank == 'King' and (suit == 'Hearts' or suit == 'Diamonds'):
                value = 0
            elif rank == 'King':
                value = 20
            else:
                value = values[rank]

            deck.append(Card(suit = suit, rank = rank, value = value))
    random.shuffle(deck)
    return deck


def deal_cards(game: Game):
    for player in game.players:
        for i in range(2):
            player.hand.append(game.deck.pop(-1))
        for i in range(2):
            player.hand.append(game.deck.pop(-1))
            player.hand[-1].is_revealed = True
        game.players_dict[player.id] = player


def start_game_logic(game: Game):
    game.discard_pile.append(game.deck.pop())
    game.discard_pile[-1].is_revealed = True
    deal_cards(game)
    game.status = "playing"


def turn_validation(game: Game, player_id: str):
    current_player = game.players[game.current_turn]

    if current_player.id != player_id:
        raise Exception("Not your turn")

    if game.status != "playing":
        raise Exception("Game is not active")


def pick_up_from_deck(game: Game, player_id: str):
    turn_validation(game, player_id)

    current_player = game.players[game.current_turn]

    if current_player.picked_up_card != None:
        raise Exception("Already picked up")
    

    pickedUpCard = game.deck.pop()
    pickedUpCard.is_revealed = True
    current_player.picked_up_card = pickedUpCard

    if (current_player.first_turn == True):
        for card in current_player.hand:
            card.is_revealed = False
        game.players[game.current_turn].first_turn = False

    if(pickedUpCard.rank == "10"):
        current_player.special_card_played = '10'
    
    game.can_match = False
    return pickedUpCard



def pick_up_from_discard(game: Game, player_id: str):
    turn_validation(game, player_id)
    current_player = game.players[game.current_turn]
    if not game.discard_pile:
        raise Exception("Discard Empty")
    
    if current_player.picked_up_card != None:
        raise Exception("Already picked up")

    pickedUpCard = game.discard_pile.pop()
    pickedUpCard.is_revealed = True
    current_player.picked_up_card = pickedUpCard
    current_player = game.players[game.current_turn]
    if (current_player.first_turn == True):
        current_player.hand[-1].is_revealed = False
        current_player.hand[-2].is_revealed = False
        game.players[game.current_turn].first_turn = False

    game.can_match = False
    return pickedUpCard


def play_10(game: Game, player_id: str, target_player_id: str):
    turn_validation(game, player_id)

    player = game.players_dict[player_id]
    target_player = game.players_dict[target_player_id]
    if player.picked_up_card.rank != "10":
        raise Exception("You do not have a 10")
    
    player.picked_up_card.is_revealed = False
    target_player.hand.append(player.picked_up_card)
    player.picked_up_card = None

    advance_turn(game)
    return


def discard_from_hand(player_id: str, hand_index: int, game: Game):
    turn_validation(game, player_id)
    current_player = game.players[game.current_turn]
    hand = None
    for player in game.players:
        if player.id == player_id:
            hand = player.hand

    game.discard_pile.append(hand[hand_index])
    game.discard_pile[-1].is_revealed = True
    hand[hand_index] = current_player.picked_up_card
    hand[hand_index].is_revealed = False
    current_player.picked_up_card = None

    if (game.discard_pile[-1].rank == "Jack"):
        game.players_dict[player_id].special_activated = True
        game.players_dict[player_id].special_card_played = "Jack"
        return

    if (game.discard_pile[-1].rank == "Queen"):
        game.players_dict[player_id].special_activated = True
        game.players_dict[player_id].special_card_played = "Queen"
        return

    advance_turn(game)
    return


def discard_pick_up_card(player_id: str, game: Game):
    turn_validation(game, player_id)
    current_player = game.players[game.current_turn]
    game.discard_pile.append(current_player.picked_up_card)
    game.discard_pile[-1].is_revealed = True
    current_player.picked_up_card = None

    if (game.discard_pile[-1].rank == "Jack"):
        game.players_dict[player_id].special_activated = True
        game.players_dict[player_id].special_card_played = "Jack"
        return
    
    if (game.discard_pile[-1].rank == "Queen"):
        game.players_dict[player_id].special_activated = True
        game.players_dict[player_id].special_card_played = "Queen"
        return
    
    advance_turn(game)
    return


def jack_played(player_index: int, card_index: int, player_id: str, game: Game):
    turn_validation(game, player_id)
    if (game.players_dict[player_id].special_activated == False or 
        game.players_dict[player_id].special_card_played != "Jack" or
        game.jack_viewed):
        return
    
    player = game.players[player_index]

    revealed_card = player.hand[card_index].model_copy()
    revealed_card.is_revealed = True
    game.jack_viewed = True
    return revealed_card


def end_viewing(player_id: str, game: Game):
    turn_validation(game, player_id)
    
    for player in game.players:
        player.picked_up_card = None
        for card in player.hand:
            card.is_revealed = False

    game.jack_viewed = False
    advance_turn(game)
    return


def queen_played(player1_index: int, card1_index: int, player2_index: int, card2_index: int, game: Game, player_id: str):
    if (game.players_dict[player_id].special_activated == False or 
        game.players_dict[player_id].special_card_played != "Queen"):
        return
    turn_validation(game, player_id)
    player1 = game.players[player1_index]
    player2 = game.players[player2_index]

    temp = player1.hand[card1_index]
    player1.hand[card1_index] = player2.hand[card2_index]
    player2.hand[card2_index] = temp

    for card in player1.hand:
        card.is_revealed = False
    for card in player2.hand:
        card.is_revealed = False
    advance_turn(game)
    return

def match(game: Game, player_id: str, card_index: int):
    if(not game.can_match):
        return

    current_player = game.players_dict[player_id]
    if current_player.hand[card_index].rank != game.discard_pile[-1].rank:
        current_player.hand.append(game.deck.pop())
        return
    
    game.discard_pile.append(current_player.hand.pop(card_index))
    game.discard_pile[-1].is_revealed = True
    game.can_match = False
    return


def advance_turn(game: Game):
    for player in game.players:
        player.special_activated = False
        player.special_card_played = None

    if game.dutch_called_by != None:
        game.turns_remaining -= 1
        if game.turns_remaining == 0:
            game.status = "finished"
            return
        
    game.can_match = True
    game.current_turn = (game.current_turn + 1) % len(game.players)


def call_dutch_logic(game: Game, player_id: str):
    turn_validation(game, player_id)

    if game.dutch_called:
        raise Exception("Dutch has already been called")
    
    game.dutch_called = True
    game.dutch_called_by = player_id
    game.turns_remaining = len(game.players)
    return


def determine_scores(game: Game):
    game_tied = False
    scores = []
    winners_name = []
    hands: list[list[Card]] = []
    lowest_score = len(game.players[0].hand) * 20
    
    for player in game.players:
        score = 0
        hands.append(player.hand)
        for card in player.hand:
            score += card.value
        scores.append(score)

        if score < lowest_score:
            winners_name = [player.name]
            lowest_score = score
        elif score == lowest_score:
            winners_name.append(player.name)

    for hand in hands:
        for card in hand:
            card.is_revealed = True

    if len(winners_name) > 1: game_tied = True
    return winners_name, scores, hands, game_tied
