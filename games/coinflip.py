import random
import discord
from utils.embeds import EmbedBuilder

class CoinflipGame:
    """Manages a coinflip game."""
    
    def __init__(self, prediction: str, bet_amount: int):
        self.prediction = prediction.lower()
        self.bet_amount = bet_amount
        self.result = None
        self.payout = 0
        
        # Normalize prediction
        if self.prediction in ['h', 'head']:
            self.prediction = 'heads'
        elif self.prediction in ['t', 'tail']:
            self.prediction = 'tails'
        
        self.play()
    
    def play(self):
        """Play the coinflip game."""
        outcomes = ['heads', 'tails']
        self.result = random.choice(outcomes)
        
        if self.result == self.prediction:
            self.payout = self.bet_amount  # 1:1 odds
        else:
            self.payout = -self.bet_amount
    
    def get_result_embed(self) -> discord.Embed:
        """Get embed showing game result."""
        title = "🪙 Coinflip Result"
        
        # Choose emoji based on result
        coin_emoji = "🟡" if self.result == "heads" else "🔘"
        
        description = f"The coin landed on: **{self.result.title()}** {coin_emoji}\n"
        description += f"You predicted: **{self.prediction.title()}**\n\n"
        
        if self.payout > 0:
            description += f"🎉 **You won {self.payout:,} coins!**"
            color = 0x00ff00
        else:
            description += f"💔 **You lost {abs(self.payout):,} coins!**"
            color = 0xff0000
        
        embed = EmbedBuilder.game_result(title, description, color)
        
        embed.add_field(
            name="💰 Payout",
            value=f"{self.payout:+,} coins",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Odds",
            value="1:1",
            inline=True
        )
        
        return embed
