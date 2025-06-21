import random
import discord
from utils.embeds import EmbedBuilder
from utils.helpers import get_roulette_numbers

class RouletteGame:
    """Manages a roulette game."""
    
    def __init__(self, prediction: str, bet_amount: int):
        self.prediction = prediction.lower().strip()
        self.bet_amount = bet_amount
        self.result = None
        self.result_color = ""
        self.payout = 0
        self.odds = ""
        
        self.roulette_numbers = get_roulette_numbers()
        self.play()
    
    def play(self):
        """Play the roulette game."""
        # Generate result (0-36, where 37 represents 00)
        possible_outcomes = list(range(37)) + [37]  # 0-36 + 00
        self.result = random.choice(possible_outcomes)
        
        # Determine result color
        if self.result == 0 or self.result == 37:
            self.result_color = "green"
        elif self.result in self.roulette_numbers['red']:
            self.result_color = "red"
        else:
            self.result_color = "black"
        
        # Check if prediction wins
        self._calculate_payout()
    
    def _calculate_payout(self):
        """Calculate payout based on prediction."""
        prediction = self.prediction
        
        # Direct number prediction
        try:
            if prediction == "00":
                if self.result == 37:
                    self.payout = self.bet_amount * 35  # 35:1
                    self.odds = "35:1"
                    return
            else:
                pred_num = int(prediction)
                if 0 <= pred_num <= 36 and self.result == pred_num:
                    self.payout = self.bet_amount * 35  # 35:1
                    self.odds = "35:1"
                    return
        except ValueError:
            pass
        
        # Color predictions
        if prediction in ['red', 'black', 'green']:
            if prediction == self.result_color:
                if prediction == 'green':
                    self.payout = self.bet_amount * 17  # 17:1 for green
                    self.odds = "17:1"
                else:
                    self.payout = self.bet_amount  # 1:1 for red/black
                    self.odds = "1:1"
                return
        
        # Range predictions
        winning_ranges = {
            '1sthalf': self.roulette_numbers['1sthalf'],
            '2ndhalf': self.roulette_numbers['2ndhalf'],
            '1st12': self.roulette_numbers['1st12'],
            '2nd12': self.roulette_numbers['2nd12'],
            '3rd12': self.roulette_numbers['3rd12'],
            '1stcol': self.roulette_numbers['1stcol'],
            '2ndcol': self.roulette_numbers['2ndcol'],
            '3rdcol': self.roulette_numbers['3rdcol'],
            'col1': self.roulette_numbers['1stcol'],
            'col2': self.roulette_numbers['2ndcol'],
            'col3': self.roulette_numbers['3rdcol']
        }
        
        if prediction in winning_ranges:
            if self.result in winning_ranges[prediction]:
                if '12' in prediction:
                    self.payout = self.bet_amount * 2  # 2:1
                    self.odds = "2:1"
                elif 'col' in prediction or 'half' in prediction:
                    self.payout = self.bet_amount  # 1:1
                    self.odds = "1:1"
                return
        
        # Range betting (e.g., "1-18", "19-36")
        if '-' in prediction:
            try:
                start, end = map(int, prediction.split('-'))
                if start <= self.result <= end and self.result != 0 and self.result != 37:
                    # Calculate odds based on range size
                    range_size = end - start + 1
                    if range_size <= 18:  # Max half the board
                        self.payout = self.bet_amount  # 1:1
                        self.odds = "1:1"
                    return
            except ValueError:
                pass
        
        # Comma-separated numbers
        if ',' in prediction:
            try:
                numbers = [int(x.strip()) for x in prediction.split(',')]
                if self.result in numbers:
                    # Odds based on number of selections
                    multiplier = max(1, 36 // len(numbers))
                    self.payout = self.bet_amount * multiplier
                    self.odds = f"{multiplier}:1"
                    return
            except ValueError:
                pass
        
        # If no win condition met
        self.payout = -self.bet_amount
        self.odds = "Loss"
    
    def get_result_embed(self) -> discord.Embed:
        """Get embed showing game result."""
        title = "🎰 Roulette Result"
        
        # Format result display
        if self.result == 37:
            result_display = "00"
        else:
            result_display = str(self.result)
        
        # Color emoji
        color_emojis = {"red": "🔴", "black": "⚫", "green": "🟢"}
        color_emoji = color_emojis.get(self.result_color, "")
        
        description = f"The ball landed on: **{result_display}** {color_emoji}\n"
        description += f"You bet on: **{self.prediction}**\n\n"
        
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
            value=self.odds,
            inline=True
        )
        
        # Add betting options info
        betting_info = "**Betting Options:**\n"
        betting_info += "Numbers: 0-36, 00 (35:1)\n"
        betting_info += "Colors: red, black (1:1), green (17:1)\n"
        betting_info += "Ranges: 1stHalf, 2ndHalf (1:1)\n"
        betting_info += "Dozens: 1st12, 2nd12, 3rd12 (2:1)\n"
        betting_info += "Columns: 1stCol, 2ndCol, 3rdCol (1:1)"
        
        embed.add_field(
            name="📋 Betting Guide",
            value=betting_info,
            inline=False
        )
        
        return embed
