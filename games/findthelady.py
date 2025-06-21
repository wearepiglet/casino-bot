import random
import asyncio
import discord
from discord.ext import commands
from utils.embeds import EmbedBuilder

class FindTheLadyGame:
    """Manages a Find the Lady game."""
    
    def __init__(self, bet_amount: int, hard_mode: bool = False):
        self.bet_amount = bet_amount
        self.hard_mode = hard_mode
        self.num_cards = 5 if hard_mode else 3
        self.lady_position = random.randint(0, self.num_cards - 1)
        self.cards = ['👸' if i == self.lady_position else '👑' for i in range(self.num_cards)]
        self.shuffled = False
        self.game_over = False
        self.result = None
        self.payout = 0
    
    async def start_game(self, interaction: discord.Interaction):
        """Start the Find the Lady game."""
        # Show initial card positions
        initial_embed = self._get_initial_embed()
        message = await interaction.followup.send(embed=initial_embed)
        
        # Wait a moment, then shuffle
        await asyncio.sleep(3)
        
        # Show shuffling animation
        shuffle_embed = EmbedBuilder.game_result(
            "🃏 Find the Lady",
            "🔄 **Shuffling cards...** 🔄\n\nWatch carefully!"
        )
        await message.edit(embed=shuffle_embed)
        
        # Simulate shuffling
        await asyncio.sleep(2)
        
        # Show face-down cards and add reactions
        game_embed = self._get_game_embed()
        await message.edit(embed=game_embed)
        
        # Add number reactions
        for i in range(self.num_cards):
            await message.add_reaction(f"{i+1}\u20e3")  # Number emojis
        
        # Wait for user selection
        try:
            reaction, user = await interaction.client.wait_for(
                'reaction_add',
                timeout=30,
                check=lambda r, u: (
                    r.message.id == message.id and 
                    u.id == interaction.user.id and
                    str(r.emoji) in [f"{i+1}\u20e3" for i in range(self.num_cards)]
                )
            )
            
            # Get selected position
            selected = int(str(reaction.emoji)[0]) - 1
            self._process_selection(selected)
            
        except asyncio.TimeoutError:
            self.result = "timeout"
            self.payout = -self.bet_amount
        
        # Show final result
        final_embed = self._get_result_embed()
        await message.edit(embed=final_embed)
        
        return {
            'won': self.payout > 0,
            'payout': self.payout,
            'result': self.result
        }
    
    def _get_initial_embed(self) -> discord.Embed:
        """Get initial embed showing card positions."""
        title = f"🃏 Find the Lady ({'Hard Mode' if self.hard_mode else 'Easy Mode'})"
        
        card_display = " ".join(self.cards)
        description = f"Remember where the lady is!\n\n{card_display}\n\n"
        
        if self.hard_mode:
            description += "**Hard Mode:** 5 cards, 1:5 odds"
        else:
            description += "**Easy Mode:** 3 cards, 1:3 odds"
        
        embed = EmbedBuilder.game_result(title, description)
        return embed
    
    def _get_game_embed(self) -> discord.Embed:
        """Get game embed with face-down cards."""
        title = f"🃏 Find the Lady ({'Hard Mode' if self.hard_mode else 'Easy Mode'})"
        
        # Show face-down cards
        face_down_cards = " ".join(["🂠" for _ in range(self.num_cards)])
        numbers = " ".join([f"{i+1}" for i in range(self.num_cards)])
        
        description = f"Find the lady among the kings!\n\n{face_down_cards}\n{numbers}\n\n"
        description += "Click the number reaction for the card you think has the lady!"
        
        embed = EmbedBuilder.game_result(title, description)
        return embed
    
    def _process_selection(self, selected_position: int):
        """Process the user's card selection."""
        if selected_position == self.lady_position:
            self.result = "win"
            if self.hard_mode:
                self.payout = self.bet_amount * 4  # 1:5 becomes 4x profit
            else:
                self.payout = self.bet_amount * 2  # 1:3 becomes 2x profit
        else:
            self.result = "lose"
            self.payout = -self.bet_amount
    
    def _get_result_embed(self) -> discord.Embed:
        """Get result embed showing the outcome."""
        title = "🃏 Find the Lady - Result"
        
        # Show revealed cards
        revealed_cards = []
        for i in range(self.num_cards):
            if i == self.lady_position:
                revealed_cards.append("👸")
            else:
                revealed_cards.append("👑")
        
        card_display = " ".join(revealed_cards)
        numbers = " ".join([f"{i+1}" for i in range(self.num_cards)])
        
        description = f"{card_display}\n{numbers}\n\n"
        description += f"The lady was in position **{self.lady_position + 1}**!\n\n"
        
        if self.result == "win":
            description += f"🎉 **You found her! You won {self.payout:,} coins!**"
            color = 0x00ff00
        elif self.result == "timeout":
            description += "⏰ **Time's up! You didn't choose in time.**"
            color = 0xffff00
        else:
            description += f"💔 **Wrong card! You lost {abs(self.payout):,} coins!**"
            color = 0xff0000
        
        embed = EmbedBuilder.game_result(title, description, color)
        
        embed.add_field(
            name="💰 Payout",
            value=f"{self.payout:+,} coins",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Odds",
            value=f"1:{self.num_cards}",
            inline=True
        )
        
        return embed
