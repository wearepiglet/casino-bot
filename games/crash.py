import random
import asyncio
import discord
from discord.ext import commands
from utils.embeds import EmbedBuilder

class CrashGame:
    """Manages a crash game."""
    
    def __init__(self, bet_amount: int, hard_mode: bool = False):
        self.bet_amount = bet_amount
        self.hard_mode = hard_mode
        self.multiplier = 1.0
        self.crashed = False
        self.cashed_out = False
        self.game_active = True
        self.start_time = None
        self.max_duration = 120  # 2 minutes max
        
    async def start_game(self, interaction: discord.Interaction):
        """Start the crash game."""
        self.start_time = asyncio.get_event_loop().time()
        
        if self.hard_mode:
            embed = EmbedBuilder.game_result(
                "💥 Crash Game (Hard Mode)",
                "Game started! You have 2 minutes to cash out.\n"
                "React with 🛑 when you want to cash out!\n\n"
                "**Hard Mode:** Multiplier and crash status are hidden!"
            )
        else:
            embed = EmbedBuilder.game_result(
                "💥 Crash Game",
                f"Current multiplier: **{self.multiplier:.2f}x**\n"
                "React with 🛑 to cash out before it crashes!\n\n"
                "💡 10% chance to crash on each multiplier increase"
            )
        
        message = await interaction.followup.send(embed=embed)
        await message.add_reaction('🛑')
        
        # Game loop
        await self._run_game_loop(message, interaction)
        
        return self._get_final_result()
    
    async def _run_game_loop(self, message: discord.Message, interaction: discord.Interaction):
        """Run the main game loop."""
        while self.game_active and not self.crashed and not self.cashed_out:
            await asyncio.sleep(2 if not self.hard_mode else 1)  # Update every 2 seconds (1 in hard mode)
            
            # Check for timeout
            if asyncio.get_event_loop().time() - self.start_time > self.max_duration:
                self.crashed = True
                break
            
            # 10% chance to crash
            if random.random() < 0.1:
                self.crashed = True
                break
            
            # Increase multiplier
            if self.hard_mode:
                self.multiplier += random.uniform(0.1, 0.3)  # Faster in hard mode
            else:
                self.multiplier += random.uniform(0.05, 0.15)
            
            # Update embed (only in easy mode)
            if not self.hard_mode:
                embed = EmbedBuilder.game_result(
                    "💥 Crash Game",
                    f"Current multiplier: **{self.multiplier:.2f}x**\n"
                    "React with 🛑 to cash out before it crashes!\n\n"
                    "💡 10% chance to crash on each multiplier increase"
                )
                
                try:
                    await message.edit(embed=embed)
                except discord.NotFound:
                    break
            
            # Check for user reaction
            try:
                reaction, user = await interaction.client.wait_for(
                    'reaction_add',
                    timeout=0.1,
                    check=lambda r, u: r.message.id == message.id and str(r.emoji) == '🛑' and u.id == interaction.user.id
                )
                self.cashed_out = True
                break
            except asyncio.TimeoutError:
                continue
        
        # Final update
        final_embed = self._get_final_embed()
        try:
            await message.edit(embed=final_embed)
        except discord.NotFound:
            pass
    
    def _get_final_result(self) -> dict:
        """Get the final game result."""
        if self.cashed_out:
            payout = int(self.bet_amount * self.multiplier) - self.bet_amount
            return {
                'won': True,
                'payout': payout,
                'multiplier': self.multiplier,
                'result': f"Cashed out at {self.multiplier:.2f}x"
            }
        else:
            return {
                'won': False,
                'payout': -self.bet_amount,
                'multiplier': self.multiplier,
                'result': f"Crashed at {self.multiplier:.2f}x"
            }
    
    def _get_final_embed(self) -> discord.Embed:
        """Get the final game embed."""
        if self.cashed_out:
            title = "🛑 Cashed Out!"
            payout = int(self.bet_amount * self.multiplier) - self.bet_amount
            description = f"You cashed out at **{self.multiplier:.2f}x**!\n"
            description += f"**You won {payout:,} coins!**"
            color = 0x00ff00
        else:
            title = "💥 CRASHED!"
            description = f"The game crashed at **{self.multiplier:.2f}x**!\n"
            description += f"**You lost {self.bet_amount:,} coins!**"
            color = 0xff0000
        
        embed = EmbedBuilder.game_result(title, description, color)
        
        embed.add_field(
            name="🎯 Final Multiplier",
            value=f"{self.multiplier:.2f}x",
            inline=True
        )
        
        if self.cashed_out:
            payout = int(self.bet_amount * self.multiplier) - self.bet_amount
            embed.add_field(
                name="💰 Winnings",
                value=f"+{payout:,} coins",
                inline=True
            )
        else:
            embed.add_field(
                name="💸 Loss",
                value=f"-{self.bet_amount:,} coins",
                inline=True
            )
        
        return embed
