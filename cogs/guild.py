import discord
from discord.ext import commands
from discord import app_commands
import json
from typing import List, Optional

from utils.embeds import EmbedBuilder

class GuildConfigCog(commands.Cog):
    """Guild configuration commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    def _check_admin_permissions(self, interaction: discord.Interaction, guild_config: dict) -> bool:
        """Check if user has admin permissions for guild config."""
        # Guild owner can always configure
        if interaction.guild.owner_id == interaction.user.id:
            return True
        
        # Check if user has administrator permission
        if interaction.user.guild_permissions.administrator:
            return True
        
        # Check if user is in admin_ids list
        if interaction.user.id in guild_config.get('admin_ids', []):
            return True
        
        return False
    
    @app_commands.command(name="config", description="Show guild configuration")
    async def config_show(self, interaction: discord.Interaction):
        """Show current guild configuration."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            embed = discord.Embed(
                title="⚙️ Guild Configuration",
                description=f"Configuration for **{interaction.guild.name}**",
                color=0x0099ff
            )
            
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            # Basic settings
            embed.add_field(
                name="🔧 Basic Settings",
                value=f"**Prefix:** `{guild_config['prefix']}`\n"
                      f"**Force Commands:** {guild_config['force_commands']}\n"
                      f"**Update Messages:** {'Disabled' if guild_config['disable_update_messages'] else 'Enabled'}",
                inline=False
            )
            
            # Currency settings
            embed.add_field(
                name="💰 Currency Settings",
                value=f"**Cash Name:** {guild_config['cash_name']}\n"
                      f"**Cash Emoji:** {guild_config['cash_emoji']}\n"
                      f"**Crypto Name:** {guild_config['crypto_name']}\n"
                      f"**Crypto Emoji:** {guild_config['crypto_emoji']}",
                inline=False
            )
            
            # Channel restrictions
            allowed_channels = guild_config.get('allowed_channels', [])
            if allowed_channels:
                channel_mentions = []
                for channel_id in allowed_channels:
                    channel = interaction.guild.get_channel(channel_id)
                    if channel:
                        channel_mentions.append(channel.mention)
                
                if channel_mentions:
                    embed.add_field(
                        name="📺 Allowed Channels",
                        value="\n".join(channel_mentions),
                        inline=False
                    )
            else:
                embed.add_field(
                    name="📺 Allowed Channels",
                    value="All channels (no restrictions)",
                    inline=False
                )
            
            # Admin users
            admin_ids = guild_config.get('admin_ids', [])
            if admin_ids:
                admin_mentions = []
                for user_id in admin_ids:
                    user = interaction.guild.get_member(user_id)
                    if user:
                        admin_mentions.append(user.mention)
                    else:
                        admin_mentions.append(f"<@{user_id}> (not found)")
                
                embed.add_field(
                    name="👑 Config Admins",
                    value="\n".join(admin_mentions) if admin_mentions else "None",
                    inline=False
                )
            else:
                embed.add_field(
                    name="👑 Config Admins",
                    value="None (only server admins and owner)",
                    inline=False
                )
            
            # Show available commands
            embed.add_field(
                name="🔧 Configuration Commands",
                value="• `/config channel` - Set allowed channels\n"
                      "• `/config admin_ids add/delete` - Manage config admins\n"
                      "• `/config cash_name` - Set custom cash name\n"
                      "• `/config cashmoji` - Set custom cash emoji\n"
                      "• `/config crypto_name` - Set custom crypto name\n"
                      "• `/config cryptomoji` - Set custom crypto emoji\n"
                      "• `/config disable_update_messages` - Toggle update messages",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to show config: {str(e)}")
            )
    
    @app_commands.command(name="config_channels", description="Set allowed channels for bot commands")
    @app_commands.describe(
        channel1="First channel to allow",
        channel2="Second channel to allow (optional)",
        channel3="Third channel to allow (optional)",
        channel4="Fourth channel to allow (optional)",
        channel5="Fifth channel to allow (optional)"
    )
    async def config_channels(self, interaction: discord.Interaction,
                            channel1: discord.TextChannel = None,
                            channel2: discord.TextChannel = None,
                            channel3: discord.TextChannel = None,
                            channel4: discord.TextChannel = None,
                            channel5: discord.TextChannel = None):
        """Configure allowed channels."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            # Collect channels
            channels = [ch for ch in [channel1, channel2, channel3, channel4, channel5] if ch is not None]
            
            if not channels:
                # Clear channel restrictions
                channel_ids = []
                description = "All channels are now allowed (no restrictions)."
            else:
                # Set specific channels
                channel_ids = [ch.id for ch in channels]
                channel_mentions = [ch.mention for ch in channels]
                description = f"Bot commands are now restricted to:\n{', '.join(channel_mentions)}"
            
            # Update database
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET allowed_channels = ? WHERE guild_id = ?",
                    (json.dumps(channel_ids), interaction.guild.id)
                )
                await db.commit()
            
            embed = EmbedBuilder.success("Channels Updated", description)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to update channels: {str(e)}")
            )
    
    @app_commands.command(name="config_add_admin", description="Add a user as config admin")
    @app_commands.describe(user="User to add as config admin")
    async def config_add_admin(self, interaction: discord.Interaction, user: discord.Member):
        """Add config admin."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            admin_ids = guild_config.get('admin_ids', [])
            
            if user.id in admin_ids:
                await interaction.followup.send(
                    embed=EmbedBuilder.warning("Already Admin", f"{user.mention} is already a config admin!")
                )
                return
            
            admin_ids.append(user.id)
            
            # Update database
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET admin_ids = ? WHERE guild_id = ?",
                    (json.dumps(admin_ids), interaction.guild.id)
                )
                await db.commit()
            
            embed = EmbedBuilder.success(
                "Admin Added",
                f"{user.mention} has been added as a config admin!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to add admin: {str(e)}")
            )
    
    @app_commands.command(name="config_remove_admin", description="Remove a user from config admins")
    @app_commands.describe(user="User to remove from config admins")
    async def config_remove_admin(self, interaction: discord.Interaction, user: discord.Member):
        """Remove config admin."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            admin_ids = guild_config.get('admin_ids', [])
            
            if user.id not in admin_ids:
                await interaction.followup.send(
                    embed=EmbedBuilder.warning("Not Admin", f"{user.mention} is not a config admin!")
                )
                return
            
            admin_ids.remove(user.id)
            
            # Update database
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET admin_ids = ? WHERE guild_id = ?",
                    (json.dumps(admin_ids), interaction.guild.id)
                )
                await db.commit()
            
            embed = EmbedBuilder.success(
                "Admin Removed",
                f"{user.mention} has been removed from config admins!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to remove admin: {str(e)}")
            )
    
    @app_commands.command(name="config_cash_name", description="Set custom cash name")
    @app_commands.describe(name="New name for the currency")
    async def config_cash_name(self, interaction: discord.Interaction, name: str):
        """Set custom cash name."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            if len(name) > 24:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Name Too Long", "Cash name must be 24 characters or less!")
                )
                return
            
            # Update database
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET cash_name = ? WHERE guild_id = ?",
                    (name, interaction.guild.id)
                )
                await db.commit()
            
            embed = EmbedBuilder.success(
                "Cash Name Updated",
                f"Cash is now called **{name}** in this server!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to update cash name: {str(e)}")
            )
    
    @app_commands.command(name="config_cashmoji", description="Set custom cash emoji")
    @app_commands.describe(emoji="New emoji for the cash currency")
    async def config_cashmoji(self, interaction: discord.Interaction, emoji: str):
        """Set custom cash emoji."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            if len(emoji) > 10:  # Allow for custom Discord emojis
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Emoji Too Long", "Emoji must be a single emoji!")
                )
                return
            
            # Update database
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET cash_emoji = ? WHERE guild_id = ?",
                    (emoji, interaction.guild.id)
                )
                await db.commit()
            
            embed = EmbedBuilder.success(
                "Cash Emoji Updated",
                f"Cash emoji is now {emoji} in this server!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to update cash emoji: {str(e)}")
            )
    
    @app_commands.command(name="config_crypto_name", description="Set custom crypto name")
    @app_commands.describe(name="New name for the crypto currency")
    async def config_crypto_name(self, interaction: discord.Interaction, name: str):
        """Set custom crypto name."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            if len(name) > 24:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Name Too Long", "Crypto name must be 24 characters or less!")
                )
                return
            
            # Update database
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET crypto_name = ? WHERE guild_id = ?",
                    (name, interaction.guild.id)
                )
                await db.commit()
            
            embed = EmbedBuilder.success(
                "Crypto Name Updated",
                f"Crypto is now called **{name}** in this server!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to update crypto name: {str(e)}")
            )
    
    @app_commands.command(name="config_cryptomoji", description="Set custom crypto emoji")
    @app_commands.describe(emoji="New emoji for the crypto currency")
    async def config_cryptomoji(self, interaction: discord.Interaction, emoji: str):
        """Set custom crypto emoji."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            if len(emoji) > 10:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Emoji Too Long", "Emoji must be a single emoji!")
                )
                return
            
            # Update database
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET crypto_emoji = ? WHERE guild_id = ?",
                    (emoji, interaction.guild.id)
                )
                await db.commit()
            
            embed = EmbedBuilder.success(
                "Crypto Emoji Updated",
                f"Crypto emoji is now {emoji} in this server!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to update crypto emoji: {str(e)}")
            )
    
    @app_commands.command(name="config_disable_updates", description="Toggle update messages")
    @app_commands.describe(enabled="Whether update messages should be enabled")
    async def config_disable_updates(self, interaction: discord.Interaction, enabled: bool):
        """Toggle update messages."""
        try:
            await interaction.response.defer()
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if not self._check_admin_permissions(interaction, guild_config):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Permission Denied", "You need administrator permissions or be added as a config admin!")
                )
                return
            
            # Update database (note: enabled=True means disable_update_messages=False)
            disable_updates = not enabled
            
            async with self.bot.db.db.connect() as db:
                await db.execute(
                    "UPDATE guild_config SET disable_update_messages = ? WHERE guild_id = ?",
                    (disable_updates, interaction.guild.id)
                )
                await db.commit()
            
            status = "enabled" if enabled else "disabled"
            embed = EmbedBuilder.success(
                "Update Messages Updated",
                f"Update messages are now **{status}** for this server!"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to update setting: {str(e)}")
            )
    
    @app_commands.command(name="updates", description="Show latest bot updates")
    async def updates(self, interaction: discord.Interaction):
        """Show bot updates."""
        try:
            await interaction.response.defer()
            
            embed = discord.Embed(
                title="🔄 Bot Updates",
                description="Latest updates and changes to the gambling bot!",
                color=0x0099ff
            )
            
            # Sample update log (you can replace this with actual updates)
            updates_text = (
                "**Version 2.1.0** - `2024-01-15`\n"
                "• Added new mining system with prestige\n"
                "• Improved blackjack game mechanics\n"
                "• Fixed crash game multiplier display\n"
                "• Enhanced guild configuration options\n\n"
                
                "**Version 2.0.5** - `2024-01-10`\n"
                "• Added race games with multiple animal types\n"
                "• Improved higher or lower game interface\n"
                "• Fixed coinflip result display\n"
                "• Added gift system for players\n\n"
                
                "**Version 2.0.0** - `2024-01-05`\n"
                "• Complete rewrite with slash commands\n"
                "• Added comprehensive gambling games\n"
                "• Implemented player economy system\n"
                "• Added leaderboards and statistics"
            )
            
            embed.add_field(
                name="📋 Recent Updates",
                value=updates_text,
                inline=False
            )
            
            embed.add_field(
                name="🎯 Coming Soon",
                value="• Tournament system\n"
                      "• More mining features\n"
                      "• Advanced betting options\n"
                      "• Player achievements",
                inline=False
            )
            
            embed.set_footer(text="Stay tuned for more exciting features!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to show updates: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(GuildConfigCog(bot))
