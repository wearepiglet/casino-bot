import random
from typing import List, Dict, Tuple
import discord
from utils.embeds import EmbedBuilder

class Card:
    """Represents a playing card."""
    
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    @property
    def value(self) -> int:
        """Get numeric value of card."""
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # Ace high by default
        else:
            return int(self.rank)

class BlackjackHand:
    """Represents a blackjack hand."""
    
    def __init__(self):
        self.cards: List[Card] = []
    
    def add_card(self, card: Card):
        """Add a card to the hand."""
        self.cards.append(card)
    
    def get_value(self) -> int:
        """Get the best value of the hand."""
        value = 0
        aces = 0
        
        for card in self.cards:
            if card.rank == 'A':
                aces += 1
                value += 11
            else:
                value += card.value
        
        # Adjust for aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def get_soft_value(self) -> Tuple[int, bool]:
        """Get value and whether it's a soft hand (ace counted as 11)."""
        value = 0
        aces = 0
        
        for card in self.cards:
            if card.rank == 'A':
                aces += 1
                value += 11
            else:
                value += card.value
        
        # Check if we have a soft hand
        soft = aces > 0 and value <= 21
        
        # Adjust for aces if busted
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value, soft
    
    def is_blackjack(self) -> bool:
        """Check if hand is blackjack (21 with 2 cards)."""
        return len(self.cards) == 2 and self.get_value() == 21
    
    def is_busted(self) -> bool:
        """Check if hand is busted (over 21)."""
        return self.get_value() > 21
    
    def __str__(self):
        """String representation of hand."""
        return " ".join(str(card) for card in self.cards)

class BlackjackDeck:
    """Represents a 6-deck shoe for blackjack."""
    
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self):
        """Reset and shuffle the deck."""
        self.cards = []
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        # Create 6 decks
        for _ in range(6):
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(suit, rank))
        
        random.shuffle(self.cards)
    
    def deal_card(self) -> Card:
        """Deal a card from the deck."""
        if len(self.cards) < 50:  # Reshuffle when deck gets low
            self.reset()
        return self.cards.pop()

class BlackjackGame:
    """Manages a blackjack game."""
    
    def __init__(self, bet_amount: int, hard_mode: bool = False):
        self.bet_amount = bet_amount
        self.hard_mode = hard_mode
        self.deck = BlackjackDeck()
        self.player_hand = BlackjackHand()
        self.dealer_hand = BlackjackHand()
        self.game_over = False
        self.result = ""
        self.payout = 0
        
        # Deal initial cards
        self.player_hand.add_card(self.deck.deal_card())
        self.dealer_hand.add_card(self.deck.deal_card())
        self.player_hand.add_card(self.deck.deal_card())
        self.dealer_hand.add_card(self.deck.deal_card())
        
        # Check for blackjacks
        if self.dealer_hand.is_blackjack():
            self.game_over = True
            self.result = "Dealer Blackjack - You lose!"
            self.payout = -self.bet_amount
        elif self.player_hand.is_blackjack():
            self.game_over = True
            self.result = "Blackjack! You win!"
            self.payout = int(self.bet_amount * 1.5)  # 3:2 payout
    
    def hit(self) -> bool:
        """Player hits (takes another card)."""
        if self.game_over:
            return False
        
        self.player_hand.add_card(self.deck.deal_card())
        
        if self.player_hand.is_busted():
            self.game_over = True
            self.result = "Busted! You lose!"
            self.payout = -self.bet_amount
            return False
        
        return True
    
    def stand(self):
        """Player stands (dealer plays)."""
        if self.game_over:
            return
        
        # Dealer must hit on 16 and stand on 17
        while self.dealer_hand.get_value() < 17:
            self.dealer_hand.add_card(self.deck.deal_card())
        
        self.game_over = True
        self._determine_winner()
    
    def _determine_winner(self):
        """Determine the winner and set result/payout."""
        player_value = self.player_hand.get_value()
        dealer_value = self.dealer_hand.get_value()
        
        if self.dealer_hand.is_busted():
            self.result = "Dealer busted! You win!"
            if self.hard_mode:
                self.payout = self.bet_amount * 2  # 2:1 in hard mode
            else:
                self.payout = int(self.bet_amount * 1.5)  # 3:2 in easy mode
        elif player_value > dealer_value:
            self.result = "You win!"
            if self.hard_mode:
                self.payout = self.bet_amount * 2
            else:
                self.payout = int(self.bet_amount * 1.5)
        elif player_value == dealer_value:
            self.result = "Push (tie)!"
            self.payout = 0
        else:
            self.result = "Dealer wins!"
            self.payout = -self.bet_amount
    
    def get_game_embed(self, show_dealer_hole: bool = False) -> discord.Embed:
        """Get embed showing current game state."""
        if self.hard_mode:
            title = "🃏 Blackjack (Hard Mode)"
        else:
            title = "🃏 Blackjack (Easy Mode)"
        
        embed = EmbedBuilder.game_result(title, "")
        
        # Player hand
        player_value, is_soft = self.player_hand.get_soft_value()
        if self.hard_mode:
            player_display = f"Cards: {self.player_hand}"
        else:
            if is_soft and player_value != 21:
                # Show both hard and soft values
                hard_value = self.player_hand.get_value()
                if hard_value != player_value:
                    player_display = f"Cards: {self.player_hand}\nValue: {hard_value} ({player_value})"
                else:
                    player_display = f"Cards: {self.player_hand}\nValue: {player_value}"
            else:
                player_display = f"Cards: {self.player_hand}\nValue: {player_value}"
        
        embed.add_field(
            name="👤 Your Hand",
            value=player_display,
            inline=False
        )
        
        # Dealer hand
        if show_dealer_hole or self.game_over:
            dealer_value = self.dealer_hand.get_value()
            if self.hard_mode:
                dealer_display = f"Cards: {self.dealer_hand}"
            else:
                dealer_display = f"Cards: {self.dealer_hand}\nValue: {dealer_value}"
        else:
            # Hide hole card
            visible_card = str(self.dealer_hand.cards[0])
            if self.hard_mode:
                dealer_display = f"Cards: {visible_card} ?"
            else:
                visible_value = self.dealer_hand.cards[0].value
                dealer_display = f"Cards: {visible_card} ?\nVisible Value: {visible_value}"
        
        embed.add_field(
            name="🎭 Dealer Hand",
            value=dealer_display,
            inline=False
        )
        
        # Game status
        if self.game_over:
            embed.add_field(
                name="🎯 Result",
                value=f"{self.result}\nPayout: {self.payout:+,} coins",
                inline=False
            )
            
            if self.payout > 0:
                embed.color = 0x00ff00  # Green for win
            elif self.payout < 0:
                embed.color = 0xff0000  # Red for loss
            else:
                embed.color = 0xffff00  # Yellow for push
        else:
            embed.add_field(
                name="🎮 Actions",
                value="React with 🎯 to **Hit** or ✋ to **Stand**",
                inline=False
            )
        
        return embed
