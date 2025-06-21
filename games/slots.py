import random
import discord
from utils.embeds import EmbedBuilder

class SlotsGame:
    """Manages a slots game."""
    
    def __init__(self, bet_amount: int):
        self.bet_amount = bet_amount
        self.result = []
        self.payout = 0
        self.winning_combination = ""
        
        # Slot symbols and their rarities (higher weight = more common)
        self.symbols = {
            '🍒': 30,  # Cherry - most common
            '🍋': 25,  # Lemon
            '🍊': 20,  # Orange  
            '🍇': 15,  # Grapes
            '🔔': 8,   # Bell
            '⭐': 2    # Star - rarest
        }
        
        # Payout table
        self.payouts = {
            '⭐': {'3': 500, '2': 25},
            '🔔': {'3': 25, '2': 10},
            '🍇': {'3': 5, '2': 3},
            '🍊': {'3': 3, '2': 2},
            '🍋': {'3': 2, '2': 1},
            '🍒': {'3': 1, '2': 1}
        }
        
        self.play()
    
    def _get_weighted_symbol(self) -> str:
        """Get a random symbol based on weights."""
        symbols = list(self.symbols.keys())
        weights = list(self.symbols.values())
        return random.choices(symbols, weights=weights)[0]
    
    def play(self):
        """Play the slots game."""
        # Spin 3 reels
        self.result = [self._get_weighted_symbol() for _ in range(3)]
        
        # Check for winning combinations
        self._calculate_payout()
    
    def _calculate_payout(self):
        """Calculate payout based on results."""
        symbol_counts = {}
        for symbol in self.result:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Find best payout (highest multiplier)
        best_payout = 0
        best_combination = ""
        
        for symbol, count in symbol_counts.items():
            if symbol in self.payouts:
                if count >= 3 and '3' in self.payouts[symbol]:
                    multiplier = self.payouts[symbol]['3']
                    if multiplier > best_payout:
                        best_payout = multiplier
                        best_combination = f"3x {symbol}"
                elif count >= 2 and '2' in self.payouts[symbol]:
                    multiplier = self.payouts[symbol]['2']
                    if multiplier > best_payout:
                        best_payout = multiplier
                        best_combination = f"2x {symbol}"
        
        if best_payout > 0:
            self.payout = self.bet_amount * best_payout
            self.winning_combination = best_combination
        else:
            self.payout = -self.bet_amount
            self.winning_combination = "No match"
    
    def get_result_embed(self) -> discord.Embed:
        """Get embed showing game result."""
        title = "🎰 Slot Machine"
        
        # Show the slot result
        slot_display = " | ".join(self.result)
        
        description = f"**{slot_display}**\n\n"
        
        if self.payout > 0:
            description += f"🎉 **{self.winning_combination}!**\n"
            description += f"**You won {self.payout:,} coins!**"
            color = 0x00ff00
        else:
            description += f"💔 **No match!**\n"
            description += f"**You lost {abs(self.payout):,} coins!**"
            color = 0xff0000
        
        embed = EmbedBuilder.game_result(title, description, color)
        
        embed.add_field(
            name="💰 Result",
            value=f"{self.winning_combination}",
            inline=True
        )
        
        embed.add_field(
            name="💸 Payout",
            value=f"{self.payout:+,} coins",
            inline=True
        )
        
        # Add payout table
        payout_info = "**Payout Table:**\n"
        payout_info += "⭐ 3x = 500:1, 2x = 25:1\n"
        payout_info += "🔔 3x = 25:1, 2x = 10:1\n"
        payout_info += "🍇 3x = 5:1, 2x = 3:1\n"
        payout_info += "🍊 3x = 3:1, 2x = 2:1\n"
        payout_info += "🍋 3x = 2:1, 2x = 1:1\n"
        payout_info += "🍒 3x = 1:1, 2x = 1:1"
        
        embed.add_field(
            name="📊 Payouts",
            value=payout_info,
            inline=False
        )
        
        return embed
