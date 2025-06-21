import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from typing import Optional

from utils.embeds import EmbedBuilder
from utils.helpers import parse_bet_amount, format_currency, validate_prediction
from games.blackjack import BlackjackGame
from games.coinflip import CoinflipGame
from games.dice import DiceGame
from games.slots import SlotsGame
from games.roulette import RouletteGame
from games.crash import CrashGame
from games.findthelady import FindTheLadyGame
from games.rockpaperscissors import RockPaperScissorsGame
from games.sevens import SevensGame
from games.higherorlower import HigherOrLowerGame
from games.race import RaceGame

class GamesCog(commands.Cog):
    """All gambling games commands."""
    
    def __init__(self, bot):
        self.bot = bot
        # Store active games to prevent multiple games per user
        self.active_games = {}
    
    def _check_active_game(self, user_id: int) -> bool:
        """Check if user has an active game."""
        return user_id in self.active_games
    
    def _start_game(self, user_id: int, game_type: str):
        """Mark user as having an active game."""
        self.active_games[user_id] = game_type
    
    def _end_game(self, user_id: int):
        """Mark user's game as ended."""
        if user_id in self.active_games:
            del self.active_games[user_id]
    
    async def _validate_bet(self, interaction: discord.Interaction, bet_str: str) -> Optional[int]:
        """Validate and parse bet amount."""
        player = await self.bot.db.get_player(interaction.user.id, interaction.guild.id)
        player_cash = player['cash']
        
        bet_amount = parse_bet_amount(bet_str, player_cash)
        
        if not bet_amount:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Invalid Bet", "Please enter a valid bet amount!")
            )
            return None
        
        if bet_amount <= 0:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Invalid Bet", "Bet amount must be positive!")
            )
            return None
        
        if bet_amount > player_cash:
            await interaction.followup.send(
                embed=EmbedBuilder.error(
                    "Insufficient Funds", 
                    f"You only have {format_currency(player_cash)} but tried to bet {format_currency(bet_amount)}!"
                )
            )
            return None
        
        # Max bet is 50% of cash (configurable)
        max_bet = int(player_cash * 0.5)
        if bet_str not in ['a', 'all', 'allin'] and bet_amount > max_bet:
            await interaction.followup.send(
                embed=EmbedBuilder.error(
                    "Bet Too High", 
                    f"Maximum bet is {format_currency(max_bet)} (50% of your cash)!"
                )
            )
            return None
        
        return bet_amount
    
    async def _process_game_result(self, interaction: discord.Interaction, game_name: str, 
                                 bet_amount: int, payout: int, embed: discord.Embed):
        """Process game result and update database."""
        # Update player cash
        await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, payout)
        
        # Add game statistics
        await self.bot.db.add_game_stat(
            interaction.user.id, interaction.guild.id, game_name,
            bet_amount, max(0, payout), "win" if payout > 0 else "loss"
        )
        
        # Add XP for wins
        if payout > 0:
            # Simple XP system: 100 XP per win
            # TODO: Add XP to database and level system
            pass
        
        # End the game
        self._end_game(interaction.user.id)
        
        return embed
    
    @app_commands.command(name="blackjack", description="Play a game of Blackjack")
    @app_commands.describe(
        bet="The amount to bet",
        mode="Toggle hard mode (default: Easy Mode)"
    )
    async def blackjack(self, interaction: discord.Interaction, bet: str, mode: str = "easy"):
        """Play Blackjack."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            hard_mode = mode.lower() in ['hard', 'h']
            
            # Start game
            self._start_game(interaction.user.id, "blackjack")
            game = BlackjackGame(bet_amount, hard_mode)
            
            # Show initial game state
            embed = game.get_game_embed()
            message = await interaction.followup.send(embed=embed)
            
            # If game is over (blackjack), process result
            if game.game_over:
                await self._process_game_result(interaction, "blackjack", bet_amount, game.payout, embed)
                return
            
            # Add reactions for hit/stand
            await message.add_reaction('🎯')  # Hit
            await message.add_reaction('✋')   # Stand
            
            # Wait for user reaction
            def check(reaction, user):
                return (user.id == interaction.user.id and 
                       reaction.message.id == message.id and
                       str(reaction.emoji) in ['🎯', '✋'])
            
            while not game.game_over:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == '🎯':
                        # Hit
                        game.hit()
                    elif str(reaction.emoji) == '✋':
                        # Stand
                        game.stand()
                    
                    # Update embed
                    embed = game.get_game_embed()
                    await message.edit(embed=embed)
                    
                    # Remove user's reaction
                    try:
                        await message.remove_reaction(reaction.emoji, user)
                    except:
                        pass
                    
                except asyncio.TimeoutError:
                    # Auto-stand on timeout
                    game.stand()
                    embed = game.get_game_embed()
                    await message.edit(embed=embed)
                    break
            
            # Process final result
            await self._process_game_result(interaction, "blackjack", bet_amount, game.payout, embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="coinflip", description="Flip a coin!")
    @app_commands.describe(
        prediction="Choose heads or tails",
        bet="The amount to bet"
    )
    async def coinflip(self, interaction: discord.Interaction, prediction: str, bet: str):
        """Play Coinflip."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            if not validate_prediction("coinflip", prediction):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Prediction", "Choose 'heads' or 'tails'!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            # Play game
            self._start_game(interaction.user.id, "coinflip")
            game = CoinflipGame(prediction, bet_amount)
            
            embed = game.get_result_embed()
            await self._process_game_result(interaction, "coinflip", bet_amount, game.payout, embed)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="roll", description="Roll a dice and bet on the result!")
    @app_commands.describe(
        dice_type="The type of dice to roll (d4, d6, d8, d10, d12, d20)",
        prediction="What number will the dice land on?",
        bet="The amount to bet"
    )
    async def roll(self, interaction: discord.Interaction, dice_type: str, prediction: int, bet: str):
        """Play Dice Roll."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            valid_dice = ['d4', 'd6', 'd8', 'd10', 'd12', 'd20']
            if dice_type.lower() not in valid_dice:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Dice", f"Choose from: {', '.join(valid_dice)}")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            # Play game
            self._start_game(interaction.user.id, "roll")
            game = DiceGame(dice_type, prediction, bet_amount)
            
            if not game.dice_max:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "Invalid dice type!")
                )
                self._end_game(interaction.user.id)
                return
            
            embed = game.get_result_embed()
            await self._process_game_result(interaction, "roll", bet_amount, game.payout, embed)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="slots", description="Try your luck in the slots!")
    @app_commands.describe(bet="The amount to bet")
    async def slots(self, interaction: discord.Interaction, bet: str):
        """Play Slots."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            # Play game
            self._start_game(interaction.user.id, "slots")
            game = SlotsGame(bet_amount)
            
            embed = game.get_result_embed()
            await self._process_game_result(interaction, "slots", bet_amount, game.payout, embed)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="roulette", description="Play a game of roulette!")
    @app_commands.describe(
        prediction="What roulette bet you'd like to place",
        bet="The amount to bet"
    )
    async def roulette(self, interaction: discord.Interaction, prediction: str, bet: str):
        """Play Roulette."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            # Play game
            self._start_game(interaction.user.id, "roulette")
            game = RouletteGame(prediction, bet_amount)
            
            embed = game.get_result_embed()
            await self._process_game_result(interaction, "roulette", bet_amount, game.payout, embed)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="crash", description="Cash out before the multiplier crashes!")
    @app_commands.describe(
        bet="The amount to bet",
        mode="Toggle hard mode (default: Easy Mode)"
    )
    async def crash(self, interaction: discord.Interaction, bet: str, mode: str = "easy"):
        """Play Crash."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            hard_mode = mode.lower() in ['hard', 'h']
            
            # Start game
            self._start_game(interaction.user.id, "crash")
            game = CrashGame(bet_amount, hard_mode)
            
            # Start the interactive game
            result = await game.start_game(interaction)
            
            await self._process_game_result(interaction, "crash", bet_amount, result['payout'], None)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="findthelady", description="Find the lady among the kings!")
    @app_commands.describe(
        bet="The amount to bet",
        mode="Toggle hard mode (default: Easy Mode)"
    )
    async def findthelady(self, interaction: discord.Interaction, bet: str, mode: str = "easy"):
        """Play Find the Lady."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            hard_mode = mode.lower() in ['hard', 'h']
            
            # Start game
            self._start_game(interaction.user.id, "findthelady")
            game = FindTheLadyGame(bet_amount, hard_mode)
            
            # Start the interactive game
            result = await game.start_game(interaction)
            
            await self._process_game_result(interaction, "findthelady", bet_amount, result['payout'], None)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="rockpaperscissors", description="Play rock paper scissors!")
    @app_commands.describe(
        selection="Your choice of Rock, Paper or Scissors",
        bet="The amount to bet"
    )
    async def rockpaperscissors(self, interaction: discord.Interaction, selection: str, bet: str):
        """Play Rock Paper Scissors."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            if not validate_prediction("rps", selection):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Selection", "Choose 'rock', 'paper', or 'scissors'!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            # Play game
            self._start_game(interaction.user.id, "rps")
            game = RockPaperScissorsGame(selection, bet_amount)
            
            embed = game.get_result_embed()
            await self._process_game_result(interaction, "rps", bet_amount, game.payout, embed)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="sevens", description="Play a game of sevens!")
    @app_commands.describe(
        prediction="What do you think it will land on? (7, low, high)",
        bet="The amount to bet"
    )
    async def sevens(self, interaction: discord.Interaction, prediction: str, bet: str):
        """Play Sevens."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            if not validate_prediction("sevens", prediction):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Prediction", "Choose '7', 'low' (1-6), or 'high' (8-13)!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            # Play game
            self._start_game(interaction.user.id, "sevens")
            game = SevensGame(prediction, bet_amount)
            
            embed = game.get_result_embed()
            await self._process_game_result(interaction, "sevens", bet_amount, game.payout, embed)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="higherorlower", description="Play higher or lower with cards!")
    async def higherorlower(self, interaction: discord.Interaction):
        """Play Higher or Lower."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            # Start game (no bet required, payout based on score)
            self._start_game(interaction.user.id, "higherorlower")
            game = HigherOrLowerGame()
            
            # Show initial game state
            embed = game.get_game_embed()
            message = await interaction.followup.send(embed=embed)
            
            # Add reactions
            await message.add_reaction('⬆️')  # Higher
            await message.add_reaction('⬇️')  # Lower
            await message.add_reaction('💰')  # Cash out
            
            # Game loop
            def check(reaction, user):
                return (user.id == interaction.user.id and 
                       reaction.message.id == message.id and
                       str(reaction.emoji) in ['⬆️', '⬇️', '💰'])
            
            while not game.game_over:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == '⬆️':
                        result = game.make_guess('higher')
                    elif str(reaction.emoji) == '⬇️':
                        result = game.make_guess('lower')
                    elif str(reaction.emoji) == '💰':
                        # Cash out
                        result = game.cash_out()
                        break
                    
                    if not result['success']:
                        await interaction.followup.send(
                            embed=EmbedBuilder.error("Error", result['message'])
                        )
                        continue
                    
                    # Update embed
                    embed = game.get_game_embed()
                    await message.edit(embed=embed)
                    
                    # Remove user's reaction
                    try:
                        await message.remove_reaction(reaction.emoji, user)
                    except:
                        pass
                    
                    if not result['continue']:
                        break
                    
                except asyncio.TimeoutError:
                    # Auto cash out on timeout
                    game.cash_out()
                    embed = game.get_game_embed()
                    await message.edit(embed=embed)
                    break
            
            # Process final result
            final_result = game.cash_out() if not game.game_over else {'payout': 100 * game.score, 'xp': 10 * game.score}
            
            # Update player cash
            if final_result['payout'] > 0:
                await self.bot.db.update_player_cash(
                    interaction.user.id, interaction.guild.id, final_result['payout']
                )
            
            # Add game stat
            await self.bot.db.add_game_stat(
                interaction.user.id, interaction.guild.id, "higherorlower",
                0, final_result['payout'], f"score_{game.score}"
            )
            
            self._end_game(interaction.user.id)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="race", description="Race animals and bet on the winner!")
    @app_commands.describe(
        racer_type="The type of racer (turtle/t, dog/d, horse/h, dinosaur/di)",
        prediction="Which racer you think will win",
        bet="The amount to bet"
    )
    async def race(self, interaction: discord.Interaction, racer_type: str, prediction: int, bet: str):
        """Play Race."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            # Start game
            self._start_game(interaction.user.id, "race")
            game = RaceGame(racer_type, prediction, bet_amount)
            
            if not game.config:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Racer", "Choose from: turtle/t, dog/d, horse/h, dinosaur/di")
                )
                self._end_game(interaction.user.id)
                return
            
            # Start the race
            result = await game.start_race(interaction)
            
            if result['success']:
                await self._process_game_result(interaction, "race", bet_amount, result['payout'], None)
            else:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", result['message'])
                )
                self._end_game(interaction.user.id)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )
    
    @app_commands.command(name="gamble", description="Play a random game!")
    @app_commands.describe(
        bet="The amount to bet",
        mode="Toggle hard mode for applicable games"
    )
    async def gamble(self, interaction: discord.Interaction, bet: str, mode: str = "easy"):
        """Play a random game."""
        try:
            await interaction.response.defer()
            
            if self._check_active_game(interaction.user.id):
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Active Game", "You already have a game in progress!")
                )
                return
            
            # Pick a random game
            simple_games = ['coinflip', 'slots', 'rps', 'sevens']
            chosen_game = random.choice(simple_games)
            
            bet_amount = await self._validate_bet(interaction, bet)
            if not bet_amount:
                return
            
            self._start_game(interaction.user.id, "gamble")
            
            embed = EmbedBuilder.info("🎰 Random Gamble", f"Playing random game: **{chosen_game.title()}**!")
            await interaction.followup.send(embed=embed)
            
            # Wait a moment for suspense
            await asyncio.sleep(2)
            
            # Play the chosen game with random parameters
            if chosen_game == 'coinflip':
                prediction = random.choice(['heads', 'tails'])
                game = CoinflipGame(prediction, bet_amount)
                embed = game.get_result_embed()
                payout = game.payout
            
            elif chosen_game == 'slots':
                game = SlotsGame(bet_amount)
                embed = game.get_result_embed()
                payout = game.payout
            
            elif chosen_game == 'rps':
                selection = random.choice(['rock', 'paper', 'scissors'])
                game = RockPaperScissorsGame(selection, bet_amount)
                embed = game.get_result_embed()
                payout = game.payout
            
            elif chosen_game == 'sevens':
                prediction = random.choice(['7', 'low', 'high'])
                game = SevensGame(prediction, bet_amount)
                embed = game.get_result_embed()
                payout = game.payout
            
            # Add random gamble indicator
            embed.title = f"🎰 Random Gamble - {embed.title}"
            
            await self._process_game_result(interaction, "gamble", bet_amount, payout, embed)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self._end_game(interaction.user.id)
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Game error: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(GamesCog(bot))
