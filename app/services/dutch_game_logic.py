import random
from pydantic import BaseModel

from app.dto.LastAction import GameActionsEnum, LastActionDTO


class Card(BaseModel):
    suit: str | None = None
    rank: str | None = None
    value: int | None = None
    is_revealed: bool = False


class Player(BaseModel):
    player_number: int
    first_turn: bool = True
    name: str
    id: str
    hand: list[Card]
    picked_up_card: Card | None = None
    picked_up_from_discard: bool = False
    can_pickup: bool = True
    can_discard: bool = False
    opponents_hands: list[list[Card]]


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

    special_card_played: str | None = None
    special_activated: bool = False

    last_action: LastActionDTO | None = None
    action_count: int = 0


def create_deck():
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = [
        "Ace",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "Jack",
        "Queen",
        "King",
    ]
    values = {
        "Ace": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "Jack": 10,
        "Queen": 10,
    }
    deck = []

    for suit in suits:
        for rank in ranks:
            if rank == "King" and (suit == "Hearts" or suit == "Diamonds"):
                value = 0
            elif rank == "King":
                value = 20
            else:
                value = values[rank]

            deck.append(Card(suit=suit, rank=rank, value=value))
    random.shuffle(deck)
    return deck


def deal_cards(game: Game):
    for player in game.players:
        for i in range(2):
            player.hand.append(game.deck.pop(-1))

        for i in range(2):
            player.hand.append(game.deck.pop(-1))
            player.hand[-1].is_revealed = True

        for i in range(len(game.players) - 1):
            player.opponents_hands[i] = [Card(), Card(), Card(), Card()]
        
        game.players_dict[player.id] = player


def start_game_logic(game: Game):
    game.discard_pile.append(game.deck.pop())
    game.discard_pile[-1].is_revealed = True
    deal_cards(game)

    game.status = "playing"
    game.current_turn = random.randint(0, len(game.players) - 1)


def turn_validation(game: Game, player_id: str):
    current_player = game.players[game.current_turn]

    if current_player.id != player_id:
        raise Exception("Not your turn")

    if game.status != "playing":
        raise Exception("Game is not active")


def pick_up_from_deck(game: Game, player_id: str):
    turn_validation(game, player_id)

    current_player = game.players[game.current_turn]
    if not current_player.can_pickup or current_player.picked_up_card is not None:
        raise Exception("Already picked up")

    pickedUpCard = game.deck.pop()
    pickedUpCard.is_revealed = True
    current_player.picked_up_card = pickedUpCard
    current_player.can_discard = True
    current_player.can_pickup = False

    if current_player.first_turn:
        for card in current_player.hand:
            card.is_revealed = False
        game.players[game.current_turn].first_turn = False

    if pickedUpCard.rank == "10":
        game.special_card_played = "10"

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.PICKUP_DECK,
        player_id=current_player.player_number,
        player_name=current_player.name,
    )
    game.action_count += 1

    game.can_match = False
    return pickedUpCard


def pick_up_from_discard(game: Game, player_id: str):
    turn_validation(game, player_id)
    current_player = game.players[game.current_turn]
    if not game.discard_pile:
        raise Exception("Discard Empty")

    if not current_player.can_pickup or current_player.picked_up_card is not None:
        raise Exception("Already picked up")

    pickedUpCard = game.discard_pile.pop()
    pickedUpCard.is_revealed = True
    current_player.picked_up_card = pickedUpCard
    current_player.picked_up_from_discard = True
    current_player.can_discard = True
    current_player.can_pickup = False

    if current_player.first_turn:
        current_player.hand[-1].is_revealed = False
        current_player.hand[-2].is_revealed = False
        game.players[game.current_turn].first_turn = False

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.PICKUP_DISCARD,
        player_id=current_player.player_number,
        player_name=current_player.name,
    )
    game.action_count += 1

    game.can_match = False
    return pickedUpCard


def play_10(game: Game, player_id: str, target_player_index: int):
    turn_validation(game, player_id)

    player = game.players_dict[player_id]

    target_player = game.players[target_player_index]
    if not player.picked_up_card or player.picked_up_card.rank != "10":
        raise Exception("You do not have a 10")
  
    player.picked_up_card.is_revealed = False
    target_player.hand.append(player.picked_up_card)

    player.picked_up_card = None

    for other_player in game.players:
        if other_player.id == target_player.id:
            continue

        if target_player_index > player.player_number:
            target_player_index -= 1

        other_player.opponents_hands[target_player_index].append(Card())

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.TEN_ADD,
        player_id=player.player_number,
        player_name=player.name,
        target_player_1=target_player.player_number,
        target_card_index_1=len(target_player.hand) - 1,
    )
    game.action_count += 1

    advance_turn(game)
    return


def discard_from_hand(player_id: str, hand_index: int, game: Game):
    turn_validation(game, player_id)
    current_player: Player = game.players[game.current_turn]

    if not current_player.can_discard:
        # add some error handling
        return

    hand = None
    for player in game.players:
        if player.id == player_id:
            hand = player.hand

    if hand:
        game.discard_pile.append(hand[hand_index])
        game.discard_pile[-1].is_revealed = True
        if current_player.picked_up_card:
            hand[hand_index] = current_player.picked_up_card
            hand[hand_index].is_revealed = False

    current_player.picked_up_card = None
    current_player.can_discard = False

    if game.discard_pile[-1].rank == "Jack":
        game.special_activated = True
        game.special_card_played = "Jack"
        return

    if game.discard_pile[-1].rank == "Queen":
        game.special_activated = True
        game.special_card_played = "Queen"
        return

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.DISCARD_HAND,
        player_id=current_player.player_number,
        player_name=current_player.name,
        target_player_1=current_player.player_number,
        target_card_index_1=hand_index,
    )
    game.action_count += 1

    advance_turn(game)
    return


def discard_pick_up_card(player_id: str, game: Game):
    turn_validation(game, player_id)
    current_player = game.players[game.current_turn]

    if not current_player.can_discard:
        # add some error handling
        return

    if current_player.picked_up_card:
        game.discard_pile.append(current_player.picked_up_card)

    game.discard_pile[-1].is_revealed = True
    current_player.picked_up_card = None

    picked_from_discard = current_player.picked_up_from_discard
    current_player.picked_up_from_discard = False

    current_player.can_discard = False

    if not picked_from_discard:
        if game.discard_pile[-1].rank == "Jack":
            game.special_activated = True
            game.special_card_played = "Jack"
            return

        if game.discard_pile[-1].rank == "Queen":
            game.special_activated = True
            game.special_card_played = "Queen"
            return

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.DISCARD_PICK_UP,
        player_id=current_player.player_number,
        player_name=current_player.name,
        target_player_1=current_player.player_number,
    )
    game.action_count += 1

    advance_turn(game)
    return


def jack_played(player_index: int, card_index: int, player_id: str, game: Game):
    turn_validation(game, player_id)
    if (
        not game.special_activated
        or game.special_card_played != "Jack"
        or game.jack_viewed
    ):
        return

    target_player = game.players[player_index]
    player = game.players_dict[player_id]

    revealed_card = target_player.hand[card_index].model_copy()
    revealed_card.is_revealed = True

    if player_index == player.player_number:
        player.hand[card_index] = revealed_card
    else:
        player.opponents_hands[player_index][card_index] = revealed_card

    game.jack_viewed = True

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.JACK_VIEW,
        player_id=player.player_number,
        player_name=player.name,
        target_player_1=target_player.player_number,
        target_card_index_1=card_index,
    )
    game.action_count += 1


def end_viewing(player_id: str, game: Game):
    turn_validation(game, player_id)

    for player in game.players:
        player.picked_up_card = None
        for card in player.hand:
            card.is_revealed = False

    game.jack_viewed = False

    current_player = game.players_dict[player_id]
    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.END_TURN,
        player_id=current_player.player_number,
        player_name=current_player.name,
    )
    game.action_count += 1

    advance_turn(game)
    return


def queen_played(
    player1_index: int,
    card1_index: int,
    player2_index: int,
    card2_index: int,
    game: Game,
    player_id: str,
):
    if not game.special_activated or game.special_card_played != "Queen":
        return
    turn_validation(game, player_id)
    player = game.players_dict[player_id]
    player1 = game.players[player1_index]
    player2 = game.players[player2_index]

    temp = player1.hand[card1_index]
    player1.hand[card1_index] = player2.hand[card2_index]
    player2.hand[card2_index] = temp

    for card in player1.hand:
        card.is_revealed = False
    for card in player2.hand:
        card.is_revealed = False

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.QUEEN_SWAP,
        player_id=player.player_number,
        player_name=player.name,
        target_player_1=player1_index,
        target_card_index_1=card1_index,
        target_player_2=player2_index,
        target_card_index_2=card2_index,
    )
    game.action_count += 1

    advance_turn(game)
    return


def match(game: Game, player_id: str, card_index: int):
    if not game.can_match:
        return

    current_player = game.players_dict[player_id]
    if current_player.hand[card_index].rank != game.discard_pile[-1].rank:
        current_player.hand.append(game.deck.pop())

        target_player_index = current_player.player_number
        for other_player in game.players:
            if other_player.id == current_player.id:
                continue
            
            if target_player_index > other_player.player_number:
                target_player_index -= 1

            other_player.opponents_hands[target_player_index].append(Card())

        game.last_action = LastActionDTO(
            action_type=GameActionsEnum.WRONG_MATCH,
            player_id=current_player.player_number,
            player_name=current_player.name,
            target_player_1=current_player.player_number,
            target_card_index_1=card_index,
        )
        game.action_count += 1

        return

    game.discard_pile.append(current_player.hand.pop(card_index))
    game.discard_pile[-1].is_revealed = True
    game.can_match = False

    target_player_index = current_player.player_number
    for other_player in game.players:
        if other_player.id == current_player.id:
            continue
        
        if target_player_index > other_player.player_number:
            target_player_index -= 1

        other_player.opponents_hands[target_player_index].pop()

    game.last_action = LastActionDTO(
        action_type=GameActionsEnum.CORRECT_MATCH,
        player_id=current_player.player_number,
        player_name=current_player.name,
        target_player_1=current_player.player_number,
        target_card_index_1=card_index,
    )
    game.action_count += 1
    return


def advance_turn(game: Game):
    game.special_activated = False
    game.special_card_played = None

    if game.dutch_called_by is not None:
        if game.turns_remaining:
            game.turns_remaining -= 1
        if game.turns_remaining == 0:
            game.status = "finished"
            return

    for player in game.players:
        player.can_pickup = True
        player.can_discard = False

        player_number = 0
        for opponent in game.players:
            if opponent.id == player.id:
                continue
            player.opponents_hands[player_number] = [Card() for _ in opponent.hand]
            player_number += 1

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
            if card.value:
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

    if len(winners_name) > 1:
        game_tied = True
    return winners_name, scores, hands, game_tied
