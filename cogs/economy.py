import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import EmbedBuilder
from utils.helpers import format_currency, parse_bet_amount

class EconomyCog(commands.Cog):
    """Economy-related commands like shop, inventory, etc."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Sample items for the shop
        self.items = {
            'lucky_charm': {
                'name': 'Lucky Charm',
                'price': 10000,
                'description': 'Increases your luck in games by 5%',
                'emoji': '🍀'
            },
            'multiplier_boost': {
                'name': 'Multiplier Boost',
                'price': 25000,
                'description': 'Doubles your winnings for 1 hour',
                'emoji': '⚡'
            },
            'insurance': {
                'name': 'Bet Insurance',
                'price': 15000,
                'description': 'Protects you from losing more than 50% of a bet',
                'emoji': '🛡️'
            },
            'vip_pass': {
                'name': 'VIP Pass',
                'price': 100000,
                'description': 'Access to exclusive VIP games',
                'emoji': '👑'
            }
        }
    
    @app_commands.command(name="shop", description="Browse the shop")
    @app_commands.describe(
        shop_type="Type of shop to browse",
        page="Page number"
    )
    async def shop(self, interaction: discord.Interaction, shop_type: str = "items", page: int = 1):
        """Show the shop."""
        try:
            await interaction.response.defer()
            
            if shop_type.lower() == "items":
                embed = self._create_shop_embed(page)
            else:
                embed = EmbedBuilder.error("Error", f"Shop type '{shop_type}' not found!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to show shop: {str(e)}")
            )
    
    def _create_shop_embed(self, page: int = 1) -> discord.Embed:
        """Create shop embed."""
        embed = discord.Embed(
            title="🛒 Item Shop",
            description="Buy items to enhance your gambling experience!",
            color=0x0099ff
        )
        
        items_per_page = 4
        start_idx = (page - 1) * items_per_page
        items_list = list(self.items.items())
        page_items = items_list[start_idx:start_idx + items_per_page]
        
        if not page_items:
            embed.description = "No items found on this page!"
            return embed
        
        for item_id, item_data in page_items:
            embed.add_field(
                name=f"{item_data['emoji']} {item_data['name']}",
                value=f"{item_data['description']}\n**Price:** {format_currency(item_data['price'])}\n"
                      f"**ID:** `{item_id}`",
                inline=False
            )
        
        total_pages = (len(items_list) + items_per_page - 1) // items_per_page
        embed.set_footer(text=f"Page {page}/{total_pages} • Use /buy item <item_id> <amount> to purchase")
        
        return embed
    
    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(
        item_id="The ID of the item to buy",
        amount="Amount to buy"
    )
    async def buy_item(self, interaction: discord.Interaction, item_id: str, amount: str = "1"):
        """Buy an item."""
        try:
            await interaction.response.defer()
            
            if item_id not in self.items:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", f"Item '{item_id}' not found!")
                )
                return
            
            # Parse amount
            try:
                buy_amount = int(amount) if amount != 'a' else 1
                if buy_amount <= 0:
                    raise ValueError()
            except ValueError:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "Invalid amount!")
                )
                return
            
            item = self.items[item_id]
            total_cost = item['price'] * buy_amount
            
            # Check if player has enough money
            player = await self.bot.db.get_player(interaction.user.id, interaction.guild.id)
            if player['cash'] < total_cost:
                await interaction.followup.send(
                    embed=EmbedBuilder.error(
                        "Insufficient Funds",
                        f"You need {format_currency(total_cost)} but only have {format_currency(player['cash'])}!"
                    )
                )
                return
            
            # Process purchase
            await self.bot.db.update_player_cash(interaction.user.id, interaction.guild.id, -total_cost)
            
            # Add to inventory (simplified - just update cash for now)
            embed = EmbedBuilder.success(
                "Purchase Successful!",
                f"You bought {buy_amount}x {item['emoji']} **{item['name']}** for {format_currency(total_cost)}!"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to buy item: {str(e)}")
            )
    
    @app_commands.command(name="inventory", description="Show your inventory")
    async def inventory(self, interaction: discord.Interaction):
        """Show player inventory."""
        try:
            await interaction.response.defer()
            
            # For now, just show a placeholder
            embed = EmbedBuilder.info(
                "📦 Your Inventory",
                "Your inventory is empty!\n\nUse `/shop` to browse items and `/buy` to purchase them."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to show inventory: {str(e)}")
            )
    
    @app_commands.command(name="leaderboard", description="Show server leaderboards")
    @app_commands.describe(
        category="Category to show leaderboard for",
        global_board="Show global leaderboard instead of server"
    )
    async def leaderboard(self, interaction: discord.Interaction, category: str = "cash", global_board: bool = False):
        """Show leaderboards."""
        try:
            await interaction.response.defer()
            
            valid_categories = ["cash", "winnings", "games"]
            if category not in valid_categories:
                await interaction.followup.send(
                    embed=EmbedBuilder.error(
                        "Error", 
                        f"Invalid category! Choose from: {', '.join(valid_categories)}"
                    )
                )
                return
            
            # Map category to database field
            stat_map = {
                "cash": "cash",
                "winnings": "total_winnings", 
                "games": "games_played"
            }
            
            stat_name = stat_map[category]
            guild_id = None if global_board else interaction.guild.id
            
            entries = await self.bot.db.get_leaderboard(guild_id or interaction.guild.id, stat_name)
            
            title = f"{'Global' if global_board else interaction.guild.name} {category.title()} Leaderboard"
            embed = EmbedBuilder.leaderboard(title, entries, interaction.guild, stat_name)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to show leaderboard: {str(e)}")
            )
    
    @app_commands.command(name="gift", description="Send a free gift to someone")
    @app_commands.describe(recipient="The user to receive the gift")
    async def gift(self, interaction: discord.Interaction, recipient: discord.Member = None):
        """Send a free gift."""
        try:
            await interaction.response.defer()
            
            # Check cooldown (12 hours)
            cooldown = await self.bot.db.check_cooldown(
                interaction.user.id, interaction.guild.id, "gift"
            )
            
            if cooldown:
                from utils.helpers import format_time_remaining
                time_left = format_time_remaining(cooldown)
                embed = EmbedBuilder.warning(
                    "Gift Cooldown",
                    f"You can send another gift in {time_left}"
                )
                await interaction.followup.send(embed=embed)
                return
            
            if not recipient:
                # Show gift info
                embed = EmbedBuilder.info(
                    "🎁 Free Gifts",
                    "Send up to 5 free gifts every 12 hours!\n\n"
                    "Gifts don't cost you anything and brighten someone's day!\n"
                    "Use `/gift @user` to send a gift."
                )
                await interaction.followup.send(embed=embed)
                return
            
            if recipient.bot:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "You cannot gift to bots!")
                )
                return
            
            if recipient.id == interaction.user.id:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Error", "You cannot gift to yourself!")
                )
                return
            
            # Generate random gift amount
            import random
            gift_amount = random.randint(500, 2000)
            
            # Give gift to recipient
            await self.bot.db.update_player_cash(recipient.id, interaction.guild.id, gift_amount)
            
            # Set cooldown
            await self.bot.db.set_cooldown(
                interaction.user.id, interaction.guild.id, "gift", 12
            )
            
            embed = EmbedBuilder.success(
                "🎁 Gift Sent!",
                f"You sent a gift of {format_currency(gift_amount)} to {recipient.mention}!\n\n"
                "Your kindness doesn't go unnoticed! 💝"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to send gift: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
