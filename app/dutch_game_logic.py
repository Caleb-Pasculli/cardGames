from enum import Enum
import random
from pydantic import BaseModel

class Card(BaseModel): 
    suit: str = None
    rank: str = None
    value: int = None
    is_revealed: bool = False

class Player(BaseModel):
    id: int
    hand: list[Card]

class Game(BaseModel):
    deck: list[Card]
    discard_pile: list[Card]
    picked_up_card: Card | None = None
    players: list[Player]
    current_turn: int = 0
    status: str
    dutch_called_by: int | None = None
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
        for i in range(4):
            player.hand.append(game.deck.pop(-1))



def start_game(game: Game):
    game.discard_pile.append(game.deck.pop())
    game.discard_pile[-1].is_revealed = True
    deal_cards(game)
    game.status = "playing"



def turn_validation(game: Game, player_id = int):
    current_player = game.players[game.current_turn]

    if current_player.id != player_id:
        raise Exception("Not your turn")

    if game.status != "playing":
        raise Exception("Game is not active")


def reveal_initial_cards(player: Player):
    player.hand[2].is_revealed = True
    player.hand[3].is_revealed = True



def hide_initial_cards(player: Player):
    player.hand[2].is_revealed = False
    player.hand[3].is_revealed = False



def pick_up_from_deck(game: Game, player_id: int):
    turn_validation(game, player_id)

    if game.picked_up_card != None:
        raise Exception("Already picked up")
    
    pickedUpCard = game.deck.pop()
    pickedUpCard.is_revealed = True
    game.picked_up_card = pickedUpCard
    return pickedUpCard



def pick_up_from_discard(game: Game, player_id: int):

    turn_validation(game, player_id)

    if not game.discard_pile:
        raise Exception("Discard Empty")
    
    if game.picked_up_card != None:
        raise Exception("Already picked up")
    
    pickedUpCard = game.discard_pile.pop()
    pickedUpCard.is_revealed = True
    game.picked_up_card = pickedUpCard
    return pickedUpCard



def discard_from_hand(player_id: int, hand_index: int, game: Game):

    turn_validation(game, player_id)

    hand = None
    for player in game.players:
        if player.id == player_id:
            hand = player.hand
    
    game.discard_pile.append(hand[hand_index])
    game.discard_pile[-1].is_revealed = True
    hand[hand_index] = game.picked_up_card
    game.picked_up_card = None
    advance_turn(game)
    return



def discard_pick_up_card(player_id: int, game: Game):
    turn_validation(game, player_id)

    game.discard_pile.append(game.picked_up_card)
    game.discard_pile[-1].is_revealed = True
    game.picked_up_card = None
    advance_turn(game)
    return



def advance_turn(game: Game):
    if game.dutch_called_by != None:
        game.turns_remaining -= 1
        if game.turns_remaining == 0:
            game.status = "finished"
            return

    game.current_turn = (game.current_turn + 1) % len(game.players)



def call_dutch(game:Game, player_id: int):
    
    turn_validation(game, player_id)

    if game.dutch_called_by != None:
        raise Exception("Dutch has already been called")
    
    game.dutch_called_by = player_id
    game.turns_remaining = len(game.players)
    return



def determine_winner(game: Game):
    lowest_score_id = []
    lowest_score = len(game.players[0].hand) * 20
    
    for player in game.players:
        score = 0
        for card in player.hand:
            score += card.value
        
        if score < lowest_score:
            lowest_score_id = [player.id]
        if score == lowest_score:
            lowest_score_id.append(player.id)

    return lowest_score_id, lowest_score
