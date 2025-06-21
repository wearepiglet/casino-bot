import random
import discord
from utils.embeds import EmbedBuilder

class SevensGame:
    """Manages a Sevens game."""
    
    def __init__(self, prediction: str, bet_amount: int):
        self.prediction = prediction.lower()
        self.bet_amount = bet_amount
        self.result = None
        self.payout = 0
        
        # Normalize prediction
        if self.prediction in ['seven']:
            self.prediction = '7'
        
        self.play()
    
    def play(self):
        """Play the Sevens game."""
        # Ball can land on 1-13
        self.result = random.randint(1, 13)
        
        # Check prediction
        if self.prediction == '7' and self.result == 7:
            self.payout = self.bet_amount * 10  # 10:1 odds
        elif self.prediction == 'low' and 1 <= self.result <= 6:
            self.payout = self.bet_amount * 2  # 2:1 odds
        elif self.prediction == 'high' and 8 <= self.result <= 13:
            self.payout = self.bet_amount * 2  # 2:1 odds
        else:
            self.payout = -self.bet_amount
    
    def get_result_embed(self) -> discord.Embed:
        """Get embed showing game result."""
        title = "🎱 Sevens"
        
        # Determine result category
        if self.result == 7:
            result_category = "Seven! 🎯"
        elif 1 <= self.result <= 6:
            result_category = "Low (1-6) 📉"
        else:
            result_category = "High (8-13) 📈"
        
        description = f"The ball landed on: **{self.result}**\n"
        description += f"Category: **{result_category}**\n"
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
        
        # Show odds based on prediction
        if self.prediction == '7':
            odds = "10:1"
        else:
            odds = "2:1"
        
        embed.add_field(
            name="🎯 Odds",
            value=odds,
            inline=True
        )
        
        # Add betting options
        betting_info = "**Betting Options:**\n"
        betting_info += "7 - Payout 10:1\n"
        betting_info += "Low (1-6) - Payout 2:1\n"
        betting_info += "High (8-13) - Payout 2:1"
        
        embed.add_field(
            name="📊 Payouts",
            value=betting_info,
            inline=False
        )
        
        return embed
