import random
import asyncio
import discord
from utils.embeds import EmbedBuilder

class RaceGame:
    """Manages a racing game."""
    
    def __init__(self, racer_type: str, prediction: int, bet_amount: int):
        self.racer_type = racer_type.lower()
        self.prediction = prediction
        self.bet_amount = bet_amount
        self.winner = None
        self.payout = 0
        
        # Race configurations
        self.race_configs = {
            't': {'name': 'Turtle', 'emoji': '🐢', 'racers': 3, 'odds': 3},
            'turtle': {'name': 'Turtle', 'emoji': '🐢', 'racers': 3, 'odds': 3},
            'd': {'name': 'Dog', 'emoji': '🐕', 'racers': 5, 'odds': 5},
            'dog': {'name': 'Dog', 'emoji': '🐕', 'racers': 5, 'odds': 5},
            'h': {'name': 'Horse', 'emoji': '🏇', 'racers': 8, 'odds': 8},
            'horse': {'name': 'Horse', 'emoji': '🏇', 'racers': 8, 'odds': 8},
            'di': {'name': 'Dinosaur', 'emoji': '🦖', 'racers': 12, 'odds': 12},
            'dinosaur': {'name': 'Dinosaur', 'emoji': '🦖', 'racers': 12, 'odds': 12}
        }
        
        self.config = self.race_configs.get(self.racer_type)
        if not self.config:
            return
        
        self.num_racers = self.config['racers']
        self.odds = self.config['odds']
    
    async def start_race(self, interaction: discord.Interaction):
        """Start the race with animation."""
        if not self.config:
            return {'success': False, 'message': 'Invalid racer type'}
        
        if not (1 <= self.prediction <= self.num_racers):
            return {'success': False, 'message': f'Prediction must be between 1 and {self.num_racers}'}
        
        # Initialize race
        race_embed = self._get_pre_race_embed()
        message = await interaction.followup.send(embed=race_embed)
        
        # Countdown
        for i in range(3, 0, -1):
            countdown_embed = EmbedBuilder.game_result(
                f"🏁 {self.config['name']} Race",
                f"Race starting in **{i}**..."
            )
            await message.edit(embed=countdown_embed)
            await asyncio.sleep(1)
        
        # Start race animation
        positions = [0] * self.num_racers
        track_length = 10
        
        while max(positions) < track_length:
            # Update positions randomly
            for i in range(self.num_racers):
                if random.random() < 0.7:  # 70% chance to move forward
                    positions[i] += random.randint(1, 2)
            
            # Show race progress
            race_embed = self._get_race_progress_embed(positions, track_length)
            await message.edit(embed=race_embed)
            await asyncio.sleep(1)
        
        # Determine winner
        self.winner = positions.index(max(positions)) + 1
        
        # Calculate payout
        if self.winner == self.prediction:
            self.payout = self.bet_amount * (self.odds - 1)  # Profit (odds - 1):1
        else:
            self.payout = -self.bet_amount
        
        # Show final result
        final_embed = self._get_result_embed()
        await message.edit(embed=final_embed)
        
        return {
            'success': True,
            'won': self.payout > 0,
            'payout': self.payout,
            'winner': self.winner
        }
    
    def _get_pre_race_embed(self) -> discord.Embed:
        """Get embed before race starts."""
        title = f"🏁 {self.config['name']} Race"
        
        description = f"**Racers:** {self.num_racers} {self.config['emoji']}\n"
        description += f"**Your Pick:** Racer #{self.prediction}\n"
        description += f"**Bet:** {self.bet_amount:,} coins\n"
        description += f"**Odds:** {self.odds}:1\n\n"
        description += "🏁 Get ready to race! 🏁"
        
        embed = EmbedBuilder.game_result(title, description)
        return embed
    
    def _get_race_progress_embed(self, positions: list, track_length: int) -> discord.Embed:
        """Get embed showing race progress."""
        title = f"🏁 {self.config['name']} Race - In Progress"
        
        track_display = ""
        for i, pos in enumerate(positions):
            racer_num = i + 1
            track = "🏁" + "─" * (track_length - 1)
            
            # Place racer on track
            if pos >= track_length:
                pos = track_length - 1
            
            track_list = list(track)
            track_list[pos] = self.config['emoji']
            track_visual = "".join(track_list)
            
            # Highlight user's pick
            if racer_num == self.prediction:
                track_display += f"**#{racer_num}:** {track_visual} ⭐\n"
            else:
                track_display += f"#{racer_num}: {track_visual}\n"
        
        embed = EmbedBuilder.game_result(title, track_display)
        return embed
    
    def _get_result_embed(self) -> discord.Embed:
        """Get embed showing race result."""
        title = f"🏁 {self.config['name']} Race - Results"
        
        description = f"🏆 **Winner: Racer #{self.winner}** {self.config['emoji']}\n"
        description += f"Your pick: **Racer #{self.prediction}**\n\n"
        
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
            value=f"{self.odds}:1",
            inline=True
        )
        
        # Show all racer types
        racer_info = "**Available Races:**\n"
        racer_info += "🐢 Turtle (3 racers, 3:1)\n"
        racer_info += "🐕 Dog (5 racers, 5:1)\n"
        racer_info += "🏇 Horse (8 racers, 8:1)\n"
        racer_info += "🦖 Dinosaur (12 racers, 12:1)"
        
        embed.add_field(
            name="🏆 Race Types",
            value=racer_info,
            inline=False
        )
        
        return embed
