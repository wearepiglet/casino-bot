import discord
from discord.ext import commands
import asyncio
import logging
from database import Database
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)

class GamblingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.db = Database()
        self.config = Config()
        
    async def setup_hook(self):
        """Load all cogs and sync commands."""
        try:
            # Initialize database
            await self.db.initialize()
            
            # Load cogs
            cogs = [
                'cogs.player',
                'cogs.economy', 
                'cogs.games',
                'cogs.mining',
                'cogs.guild',
                'cogs.lottery'
            ]
            
            for cog in cogs:
                try:
                    await self.load_extension(cog)
                    print(f"Loaded cog: {cog}")
                except Exception as e:
                    print(f"Failed to load cog {cog}: {e}")
            
            # Sync slash commands
            try:
                synced = await self.tree.sync()
                print(f"Synced {len(synced)} command(s)")
            except Exception as e:
                print(f"Failed to sync commands: {e}")
                
        except Exception as e:
            print(f"Error in setup_hook: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot activity
        activity = discord.Game(name="🎰 Gambling Games | /help")
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild."""
        print(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Initialize guild in database if needed
        await self.db.ensure_guild_exists(guild.id)
    
    async def on_command_error(self, ctx, error):
        """Global error handler."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        print(f"Command error: {error}")
        
        if hasattr(ctx, 'send'):
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(error)}",
                color=0xff0000
            )
            await ctx.send(embed=embed, ephemeral=True)
