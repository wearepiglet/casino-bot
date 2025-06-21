import random
import discord
from utils.embeds import EmbedBuilder

class RockPaperScissorsGame:
    """Manages a Rock Paper Scissors game."""
    
    def __init__(self, player_choice: str, bet_amount: int):
        self.player_choice = player_choice.lower()
        self.bet_amount = bet_amount
        self.bot_choice = None
        self.result = None
        self.payout = 0
        
        # Normalize player choice
        choice_map = {
            'r': 'rock',
            'p': 'paper', 
            's': 'scissors'
        }
        self.player_choice = choice_map.get(self.player_choice, self.player_choice)
        
        self.play()
    
    def play(self):
        """Play Rock Paper Scissors."""
        choices = ['rock', 'paper', 'scissors']
        self.bot_choice = random.choice(choices)
        
        # Determine winner
        if self.player_choice == self.bot_choice:
            self.result = "tie"
            self.payout = 0  # Tie returns bet
        elif (
            (self.player_choice == 'rock' and self.bot_choice == 'scissors') or
            (self.player_choice == 'paper' and self.bot_choice == 'rock') or
            (self.player_choice == 'scissors' and self.bot_choice == 'paper')
        ):
            self.result = "win"
            self.payout = int(self.bet_amount * 0.5)  # 3:2 odds
        else:
            self.result = "lose"
            self.payout = -self.bet_amount
    
    def _get_emoji(self, choice: str) -> str:
        """Get emoji for choice."""
        emojis = {
            'rock': '🪨',
            'paper': '📄',
            'scissors': '✂️'
        }
        return emojis.get(choice, choice)
    
    def get_result_embed(self) -> discord.Embed:
        """Get embed showing game result."""
        title = "✂️ Rock Paper Scissors"
        
        player_emoji = self._get_emoji(self.player_choice)
        bot_emoji = self._get_emoji(self.bot_choice)
        
        description = f"You chose: **{self.player_choice.title()}** {player_emoji}\n"
        description += f"Bot chose: **{self.bot_choice.title()}** {bot_emoji}\n\n"
        
        if self.result == "win":
            description += f"🎉 **You win! You won {self.payout:,} coins!**"
            color = 0x00ff00
        elif self.result == "tie":
            description += "🤝 **It's a tie! Your bet is returned.**"
            color = 0xffff00
        else:
            description += f"💔 **You lose! You lost {abs(self.payout):,} coins!**"
            color = 0xff0000
        
        embed = EmbedBuilder.game_result(title, description, color)
        
        embed.add_field(
            name="💰 Payout",
            value=f"{self.payout:+,} coins" if self.payout != 0 else "Bet returned",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Odds",
            value="3:2",
            inline=True
        )
        
        # Add rules
        embed.add_field(
            name="📋 Rules",
            value="Rock beats Scissors\nPaper beats Rock\nScissors beats Paper",
            inline=False
        )
        
        return embed
