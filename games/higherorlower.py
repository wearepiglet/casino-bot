import random
import discord
from utils.embeds import EmbedBuilder

class HigherOrLowerGame:
    """Manages a Higher or Lower game."""
    
    def __init__(self):
        self.current_card = None
        self.next_card = None
        self.score = 0
        self.game_over = False
        self.suits = ['♠', '♥', '♦', '♣']
        self.ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.deck = self._create_deck()
        
        # Draw first card
        self.current_card = self._draw_card()
    
    def _create_deck(self) -> list:
        """Create a shuffled deck of cards."""
        deck = []
        for suit in self.suits:
            for rank in self.ranks:
                deck.append({'suit': suit, 'rank': rank, 'value': self._get_card_value(rank)})
        random.shuffle(deck)
        return deck
    
    def _get_card_value(self, rank: str) -> int:
        """Get numeric value of card rank."""
        if rank == 'A':
            return 1
        elif rank in ['J', 'Q', 'K']:
            return {'J': 11, 'Q': 12, 'K': 13}[rank]
        else:
            return int(rank)
    
    def _draw_card(self) -> dict:
        """Draw a card from the deck."""
        if len(self.deck) < 2:
            self.deck = self._create_deck()
        return self.deck.pop()
    
    def _format_card(self, card: dict) -> str:
        """Format card for display."""
        return f"{card['rank']}{card['suit']}"
    
    def make_guess(self, guess: str) -> dict:
        """Make a higher/lower guess."""
        if self.game_over:
            return {'success': False, 'message': 'Game is already over'}
        
        guess = guess.lower()
        if guess not in ['higher', 'lower', 'h', 'l']:
            return {'success': False, 'message': 'Invalid guess. Use "higher" or "lower"'}
        
        # Normalize guess
        if guess in ['h', 'higher']:
            guess = 'higher'
        else:
            guess = 'lower'
        
        # Draw next card
        self.next_card = self._draw_card()
        
        # Check if guess is correct
        current_value = self.current_card['value']
        next_value = self.next_card['value']
        
        correct = False
        if guess == 'higher' and next_value > current_value:
            correct = True
        elif guess == 'lower' and next_value < current_value:
            correct = True
        elif next_value == current_value:
            # Tie - player continues but no point
            correct = True
        
        if correct:
            if next_value != current_value:  # Only award points for non-ties
                self.score += 1
            self.current_card = self.next_card
            self.next_card = None
            return {
                'success': True,
                'correct': True,
                'score': self.score,
                'current_card': self.current_card,
                'continue': True
            }
        else:
            self.game_over = True
            return {
                'success': True,
                'correct': False,
                'score': self.score,
                'current_card': self.current_card,
                'next_card': self.next_card,
                'continue': False
            }
    
    def cash_out(self) -> dict:
        """Cash out and end the game."""
        self.game_over = True
        payout = 100 * self.score  # 100 coins per point
        xp = 10 * self.score  # 10 XP per point
        
        return {
            'score': self.score,
            'payout': payout,
            'xp': xp
        }
    
    def get_game_embed(self) -> discord.Embed:
        """Get embed showing current game state."""
        title = "🃏 Higher or Lower"
        
        description = f"**Current Card:** {self._format_card(self.current_card)}\n"
        description += f"**Score:** {self.score}\n\n"
        
        if not self.game_over:
            description += "Will the next card be **higher** or **lower**?\n"
            description += "React with ⬆️ for higher, ⬇️ for lower, or 💰 to cash out!"
        else:
            if self.next_card:
                description += f"**Next Card:** {self._format_card(self.next_card)}\n"
            description += f"**Final Score:** {self.score}\n"
            description += f"**Payout:** {100 * self.score:,} coins\n"
            description += f"**XP Earned:** {10 * self.score} XP"
        
        color = 0x0099ff if not self.game_over else (0x00ff00 if self.score > 0 else 0xff0000)
        embed = EmbedBuilder.game_result(title, description, color)
        
        if not self.game_over:
            embed.add_field(
                name="💡 How to Play",
                value="Guess if the next card will be higher or lower than the current card.\n"
                      "Each correct guess gives you 1 point.\n"
                      "Cash out anytime to secure your winnings!",
                inline=False
            )
        
        embed.add_field(
            name="💰 Payout",
            value=f"100 coins × {self.score} = {100 * self.score:,} coins",
            inline=True
        )
        
        embed.add_field(
            name="⭐ XP",
            value=f"10 XP × {self.score} = {10 * self.score} XP",
            inline=True
        )
        
        return embed
