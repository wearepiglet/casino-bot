import discord
from config import Config

class EmbedBuilder:
    """Helper class for building Discord embeds."""
    
    @staticmethod
    def success(title: str, description: str = None) -> discord.Embed:
        """Create a success embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=Config.COLOR_SUCCESS
        )
        return embed
    
    @staticmethod
    def error(title: str, description: str = None) -> discord.Embed:
        """Create an error embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=Config.COLOR_ERROR
        )
        return embed
    
    @staticmethod
    def warning(title: str, description: str = None) -> discord.Embed:
        """Create a warning embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=Config.COLOR_WARNING
        )
        return embed
    
    @staticmethod
    def info(title: str, description: str = None) -> discord.Embed:
        """Create an info embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=Config.COLOR_INFO
        )
        return embed
    
    @staticmethod
    def neutral(title: str, description: str = None) -> discord.Embed:
        """Create a neutral embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=Config.COLOR_NEUTRAL
        )
        return embed