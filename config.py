import os

class Config:
    """Configuration settings for the gambling bot."""
    
    # Bot settings
    BOT_TOKEN = os.getenv("DISCORD_TOKEN")
    DEFAULT_PREFIX = "!"
    
    # Economy settings
    STARTING_CASH = 1000
    MAX_BET_PERCENTAGE = 0.5  # Max 50% of cash in one bet
    
    # Daily rewards
    DAILY_MIN = 1000
    DAILY_MAX = 5000
    WEEKLY_MIN = 5000
    WEEKLY_MAX = 10000
    MONTHLY_MIN = 100000
    MONTHLY_MAX = 500000
    YEARLY_MIN = 10000000
    YEARLY_MAX = 50000000
    
    # Work rewards
    WORK_MIN = 100
    WORK_MAX = 500
    OVERTIME_MIN = 500
    OVERTIME_MAX = 1000
    
    # Cooldowns (in hours)
    DAILY_COOLDOWN = 24
    WEEKLY_COOLDOWN = 168  # 7 days
    MONTHLY_COOLDOWN = 720  # 30 days
    YEARLY_COOLDOWN = 8760  # 365 days
    WORK_COOLDOWN = 1
    OVERTIME_COOLDOWN = 4
    SPIN_COOLDOWN = 2
    
    # Game settings
    BLACKJACK_EASY_ODDS = 1.5  # 3:2
    BLACKJACK_HARD_ODDS = 2.0  # 2:1
    COINFLIP_ODDS = 1.0  # 1:1
    
    # XP rewards
    GAME_WIN_XP = 100
    
    # Colors for embeds
    COLOR_SUCCESS = 0x00ff00
    COLOR_ERROR = 0xff0000
    COLOR_WARNING = 0xffff00
    COLOR_INFO = 0x0099ff
    COLOR_NEUTRAL = 0x36393f
