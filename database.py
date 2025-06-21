import aiosqlite
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        
    async def initialize(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Players table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    guild_id INTEGER,
                    cash INTEGER DEFAULT 1000,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    total_winnings INTEGER DEFAULT 0,
                    total_losses INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    daily_last_claimed TEXT,
                    weekly_last_claimed TEXT,
                    monthly_last_claimed TEXT,
                    yearly_last_claimed TEXT,
                    work_last_used TEXT,
                    overtime_last_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Game statistics table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS game_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    game_name TEXT,
                    bet_amount INTEGER,
                    winnings INTEGER,
                    result TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES players (user_id)
                )
            ''')
            
            # Player inventory table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    guild_id INTEGER,
                    item_id TEXT,
                    quantity INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id, item_id),
                    FOREIGN KEY (user_id) REFERENCES players (user_id)
                )
            ''')
            
            # Mining system table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS mining (
                    user_id INTEGER PRIMARY KEY,
                    guild_id INTEGER,
                    mine_name TEXT,
                    coal INTEGER DEFAULT 0,
                    iron INTEGER DEFAULT 0,
                    gold INTEGER DEFAULT 0,
                    diamond INTEGER DEFAULT 0,
                    emerald INTEGER DEFAULT 0,
                    lapis INTEGER DEFAULT 0,
                    redstone INTEGER DEFAULT 0,
                    unprocessed_materials INTEGER DEFAULT 0,
                    prestige_level INTEGER DEFAULT 0,
                    last_dig TEXT,
                    FOREIGN KEY (user_id) REFERENCES players (user_id)
                )
            ''')
            
            # Guild configuration table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    allowed_channels TEXT,
                    cash_name TEXT DEFAULT 'coins',
                    cash_emoji TEXT DEFAULT '🪙',
                    crypto_name TEXT DEFAULT 'crypto',
                    crypto_emoji TEXT DEFAULT '💎',
                    force_commands BOOLEAN DEFAULT FALSE,
                    disable_update_messages BOOLEAN DEFAULT FALSE,
                    admin_ids TEXT DEFAULT '[]'
                )
            ''')
            
            # Cooldowns table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id INTEGER,
                    guild_id INTEGER,
                    command_name TEXT,
                    expires_at TEXT,
                    PRIMARY KEY (user_id, guild_id, command_name)
                )
            ''')
            
            await db.commit()
    
    async def ensure_player_exists(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Ensure player exists in database and return player data."""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if player exists
            cursor = await db.execute(
                "SELECT * FROM players WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            player = await cursor.fetchone()
            
            if not player:
                # Create new player
                await db.execute('''
                    INSERT INTO players (user_id, guild_id, cash, level, xp)
                    VALUES (?, ?, 1000, 1, 0)
                ''', (user_id, guild_id))
                await db.commit()
                
                # Fetch the newly created player
                cursor = await db.execute(
                    "SELECT * FROM players WHERE user_id = ? AND guild_id = ?",
                    (user_id, guild_id)
                )
                player = await cursor.fetchone()
            
            # Convert to dict
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, player))
    
    async def get_player(self, user_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get player data."""
        return await self.ensure_player_exists(user_id, guild_id)
    
    async def update_player_cash(self, user_id: int, guild_id: int, amount: int):
        """Update player cash amount."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE players SET cash = cash + ? WHERE user_id = ? AND guild_id = ?",
                (amount, user_id, guild_id)
            )
            await db.commit()
    
    async def set_player_cash(self, user_id: int, guild_id: int, amount: int):
        """Set player cash to specific amount."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE players SET cash = ? WHERE user_id = ? AND guild_id = ?",
                (amount, user_id, guild_id)
            )
            await db.commit()
    
    async def add_game_stat(self, user_id: int, guild_id: int, game_name: str, 
                           bet_amount: int, winnings: int, result: str):
        """Add game statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO game_stats (user_id, guild_id, game_name, bet_amount, winnings, result)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, guild_id, game_name, bet_amount, winnings, result))
            
            # Update player totals
            if winnings > 0:
                await db.execute(
                    "UPDATE players SET total_winnings = total_winnings + ?, games_played = games_played + 1 WHERE user_id = ? AND guild_id = ?",
                    (winnings, user_id, guild_id)
                )
            else:
                await db.execute(
                    "UPDATE players SET total_losses = total_losses + ?, games_played = games_played + 1 WHERE user_id = ? AND guild_id = ?",
                    (bet_amount, user_id, guild_id)
                )
            
            await db.commit()
    
    async def check_cooldown(self, user_id: int, guild_id: int, command_name: str) -> Optional[datetime]:
        """Check if command is on cooldown."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT expires_at FROM cooldowns WHERE user_id = ? AND guild_id = ? AND command_name = ?",
                (user_id, guild_id, command_name)
            )
            result = await cursor.fetchone()
            
            if result:
                expires_at = datetime.fromisoformat(result[0])
                if expires_at > datetime.now():
                    return expires_at
                else:
                    # Cooldown expired, remove it
                    await db.execute(
                        "DELETE FROM cooldowns WHERE user_id = ? AND guild_id = ? AND command_name = ?",
                        (user_id, guild_id, command_name)
                    )
                    await db.commit()
            
            return None
    
    async def set_cooldown(self, user_id: int, guild_id: int, command_name: str, duration_hours: float):
        """Set cooldown for a command."""
        expires_at = datetime.now() + timedelta(hours=duration_hours)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO cooldowns (user_id, guild_id, command_name, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, guild_id, command_name, expires_at.isoformat()))
            await db.commit()
    
    async def ensure_guild_exists(self, guild_id: int):
        """Ensure guild exists in configuration."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT guild_id FROM guild_config WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if not result:
                await db.execute(
                    "INSERT INTO guild_config (guild_id) VALUES (?)",
                    (guild_id,)
                )
                await db.commit()
    
    async def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        """Get guild configuration."""
        await self.ensure_guild_exists(guild_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM guild_config WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                config = dict(zip(columns, result))
                # Parse JSON fields
                config['admin_ids'] = json.loads(config['admin_ids']) if config['admin_ids'] else []
                config['allowed_channels'] = json.loads(config['allowed_channels']) if config['allowed_channels'] else []
                return config
            
            return {}
    
    async def get_leaderboard(self, guild_id: int, stat: str, limit: int = 10) -> List[Dict]:
        """Get leaderboard for a specific stat."""
        async with aiosqlite.connect(self.db_path) as db:
            if stat == 'cash':
                cursor = await db.execute(
                    "SELECT user_id, cash FROM players WHERE guild_id = ? ORDER BY cash DESC LIMIT ?",
                    (guild_id, limit)
                )
            elif stat == 'winnings':
                cursor = await db.execute(
                    "SELECT user_id, total_winnings FROM players WHERE guild_id = ? ORDER BY total_winnings DESC LIMIT ?",
                    (guild_id, limit)
                )
            elif stat == 'games':
                cursor = await db.execute(
                    "SELECT user_id, games_played FROM players WHERE guild_id = ? ORDER BY games_played DESC LIMIT ?",
                    (guild_id, limit)
                )
            else:
                return []
            
            results = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in results]
