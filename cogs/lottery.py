import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from utils.embeds import EmbedBuilder
from utils.helpers import format_currency, parse_bet_amount, format_time_remaining

class LotteryCog(commands.Cog):
    """Lottery and weekly events system."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Lottery configuration
        self.ticket_price = 1000
        self.max_tickets_per_player = 1000
        self.draw_day = 5  # Saturday (0=Monday, 6=Sunday)
        self.draw_hour = 11  # 11:00 AM UTC
        
        # Start the lottery draw task
        self.lottery_draw_task.start()
        
        # Weekly events configuration
        self.weekly_events = {
            'double_xp': {
                'name': 'Double XP Weekend',
                'description': 'Earn double XP from all games!',
                'emoji': '⚡',
                'frequency': 2  # Every 2 weeks
            },
            'bonus_daily': {
                'name': 'Bonus Daily Rewards',
                'description': 'Daily rewards are doubled!',
                'emoji': '💰',
                'frequency': 3  # Every 3 weeks
            },
            'lucky_games': {
                'name': 'Lucky Games',
                'description': 'All game payouts increased by 25%!',
                'emoji': '🍀',
                'frequency': 4  # Every 4 weeks
            },
            'mega_mining': {
                'name': 'Mega Mining',
                'description': 'Mining yields are tripled!',
                'emoji': '⛏️',
                'frequency': 3  # Every 3 weeks
            }
        }
    
    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.lottery_draw_task.cancel()
    
    async def _ensure_lottery_table(self):
        """Ensure lottery table exists."""
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS lottery (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    tickets INTEGER DEFAULT 0,
                    week_start TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS lottery_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    week_start TEXT,
                    winner_id INTEGER,
                    winner_tickets INTEGER,
                    total_tickets INTEGER,
                    prize_amount INTEGER,
                    draw_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS weekly_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    event_type TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    def _get_week_start(self) -> str:
        """Get the start of the current lottery week (Monday)."""
        now = datetime.now()
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    def _get_next_draw_time(self) -> datetime:
        """Get the next lottery draw time."""
        now = datetime.now()
        
        # Find next Saturday at 11:00 AM
        days_until_saturday = (self.draw_day - now.weekday()) % 7
        if days_until_saturday == 0 and now.hour >= self.draw_hour:
            days_until_saturday = 7  # Next Saturday if it's already past draw time today
        
        next_draw = now + timedelta(days=days_until_saturday)
        next_draw = next_draw.replace(hour=self.draw_hour, minute=0, second=0, microsecond=0)
        
        return next_draw
    
    @tasks.loop(hours=1)
    async def lottery_draw_task(self):
        """Task that runs every hour to check for lottery draws."""
        try:
            now = datetime.now()
            
            # Check if it's Saturday at 11:00 AM
            if now.weekday() == self.draw_day and now.hour == self.draw_hour:
                await self._conduct_lottery_draws()
                
        except Exception as e:
            print(f"Error in lottery draw task: {e}")
    
    @lottery_draw_task.before_loop
    async def before_lottery_task(self):
        """Wait until bot is ready before starting the task."""
        await self.bot.wait_until_ready()
        await self._ensure_lottery_table()
    
    async def _conduct_lottery_draws(self):
        """Conduct lottery draws for all guilds."""
        await self._ensure_lottery_table()
        
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            # Get all guilds with lottery participants
            cursor = await db.execute('''
                SELECT DISTINCT guild_id FROM lottery 
                WHERE week_start = ?
            ''', (self._get_week_start(),))
            
            guild_ids = [row[0] for row in await cursor.fetchall()]
            
            for guild_id in guild_ids:
                await self._draw_lottery_for_guild(guild_id, db)
    
    async def _draw_lottery_for_guild(self, guild_id: int, db):
        """Conduct lottery draw for a specific guild."""
        week_start = self._get_week_start()
        
        # Get all participants and their tickets
        cursor = await db.execute('''
            SELECT user_id, tickets FROM lottery 
            WHERE guild_id = ? AND week_start = ?
        ''', (guild_id, week_start))
        
        participants = await cursor.fetchall()
        
        if not participants:
            return
        
        # Create weighted list of all tickets
        ticket_pool = []
        total_tickets = 0
        
        for user_id, tickets in participants:
            for _ in range(tickets):
                ticket_pool.append(user_id)
            total_tickets += tickets
        
        if not ticket_pool:
            return
        
        # Draw winner
        winner_id = random.choice(ticket_pool)
        
        # Get winner's ticket count
        winner_tickets = next(tickets for uid, tickets in participants if uid == winner_id)
        
        # Calculate prize (70% of total ticket sales)
        prize_amount = int(total_tickets * self.ticket_price * 0.7)
        
        # Award prize to winner
        await self.bot.db.update_player_cash(winner_id, guild_id, prize_amount)
        
        # Record draw in history
        await db.execute('''
            INSERT INTO lottery_history 
            (guild_id, week_start, winner_id, winner_tickets, total_tickets, prize_amount, draw_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (guild_id, week_start, winner_id, winner_tickets, total_tickets, prize_amount, datetime.now().isoformat()))
        
        # Clear current week's tickets
        await db.execute('''
            DELETE FROM lottery WHERE guild_id = ? AND week_start = ?
        ''', (guild_id, week_start))
        
        await db.commit()
        
        # Announce winner in guild
        guild = self.bot.get_guild(guild_id)
        if guild:
            await self._announce_lottery_winner(guild, winner_id, winner_tickets, total_tickets, prize_amount)
    
    async def _announce_lottery_winner(self, guild: discord.Guild, winner_id: int, 
                                     winner_tickets: int, total_tickets: int, prize_amount: int):
        """Announce lottery winner in the guild."""
        winner = guild.get_member(winner_id)
        winner_name = winner.mention if winner else f"<@{winner_id}>"
        
        embed = EmbedBuilder.success(
            "🎰 Lottery Draw Results!",
            f"**Winner:** {winner_name}\n"
            f"**Winning Tickets:** {winner_tickets:,}\n"
            f"**Total Tickets:** {total_tickets:,}\n"
            f"**Prize:** {format_currency(prize_amount)}\n\n"
            f"**Win Chance:** {(winner_tickets/total_tickets)*100:.2f}%"
        )
        
        embed.add_field(
            name="🎫 Next Lottery",
            value=f"The next lottery draw will be {format_time_remaining(self._get_next_draw_time())}",
            inline=False
        )
        
        # Try to send to a general channel
        for channel_name in ['general', 'lottery', 'gambling', 'announcements']:
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if channel:
                try:
                    await channel.send(embed=embed)
                    break
                except discord.Forbidden:
                    continue
    
    @app_commands.command(name="lottery", description="Participate in the weekly lottery")
    @app_commands.describe(tickets="Number of tickets to buy (max 1000 per week)")
    async def lottery(self, interaction: discord.Interaction, tickets: str = None):
        """Participate in the weekly lottery."""
        try:
            await interaction.response.defer()
            await self._ensure_lottery_table()
            
            if not tickets:
                # Show lottery info
                embed = await self._get_lottery_info_embed(interaction.guild.id)
                await interaction.followup.send(embed=embed)
                return
            
            # Parse ticket amount
            if tickets.lower() in ['m', 'max']:
                tickets_to_buy = self.max_tickets_per_player
            else:
                try:
                    tickets_to_buy = int(tickets)
                except ValueError:
                    await interaction.followup.send(
                        embed=EmbedBuilder.error("Invalid Amount", "Please enter a valid number of tickets!")
                    )
                    return
            
            if tickets_to_buy <= 0:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Amount", "Number of tickets must be positive!")
                )
                return
            
            # Get player cash
            player = await self.bot.db.get_player(interaction.user.id, interaction.guild.id)
            player_cash = player['cash']
            
            # Check current tickets for this week
            week_start = self._get_week_start()
            
            async with aiosqlite.connect(self.bot.db.db_path) as db:
                cursor = await db.execute('''
                    SELECT tickets FROM lottery 
                    WHERE user_id = ? AND guild_id = ? AND week_start = ?
                ''', (interaction.user.id, interaction.guild.id, week_start))
                
                result = await cursor.fetchone()
                current_tickets = result[0] if result else 0
                
                # Check if adding tickets would exceed maximum
                if current_tickets + tickets_to_buy > self.max_tickets_per_player:
                    max_can_buy = self.max_tickets_per_player - current_tickets
                    await interaction.followup.send(
                        embed=EmbedBuilder.error(
                            "Too Many Tickets",
                            f"You can only buy {max_can_buy} more tickets this week! (Current: {current_tickets:,}/1,000)"
                        )
                    )
                    return
                
                # Check if player has enough money
                total_cost = tickets_to_buy * self.ticket_price
                if total_cost > player_cash:
                    await interaction.followup.send(
                        embed=EmbedBuilder.error(
                            "Insufficient Funds",
                            f"You need {format_currency(total_cost)} but only have {format_currency(player_cash)}!"
                        )
                    )
                    return
                
                # Process purchase
                await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, -total_cost)
                
                # Update or insert lottery entry
                if current_tickets > 0:
                    await db.execute('''
                        UPDATE lottery SET tickets = tickets + ? 
                        WHERE user_id = ? AND guild_id = ? AND week_start = ?
                    ''', (tickets_to_buy, interaction.user.id, interaction.guild.id, week_start))
                else:
                    await db.execute('''
                        INSERT INTO lottery (guild_id, user_id, tickets, week_start)
                        VALUES (?, ?, ?, ?)
                    ''', (interaction.guild.id, interaction.user.id, tickets_to_buy, week_start))
                
                await db.commit()
                
                # Get updated ticket count
                new_total = current_tickets + tickets_to_buy
                
                embed = EmbedBuilder.success(
                    "🎫 Lottery Tickets Purchased!",
                    f"You bought {tickets_to_buy:,} tickets for {format_currency(total_cost)}!\n\n"
                    f"**Your total tickets this week:** {new_total:,}\n"
                    f"**Remaining tickets you can buy:** {self.max_tickets_per_player - new_total:,}"
                )
                
                embed.add_field(
                    name="🏆 Next Draw",
                    value=f"{format_time_remaining(self._get_next_draw_time())}",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Current Prize Pool",
                    value=await self._get_current_prize_pool(interaction.guild.id),
                    inline=True
                )
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to process lottery: {str(e)}")
            )
    
    async def _get_lottery_info_embed(self, guild_id: int) -> discord.Embed:
        """Get lottery information embed."""
        embed = discord.Embed(
            title="🎰 Weekly Lottery",
            description="Buy tickets for a chance to win the weekly prize pool!",
            color=0xffd700
        )
        
        # Basic info
        embed.add_field(
            name="🎫 Ticket Info",
            value=f"**Price:** {format_currency(self.ticket_price)} per ticket\n"
                  f"**Max per week:** {self.max_tickets_per_player:,} tickets\n"
                  f"**Draw time:** Saturdays at 11:00 AM UTC",
            inline=False
        )
        
        # Current week info
        week_start = self._get_week_start()
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) as participants, SUM(tickets) as total_tickets
                FROM lottery WHERE guild_id = ? AND week_start = ?
            ''', (guild_id, week_start))
            
            result = await cursor.fetchone()
            participants = result[0] if result else 0
            total_tickets = result[1] if result and result[1] else 0
        
        prize_pool = int(total_tickets * self.ticket_price * 0.7)
        
        embed.add_field(
            name="📊 Current Week",
            value=f"**Participants:** {participants:,}\n"
                  f"**Total Tickets:** {total_tickets:,}\n"
                  f"**Prize Pool:** {format_currency(prize_pool)}",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Next Draw",
            value=format_time_remaining(self._get_next_draw_time()),
            inline=True
        )
        
        embed.add_field(
            name="🎮 How to Play",
            value="• Use `/lottery <amount>` to buy tickets\n"
                  "• Each ticket costs 1,000 coins\n"
                  "• More tickets = higher win chance\n"
                  "• Winner gets 70% of total sales\n"
                  "• Draw every Saturday at 11:00 AM UTC",
            inline=False
        )
        
        return embed
    
    async def _get_current_prize_pool(self, guild_id: int) -> str:
        """Get current prize pool amount."""
        week_start = self._get_week_start()
        async with aiosqlite.connect(self.bot.db.db_path) as db:
            cursor = await db.execute('''
                SELECT SUM(tickets) FROM lottery 
                WHERE guild_id = ? AND week_start = ?
            ''', (guild_id, week_start))
            
            result = await cursor.fetchone()
            total_tickets = result[0] if result and result[0] else 0
            
            prize_pool = int(total_tickets * self.ticket_price * 0.7)
            return format_currency(prize_pool)
    
    @app_commands.command(name="lottery_history", description="View lottery history")
    async def lottery_history(self, interaction: discord.Interaction):
        """View lottery history."""
        try:
            await interaction.response.defer()
            await self._ensure_lottery_table()
            
            async with aiosqlite.connect(self.bot.db.db_path) as db:
                cursor = await db.execute('''
                    SELECT winner_id, winner_tickets, total_tickets, prize_amount, draw_date
                    FROM lottery_history 
                    WHERE guild_id = ?
                    ORDER BY draw_date DESC
                    LIMIT 10
                ''', (interaction.guild.id,))
                
                history = await cursor.fetchall()
            
            if not history:
                embed = EmbedBuilder.info(
                    "Lottery History",
                    "No lottery draws have been conducted yet!"
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🏆 Lottery History",
                description="Recent lottery winners",
                color=0xffd700
            )
            
            for i, (winner_id, winner_tickets, total_tickets, prize_amount, draw_date) in enumerate(history, 1):
                winner = interaction.guild.get_member(winner_id)
                winner_name = winner.display_name if winner else f"User {winner_id}"
                
                draw_datetime = datetime.fromisoformat(draw_date)
                win_percentage = (winner_tickets / total_tickets) * 100
                
                embed.add_field(
                    name=f"#{i} - {draw_datetime.strftime('%Y-%m-%d')}",
                    value=f"**Winner:** {winner_name}\n"
                          f"**Prize:** {format_currency(prize_amount)}\n"
                          f"**Tickets:** {winner_tickets:,}/{total_tickets:,} ({win_percentage:.1f}%)",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to get lottery history: {str(e)}")
            )
    
    @app_commands.command(name="events", description="View current weekly events")
    async def events(self, interaction: discord.Interaction):
        """View current weekly events."""
        try:
            await interaction.response.defer()
            await self._ensure_lottery_table()
            
            # Get active events
            async with aiosqlite.connect(self.bot.db.db_path) as db:
                cursor = await db.execute('''
                    SELECT event_type, start_date, end_date FROM weekly_events
                    WHERE guild_id = ? AND active = TRUE AND end_date > ?
                    ORDER BY start_date DESC
                ''', (interaction.guild.id, datetime.now().isoformat()))
                
                active_events = await cursor.fetchall()
            
            embed = discord.Embed(
                title="🎉 Weekly Events",
                description="Special events and bonuses currently active",
                color=0x9966cc
            )
            
            if not active_events:
                embed.description = "No special events are currently active."
                embed.add_field(
                    name="📅 Upcoming Events",
                    value="Weekly events are automatically scheduled!\n"
                          "• Double XP Weekends\n"
                          "• Bonus Daily Rewards\n"
                          "• Lucky Games (25% bonus payouts)\n"
                          "• Mega Mining (3x yields)",
                    inline=False
                )
            else:
                for event_type, start_date, end_date in active_events:
                    if event_type in self.weekly_events:
                        event_info = self.weekly_events[event_type]
                        start_dt = datetime.fromisoformat(start_date)
                        end_dt = datetime.fromisoformat(end_date)
                        
                        embed.add_field(
                            name=f"{event_info['emoji']} {event_info['name']}",
                            value=f"{event_info['description']}\n"
                                  f"**Ends:** {format_time_remaining(end_dt)}",
                            inline=False
                        )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to get events: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(LotteryCog(bot))