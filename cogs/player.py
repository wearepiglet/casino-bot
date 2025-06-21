import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime, timedelta
from utils.embeds import EmbedBuilder
from utils.helpers import format_currency, format_time_remaining, parse_bet_amount

class PlayerCog(commands.Cog):
    """Player-related commands like profile, daily rewards, etc."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="profile", description="Show your player profile")
    @app_commands.describe(page="The sub-page to show")
    async def profile(self, interaction: discord.Interaction, page: str = None):
        """Show player profile."""
        try:
            await interaction.response.defer()
            
            player = await self.bot.db.get_player(interaction.user.id, interaction.guild.id)
            embed = EmbedBuilder.player_profile(player, interaction.user)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to get profile: {str(e)}")
            )
    
    @app_commands.command(name="daily", description="Collect your daily cash reward")
    async def daily(self, interaction: discord.Interaction):
        """Collect daily reward."""
        try:
            await interaction.response.defer()
            
            # Check cooldown
            cooldown = await self.bot.db.check_cooldown(
                interaction.user.id, interaction.guild.id, "daily"
            )
            
            if cooldown:
                time_left = format_time_remaining(cooldown)
                embed = EmbedBuilder.warning(
                    "Daily Reward",
                    f"You can collect your daily reward in {time_left}"
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Generate reward
            reward = random.randint(self.bot.config.DAILY_MIN, self.bot.config.DAILY_MAX)
            
            # Update player cash
            await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, reward)
            
            # Set cooldown
            await self.bot.db.set_cooldown(
                interaction.user.id, interaction.guild.id, "daily", self.bot.config.DAILY_COOLDOWN
            )
            
            embed = EmbedBuilder.success(
                "Daily Reward Collected!",
                f"You received {format_currency(reward)}!"
            )
            embed.add_field(
                name="💰 Amount",
                value=format_currency(reward),
                inline=True
            )
            embed.add_field(
                name="⏰ Next Daily",
                value="24 hours",
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to collect daily: {str(e)}")
            )
    
    @app_commands.command(name="weekly", description="Collect your weekly cash reward")
    async def weekly(self, interaction: discord.Interaction):
        """Collect weekly reward."""
        try:
            await interaction.response.defer()
            
            cooldown = await self.bot.db.check_cooldown(
                interaction.user.id, interaction.guild.id, "weekly"
            )
            
            if cooldown:
                time_left = format_time_remaining(cooldown)
                embed = EmbedBuilder.warning(
                    "Weekly Reward",
                    f"You can collect your weekly reward in {time_left}"
                )
                await interaction.followup.send(embed=embed)
                return
            
            reward = random.randint(self.bot.config.WEEKLY_MIN, self.bot.config.WEEKLY_MAX)
            await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, reward)
            await self.bot.db.set_cooldown(
                interaction.user.id, interaction.guild.id, "weekly", self.bot.config.WEEKLY_COOLDOWN
            )
            
            embed = EmbedBuilder.success(
                "Weekly Reward Collected!",
                f"You received {format_currency(reward)}!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to collect weekly: {str(e)}")
            )
    
    @app_commands.command(name="monthly", description="Collect your monthly cash reward")
    async def monthly(self, interaction: discord.Interaction):
        """Collect monthly reward."""
        try:
            await interaction.response.defer()
            
            cooldown = await self.bot.db.check_cooldown(
                interaction.user.id, interaction.guild.id, "monthly"
            )
            
            if cooldown:
                time_left = format_time_remaining(cooldown)
                embed = EmbedBuilder.warning(
                    "Monthly Reward",
                    f"You can collect your monthly reward in {time_left}"
                )
                await interaction.followup.send(embed=embed)
                return
            
            reward = random.randint(self.bot.config.MONTHLY_MIN, self.bot.config.MONTHLY_MAX)
            await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, reward)
            await self.bot.db.set_cooldown(
                interaction.user.id, interaction.guild.id, "monthly", self.bot.config.MONTHLY_COOLDOWN
            )
            
            embed = EmbedBuilder.success(
                "Monthly Reward Collected!",
                f"You received {format_currency(reward)}!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to collect monthly: {str(e)}")
            )
    
    @app_commands.command(name="work", description="Work for some cash")
    async def work(self, interaction: discord.Interaction):
        """Work for cash."""
        try:
            await interaction.response.defer()
            
            cooldown = await self.bot.db.check_cooldown(
                interaction.user.id, interaction.guild.id, "work"
            )
            
            if cooldown:
                time_left = format_time_remaining(cooldown)
                embed = EmbedBuilder.warning(
                    "Work Cooldown",
                    f"You can work again in {time_left}"
                )
                await interaction.followup.send(embed=embed)
                return
            
            reward = random.randint(self.bot.config.WORK_MIN, self.bot.config.WORK_MAX)
            await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, reward)
            await self.bot.db.set_cooldown(
                interaction.user.id, interaction.guild.id, "work", self.bot.config.WORK_COOLDOWN
            )
            
            work_messages = [
                "You completed your shift at the casino!",
                "You dealt cards at the poker table!",
                "You worked security at the gambling hall!",
                "You cleaned the slot machines!",
                "You counted chips in the vault!"
            ]
            
            embed = EmbedBuilder.success(
                "Work Complete!",
                f"{random.choice(work_messages)}\nYou earned {format_currency(reward)}!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to work: {str(e)}")
            )
    
    @app_commands.command(name="overtime", description="Work overtime for extra cash")
    async def overtime(self, interaction: discord.Interaction):
        """Work overtime for extra cash."""
        try:
            await interaction.response.defer()
            
            cooldown = await self.bot.db.check_cooldown(
                interaction.user.id, interaction.guild.id, "overtime"
            )
            
            if cooldown:
                time_left = format_time_remaining(cooldown)
                embed = EmbedBuilder.warning(
                    "Overtime Cooldown",
                    f"You can work overtime again in {time_left}"
                )
                await interaction.followup.send(embed=embed)
                return
            
            reward = random.randint(self.bot.config.OVERTIME_MIN, self.bot.config.OVERTIME_MAX)
            await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, reward)
            await self.bot.db.set_cooldown(
                interaction.user.id, interaction.guild.id, "overtime", self.bot.config.OVERTIME_COOLDOWN
            )
            
            embed = EmbedBuilder.success(
                "Overtime Complete!",
                f"You worked extra hours and earned {format_currency(reward)}!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to work overtime: {str(e)}")
            )
    
    @app_commands.command(name="send", description="Send money to another player")
    @app_commands.describe(
        recipient="The player to send money to",
        amount="The amount to send"
    )
    async def send_money(self, interaction: discord.Interaction, recipient: discord.Member, amount: str):
        """Send money to another player."""
        try:
            await interaction.response.defer()
            
            if recipient.bot:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "You cannot send money to bots!")
                )
                return
            
            if recipient.id == interaction.user.id:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "You cannot send money to yourself!")
                )
                return
            
            # Get sender's cash
            player = await self.bot.db.get_player(interaction.user.id, interaction.guild.id)
            player_cash = player['cash']
            
            # Parse amount
            send_amount = parse_bet_amount(amount, player_cash)
            
            if not send_amount or send_amount <= 0:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "Invalid amount!")
                )
                return
            
            if send_amount > player_cash:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "You don't have enough money!")
                )
                return
            
            # Calculate tax (5% for now)
            tax = int(send_amount * 0.05)
            final_amount = send_amount - tax
            
            # Transfer money
            await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, -send_amount)
            await self.bot.db.update_player_cash(recipient.id, interaction.guild.id, final_amount)
            
            embed = EmbedBuilder.success(
                "Money Sent!",
                f"You sent {format_currency(send_amount)} to {recipient.mention}!\n"
                f"Tax: {format_currency(tax)}\n"
                f"They received: {format_currency(final_amount)}"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to send money: {str(e)}")
            )
    
    @app_commands.command(name="lookup", description="Look up another player's stats")
    @app_commands.describe(
        user="The user to look up",
        page="The sub-page to show"
    )
    async def lookup(self, interaction: discord.Interaction, user: discord.Member, page: str = None):
        """Look up another player's stats."""
        try:
            await interaction.response.defer()
            
            if user.bot:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "Cannot lookup bot accounts!")
                )
                return
            
            player = await self.bot.db.get_player(user.id, interaction.guild.id)
            embed = EmbedBuilder.player_profile(player, user)
            embed.title = f"👁️ {user.display_name}'s Profile (Lookup)"
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to lookup player: {str(e)}")
            )
    
    @app_commands.command(name="cooldowns", description="Show your active cooldowns")
    @app_commands.describe(detailed="Show exact expiry times")
    async def cooldowns(self, interaction: discord.Interaction, detailed: bool = False):
        """Show active cooldowns."""
        try:
            await interaction.response.defer()
            
            # Check various cooldowns
            cooldown_commands = ["daily", "weekly", "monthly", "work", "overtime", "spin"]
            active_cooldowns = []
            
            for cmd in cooldown_commands:
                cooldown = await self.bot.db.check_cooldown(
                    interaction.user.id, interaction.guild.id, cmd
                )
                if cooldown:
                    if detailed:
                        time_str = cooldown.strftime("%Y-%m-%d %H:%M:%S UTC")
                    else:
                        time_str = format_time_remaining(cooldown)
                    active_cooldowns.append(f"**{cmd.title()}:** {time_str}")
            
            if not active_cooldowns:
                embed = EmbedBuilder.info("Cooldowns", "No active cooldowns! 🎉")
            else:
                embed = EmbedBuilder.info("Active Cooldowns", "\n".join(active_cooldowns))
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to get cooldowns: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
