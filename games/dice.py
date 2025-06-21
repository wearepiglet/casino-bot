import random
import re
import discord
from utils.embeds import EmbedBuilder

class DiceGame:
    """Manages a dice rolling game."""
    
    def __init__(self, dice_type: str, prediction: int, bet_amount: int):
        self.dice_type = dice_type.lower()
        self.prediction = prediction
        self.bet_amount = bet_amount
        self.result = None
        self.payout = 0
        self.dice_max = self._get_dice_max()
        
        if self.dice_max:
            self.play()
    
    def _get_dice_max(self) -> int:
        """Get maximum value for dice type."""
        match = re.match(r'd(\d+)', self.dice_type)
        if match:
            return int(match.group(1))
        return 0
    
    def play(self):
        """Play the dice game."""
        if not self.dice_max:
            return
        
        self.result = random.randint(1, self.dice_max)
        
        if self.result == self.prediction:
            self.payout = self.bet_amount * (self.dice_max - 1)  # (dice_max):1 odds
        else:
            self.payout = -self.bet_amount
    
    def get_result_embed(self) -> discord.Embed:
        """Get embed showing game result."""
        title = f"🎲 {self.dice_type.upper()} Roll Result"
        
        # Get dice emoji based on result (for d6)
        dice_emojis = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        if self.dice_type == "d6" and 1 <= self.result <= 6:
            dice_emoji = dice_emojis[self.result]
        else:
            dice_emoji = "🎲"
        
        description = f"The {self.dice_type} landed on: **{self.result}** {dice_emoji}\n"
        description += f"You predicted: **{self.prediction}**\n\n"
        
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
            value=f"{self.dice_max}:1",
            inline=True
        )
        
        return embed
