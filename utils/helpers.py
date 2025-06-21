import re
from datetime import datetime, timedelta
from typing import Optional, Union

def format_currency(amount: int, currency_name: str = "Cash", currency_emoji: str = "💰") -> str:
    """Format currency amount with proper formatting."""
    return f"{currency_emoji} {amount:,} {currency_name}"

def parse_bet_amount(bet_str: str, player_cash: int, max_bet_percentage: float = 0.5) -> Optional[int]:
    """Parse bet amount from string input."""
    bet_str = bet_str.lower().strip()
    
    if bet_str in ['all', 'max']:
        return int(player_cash * max_bet_percentage)
    elif bet_str in ['half', '50%']:
        return int(player_cash * 0.5)
    elif bet_str in ['quarter', '25%']:
        return int(player_cash * 0.25)
    elif bet_str.endswith('%'):
        try:
            percentage = float(bet_str[:-1]) / 100
            if 0 <= percentage <= max_bet_percentage:
                return int(player_cash * percentage)
        except ValueError:
            return None
    elif bet_str.endswith('k'):
        try:
            return int(float(bet_str[:-1]) * 1000)
        except ValueError:
            return None
    elif bet_str.endswith('m'):
        try:
            return int(float(bet_str[:-1]) * 1000000)
        except ValueError:
            return None
    else:
        try:
            return int(bet_str.replace(',', ''))
        except ValueError:
            return None
    
    return None

def format_time_remaining(target_time: datetime) -> str:
    """Format time remaining until target datetime."""
    now = datetime.now()
    if target_time <= now:
        return "Now"
    
    diff = target_time - now
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def format_cooldown_time(hours: float) -> str:
    """Format cooldown time in human readable format."""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif hours < 24:
        return f"{int(hours)} hour{'s' if int(hours) != 1 else ''}"
    else:
        days = int(hours / 24)
        remaining_hours = int(hours % 24)
        if remaining_hours == 0:
            return f"{days} day{'s' if days != 1 else ''}"
        else:
            return f"{days} day{'s' if days != 1 else ''} {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"

def get_xp_for_level(level: int) -> int:
    """Calculate XP required for a specific level."""
    return (level - 1) * 1000

def get_level_from_xp(xp: int) -> int:
    """Calculate level from XP amount."""
    return max(1, (xp // 1000) + 1)

def validate_emoji(emoji_str: str) -> bool:
    """Validate if string is a valid emoji."""
    # Basic emoji validation - checks for Unicode emoji or Discord custom emoji format
    if re.match(r'^<:[a-zA-Z0-9_]+:[0-9]+>$', emoji_str):  # Custom emoji
        return True
    elif re.match(r'^[\U0001F000-\U0001F9FF\U00002600-\U000027BF\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF]+$', emoji_str):  # Unicode emoji
        return True
    return False

def validate_prediction(prediction: str, valid_options: list) -> bool:
    """Validate if prediction is in valid options."""
    return prediction.lower() in [option.lower() for option in valid_options]

def get_roulette_numbers() -> dict:
    """Get roulette numbers mapping."""
    return {
        'red': [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
        'black': [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35],
        'green': [0]
    }