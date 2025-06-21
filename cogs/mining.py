import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from utils.embeds import EmbedBuilder
from utils.helpers import format_currency, format_time_remaining

class MiningCog(commands.Cog):
    """Mining system commands."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Mining items and their properties
        self.mining_items = {
            'coal': {'emoji': '⚫', 'name': 'Coal', 'rarity': 0.4},
            'iron': {'emoji': '🔩', 'name': 'Iron Ore', 'rarity': 0.3},
            'gold': {'emoji': '🟡', 'name': 'Gold Ore', 'rarity': 0.15},
            'diamond': {'emoji': '💎', 'name': 'Diamond', 'rarity': 0.05},
            'emerald': {'emoji': '💚', 'name': 'Emerald', 'rarity': 0.03},
            'lapis': {'emoji': '🔵', 'name': 'Lapis Lazuli', 'rarity': 0.04},
            'redstone': {'emoji': '🔴', 'name': 'Redstone', 'rarity': 0.08}
        }
        
        # Mining units for purchase
        self.mining_units = {
            'pickaxe_stone': {
                'name': 'Stone Pickaxe',
                'price': 1000,
                'efficiency': 1.2,
                'emoji': '⛏️'
            },
            'pickaxe_iron': {
                'name': 'Iron Pickaxe',
                'price': 5000,
                'efficiency': 1.5,
                'emoji': '⛏️'
            },
            'pickaxe_diamond': {
                'name': 'Diamond Pickaxe',
                'price': 25000,
                'efficiency': 2.0,
                'emoji': '⛏️'
            },
            'drill': {
                'name': 'Mining Drill',
                'price': 100000,
                'efficiency': 3.0,
                'emoji': '🔧'
            },
            'excavator': {
                'name': 'Excavator',
                'price': 500000,
                'efficiency': 5.0,
                'emoji': '🚜'
            }
        }
        
        # Craft packs
        self.craft_packs = {
            'tech': {
                'name': 'Tech Pack',
                'description': 'Advanced technology components',
                'requirements': {
                    'iron': 10,
                    'redstone': 5,
                    'gold': 3
                },
                'emoji': '📦'
            },
            'utility': {
                'name': 'Utility Pack',
                'description': 'General purpose utilities',
                'requirements': {
                    'coal': 20,
                    'iron': 5,
                    'lapis': 2
                },
                'emoji': '🧰'
            },
            'production': {
                'name': 'Production Pack',
                'description': 'Manufacturing components',
                'requirements': {
                    'coal': 15,
                    'iron': 8,
                    'gold': 2
                },
                'emoji': '🏭'
            }
        }
    
    async def _ensure_mine_exists(self, user_id: int, guild_id: int, mine_name: str = None) -> Dict[str, Any]:
        """Ensure user has a mine and return mine data."""
        async with self.bot.db.db.connect() as db:
            cursor = await db.execute(
                "SELECT * FROM mining WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            mine = await cursor.fetchone()
            
            if not mine:
                # Create new mine
                if not mine_name:
                    mine_name = f"Mine #{user_id % 10000}"
                
                await db.execute('''
                    INSERT INTO mining (user_id, guild_id, mine_name, coal, iron, gold, diamond, 
                                      emerald, lapis, redstone, unprocessed_materials, prestige_level)
                    VALUES (?, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                ''', (user_id, guild_id, mine_name))
                await db.commit()
                
                # Fetch the newly created mine
                cursor = await db.execute(
                    "SELECT * FROM mining WHERE user_id = ? AND guild_id = ?",
                    (user_id, guild_id)
                )
                mine = await cursor.fetchone()
            
            # Convert to dict
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, mine))
    
    @app_commands.command(name="start_mine", description="Start your mining career!")
    @app_commands.describe(name="Name for your mine (optional)")
    async def start_mine(self, interaction: discord.Interaction, name: str = None):
        """Start or update mining career."""
        try:
            await interaction.response.defer()
            
            # Use username if no name provided
            mine_name = name or f"{interaction.user.name}'s Mine"
            
            mine = await self._ensure_mine_exists(interaction.user.id, interaction.guild.id, mine_name)
            
            # Update name if provided
            if name:
                async with self.bot.db.db.connect() as db:
                    await db.execute(
                        "UPDATE mining SET mine_name = ? WHERE user_id = ? AND guild_id = ?",
                        (mine_name, interaction.user.id, interaction.guild.id)
                    )
                    await db.commit()
            
            embed = EmbedBuilder.success(
                "⛏️ Mining Career Started!",
                f"Welcome to **{mine_name}**!\n\n"
                "Use `/dig` to start mining for materials!\n"
                "Use `/mine` to view your mine information.\n"
                "Use `/process` to process unprocessed materials into valuable resources!"
            )
            
            embed.add_field(
                name="🎯 Getting Started",
                value="• Dig to find coal, ores, and unprocessed materials\n"
                      "• Process UM to discover rare gems\n"
                      "• Craft packs to enhance your mining\n"
                      "• Upgrade your equipment for better efficiency",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to start mine: {str(e)}")
            )
    
    @app_commands.command(name="mine", description="View your mine information")
    async def mine_info(self, interaction: discord.Interaction):
        """Show mine information."""
        try:
            await interaction.response.defer()
            
            mine = await self._ensure_mine_exists(interaction.user.id, interaction.guild.id)
            
            embed = discord.Embed(
                title=f"⛏️ {mine['mine_name']}",
                description=f"Owner: {interaction.user.mention}",
                color=0x8B4513  # Brown color for mining
            )
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Mining inventory
            inventory_text = ""
            for item_id, item_data in self.mining_items.items():
                amount = mine.get(item_id, 0)
                inventory_text += f"{item_data['emoji']} {item_data['name']}: {amount:,}\n"
            
            embed.add_field(
                name="📦 Inventory",
                value=inventory_text,
                inline=True
            )
            
            # Unprocessed materials and stats
            embed.add_field(
                name="🔄 Unprocessed",
                value=f"📦 Unprocessed Materials: {mine['unprocessed_materials']:,}",
                inline=True
            )
            
            embed.add_field(
                name="🏆 Stats",
                value=f"⭐ Prestige Level: {mine['prestige_level']}\n"
                      f"⏰ Last Dig: {mine.get('last_dig', 'Never') or 'Never'}",
                inline=True
            )
            
            # Instructions
            embed.add_field(
                name="🎮 Commands",
                value="• `/dig` - Mine for materials\n"
                      "• `/process` - Process unprocessed materials\n"
                      "• `/craft` - Craft useful packs\n"
                      "• `/upgrade` - Upgrade your equipment",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to show mine: {str(e)}")
            )
    
    @app_commands.command(name="dig", description="Dig in the mines for materials!")
    async def dig(self, interaction: discord.Interaction):
        """Dig for mining materials."""
        try:
            await interaction.response.defer()
            
            # Check cooldown (30 minutes)
            cooldown = await self.bot.db.check_cooldown(
                interaction.user.id, interaction.guild.id, "dig"
            )
            
            if cooldown:
                time_left = format_time_remaining(cooldown)
                embed = EmbedBuilder.warning(
                    "Dig Cooldown",
                    f"You can dig again in {time_left}"
                )
                await interaction.followup.send(embed=embed)
                return
            
            mine = await self._ensure_mine_exists(interaction.user.id, interaction.guild.id)
            
            # Generate dig results
            results = {}
            total_found = 0
            
            # Base number of items found (3-8)
            base_items = random.randint(3, 8)
            
            for _ in range(base_items):
                # Weighted random selection based on rarity
                weights = []
                items = []
                
                for item_id, item_data in self.mining_items.items():
                    if item_id in ['diamond', 'emerald']:
                        continue  # These come from processing only
                    items.append(item_id)
                    weights.append(item_data['rarity'])
                
                # Add unprocessed materials (higher chance)
                items.append('unprocessed_materials')
                weights.append(0.25)
                
                found_item = random.choices(items, weights=weights)[0]
                
                if found_item == 'unprocessed_materials':
                    amount = random.randint(1, 3)
                else:
                    amount = random.randint(1, 2)
                
                results[found_item] = results.get(found_item, 0) + amount
                total_found += amount
            
            # Update database
            async with self.bot.db.db.connect() as db:
                update_query = "UPDATE mining SET "
                update_values = []
                update_params = []
                
                for item, amount in results.items():
                    update_values.append(f"{item} = {item} + ?")
                    update_params.append(amount)
                
                update_values.append("last_dig = ?")
                update_params.extend([datetime.now().isoformat(), interaction.user.id, interaction.guild.id])
                
                update_query += ", ".join(update_values)
                update_query += " WHERE user_id = ? AND guild_id = ?"
                
                await db.execute(update_query, update_params)
                await db.commit()
            
            # Set cooldown (30 minutes)
            await self.bot.db.set_cooldown(
                interaction.user.id, interaction.guild.id, "dig", 0.5
            )
            
            # Create result embed
            embed = EmbedBuilder.success(
                "⛏️ Dig Complete!",
                f"You found {total_found} items while digging!"
            )
            
            results_text = ""
            for item, amount in results.items():
                if item == 'unprocessed_materials':
                    results_text += f"📦 Unprocessed Materials: {amount}\n"
                else:
                    item_data = self.mining_items[item]
                    results_text += f"{item_data['emoji']} {item_data['name']}: {amount}\n"
            
            embed.add_field(
                name="🎁 Items Found",
                value=results_text,
                inline=False
            )
            
            embed.add_field(
                name="💡 Tip",
                value="Use `/process` to turn unprocessed materials into rare gems!",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to dig: {str(e)}")
            )
    
    @app_commands.command(name="process", description="Process unprocessed materials into gems!")
    async def process(self, interaction: discord.Interaction):
        """Process unprocessed materials."""
        try:
            await interaction.response.defer()
            
            mine = await self._ensure_mine_exists(interaction.user.id, interaction.guild.id)
            
            um_amount = mine['unprocessed_materials']
            if um_amount <= 0:
                embed = EmbedBuilder.warning(
                    "No Materials",
                    "You don't have any unprocessed materials to process!\n"
                    "Use `/dig` to find some first."
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Process materials
            results = {}
            
            for _ in range(um_amount):
                # 15% chance for rare gems
                if random.random() < 0.15:
                    rare_gems = ['diamond', 'emerald', 'lapis', 'redstone']
                    gem = random.choice(rare_gems)
                    results[gem] = results.get(gem, 0) + 1
            
            if not results:
                embed = EmbedBuilder.warning(
                    "🔄 Processing Complete",
                    f"Processed {um_amount} unprocessed materials but found no rare gems this time.\n"
                    "Better luck next time!"
                )
            else:
                # Update database
                async with self.bot.db.db.connect() as db:
                    update_values = ["unprocessed_materials = 0"]
                    update_params = []
                    
                    for gem, amount in results.items():
                        update_values.append(f"{gem} = {gem} + ?")
                        update_params.append(amount)
                    
                    update_params.extend([interaction.user.id, interaction.guild.id])
                    
                    update_query = f"UPDATE mining SET {', '.join(update_values)} WHERE user_id = ? AND guild_id = ?"
                    await db.execute(update_query, update_params)
                    await db.commit()
                
                # Create success embed
                results_text = ""
                for gem, amount in results.items():
                    gem_data = self.mining_items[gem]
                    results_text += f"{gem_data['emoji']} {gem_data['name']}: {amount}\n"
                
                embed = EmbedBuilder.success(
                    "✨ Processing Complete!",
                    f"Processed {um_amount} unprocessed materials and found rare gems!"
                )
                
                embed.add_field(
                    name="💎 Gems Found",
                    value=results_text,
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to process: {str(e)}")
            )
    
    @app_commands.command(name="craft", description="Craft packs from materials")
    @app_commands.describe(
        pack_type="Type of pack to craft",
        amount="Amount to craft"
    )
    async def craft(self, interaction: discord.Interaction, pack_type: str = None, amount: str = "1"):
        """Craft packs."""
        try:
            await interaction.response.defer()
            
            if not pack_type:
                # Show available packs
                embed = discord.Embed(
                    title="🛠️ Crafting Menu",
                    description="Available packs to craft:",
                    color=0x8B4513
                )
                
                for pack_id, pack_data in self.craft_packs.items():
                    requirements_text = ""
                    for material, req_amount in pack_data['requirements'].items():
                        material_data = self.mining_items[material]
                        requirements_text += f"{material_data['emoji']} {req_amount} {material_data['name']}\n"
                    
                    embed.add_field(
                        name=f"{pack_data['emoji']} {pack_data['name']}",
                        value=f"{pack_data['description']}\n\n**Requirements:**\n{requirements_text}",
                        inline=False
                    )
                
                embed.add_field(
                    name="🎮 Usage",
                    value="Use `/craft <pack_type> <amount>` to craft packs",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            pack_type = pack_type.lower()
            if pack_type not in self.craft_packs:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Pack", f"Pack type '{pack_type}' not found!")
                )
                return
            
            # Parse amount
            try:
                craft_amount = int(amount) if amount != 'm' else 1
                if craft_amount <= 0:
                    raise ValueError()
            except ValueError:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Amount", "Amount must be a positive number!")
                )
                return
            
            mine = await self._ensure_mine_exists(interaction.user.id, interaction.guild.id)
            pack_data = self.craft_packs[pack_type]
            
            # Check if user has enough materials
            for material, req_amount in pack_data['requirements'].items():
                total_needed = req_amount * craft_amount
                if mine[material] < total_needed:
                    material_data = self.mining_items[material]
                    await interaction.followup.send(
                        embed=EmbedBuilder.error(
                            "Insufficient Materials",
                            f"You need {total_needed} {material_data['name']} but only have {mine[material]}!"
                        )
                    )
                    return
            
            # Calculate max craftable if using 'm'
            if amount == 'm':
                max_craftable = float('inf')
                for material, req_amount in pack_data['requirements'].items():
                    max_craftable = min(max_craftable, mine[material] // req_amount)
                craft_amount = max(1, int(max_craftable))
            
            # Craft packs
            async with self.bot.db.db.connect() as db:
                update_values = []
                update_params = []
                
                for material, req_amount in pack_data['requirements'].items():
                    total_used = req_amount * craft_amount
                    update_values.append(f"{material} = {material} - ?")
                    update_params.append(total_used)
                
                update_params.extend([interaction.user.id, interaction.guild.id])
                
                update_query = f"UPDATE mining SET {', '.join(update_values)} WHERE user_id = ? AND guild_id = ?"
                await db.execute(update_query, update_params)
                await db.commit()
            
            embed = EmbedBuilder.success(
                "🛠️ Crafting Complete!",
                f"Successfully crafted {craft_amount}x {pack_data['emoji']} **{pack_data['name']}**!"
            )
            
            # Show materials used
            used_text = ""
            for material, req_amount in pack_data['requirements'].items():
                total_used = req_amount * craft_amount
                material_data = self.mining_items[material]
                used_text += f"{material_data['emoji']} {total_used} {material_data['name']}\n"
            
            embed.add_field(
                name="📦 Materials Used",
                value=used_text,
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to craft: {str(e)}")
            )
    
    @app_commands.command(name="mining_inventory", description="Show your mining inventory")
    async def mining_inventory(self, interaction: discord.Interaction):
        """Show mining inventory."""
        try:
            await interaction.response.defer()
            
            mine = await self._ensure_mine_exists(interaction.user.id, interaction.guild.id)
            
            embed = discord.Embed(
                title=f"📦 {mine['mine_name']} - Inventory",
                color=0x8B4513
            )
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Show all materials
            inventory_text = ""
            total_items = 0
            
            for item_id, item_data in self.mining_items.items():
                amount = mine.get(item_id, 0)
                inventory_text += f"{item_data['emoji']} **{item_data['name']}:** {amount:,}\n"
                total_items += amount
            
            inventory_text += f"\n📦 **Unprocessed Materials:** {mine['unprocessed_materials']:,}"
            total_items += mine['unprocessed_materials']
            
            embed.add_field(
                name="🏪 Materials",
                value=inventory_text,
                inline=False
            )
            
            embed.add_field(
                name="📊 Summary",
                value=f"**Total Items:** {total_items:,}\n"
                      f"**Prestige Level:** {mine['prestige_level']}",
                inline=True
            )
            
            # Calculate estimated value (simplified)
            estimated_value = (
                mine['coal'] * 10 +
                mine['iron'] * 25 +
                mine['gold'] * 100 +
                mine['diamond'] * 1000 +
                mine['emerald'] * 1500 +
                mine['lapis'] * 200 +
                mine['redstone'] * 150 +
                mine['unprocessed_materials'] * 5
            )
            
            embed.add_field(
                name="💰 Estimated Value",
                value=f"{estimated_value:,} coins",
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to show inventory: {str(e)}")
            )
    
    @app_commands.command(name="upgrade", description="Upgrade your mining equipment")
    @app_commands.describe(
        upgrade_id="The upgrade to buy",
        amount="Amount to buy"
    )
    async def upgrade(self, interaction: discord.Interaction, upgrade_id: str = None, amount: int = 1):
        """Upgrade mining equipment."""
        try:
            await interaction.response.defer()
            
            if not upgrade_id:
                # Show available upgrades
                embed = discord.Embed(
                    title="⚡ Mining Upgrades",
                    description="Upgrade your equipment for better efficiency!",
                    color=0x8B4513
                )
                
                for unit_id, unit_data in self.mining_units.items():
                    embed.add_field(
                        name=f"{unit_data['emoji']} {unit_data['name']}",
                        value=f"**Price:** {format_currency(unit_data['price'])}\n"
                              f"**Efficiency:** {unit_data['efficiency']:.1f}x\n"
                              f"**ID:** `{unit_id}`",
                        inline=True
                    )
                
                embed.add_field(
                    name="🎮 Usage",
                    value="Use `/upgrade <upgrade_id> <amount>` to purchase upgrades",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            if upgrade_id not in self.mining_units:
                await interaction.followup.send(
                    embed=EmbedBuilder.error("Invalid Upgrade", f"Upgrade '{upgrade_id}' not found!")
                )
                return
            
            unit = self.mining_units[upgrade_id]
            total_cost = unit['price'] * amount
            
            # Check if player has enough cash
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
            
            embed = EmbedBuilder.success(
                "⚡ Upgrade Purchased!",
                f"You bought {amount}x {unit['emoji']} **{unit['name']}** for {format_currency(total_cost)}!"
            )
            
            embed.add_field(
                name="📈 Benefits",
                value=f"Efficiency: {unit['efficiency']:.1f}x\n"
                      "Your mining operations will be more effective!",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to upgrade: {str(e)}")
            )
    
    @app_commands.command(name="prestige", description="Prestige your mine for special rewards")
    @app_commands.describe(type="Type of prestige")
    async def prestige(self, interaction: discord.Interaction, type: str = "standard"):
        """Prestige mining operation."""
        try:
            await interaction.response.defer()
            
            mine = await self._ensure_mine_exists(interaction.user.id, interaction.guild.id)
            
            # Calculate prestige requirements (simplified)
            required_materials = {
                'coal': 1000,
                'iron': 500,
                'gold': 100,
                'diamond': 10,
                'emerald': 5
            }
            
            # Check requirements
            can_prestige = True
            missing_materials = []
            
            for material, required in required_materials.items():
                if mine[material] < required:
                    can_prestige = False
                    material_data = self.mining_items[material]
                    missing_materials.append(f"{material_data['emoji']} {required - mine[material]} more {material_data['name']}")
            
            if not can_prestige:
                embed = EmbedBuilder.warning(
                    "Prestige Requirements Not Met",
                    "You need the following materials to prestige:\n\n" + "\n".join(missing_materials)
                )
                
                # Show requirements
                req_text = ""
                for material, required in required_materials.items():
                    material_data = self.mining_items[material]
                    current = mine[material]
                    req_text += f"{material_data['emoji']} {current}/{required} {material_data['name']}\n"
                
                embed.add_field(
                    name="📋 Requirements",
                    value=req_text,
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            # Perform prestige
            crypto_reward = random.randint(5, 15)  # Simplified crypto reward
            
            async with self.bot.db.db.connect() as db:
                # Reset materials and increase prestige level
                await db.execute('''
                    UPDATE mining SET 
                    coal = 0, iron = 0, gold = 0, diamond = 0, emerald = 0, 
                    lapis = 0, redstone = 0, unprocessed_materials = 0,
                    prestige_level = prestige_level + 1
                    WHERE user_id = ? AND guild_id = ?
                ''', (interaction.user.id, interaction.guild.id))
                await db.commit()
            
            embed = EmbedBuilder.success(
                "🌟 Prestige Complete!",
                f"You've prestiged your mine to level {mine['prestige_level'] + 1}!\n\n"
                f"**Rewards:**\n"
                f"💎 {crypto_reward} Crypto\n"
                f"⭐ Increased prestige level\n"
                f"🎯 Better mining efficiency"
            )
            
            embed.add_field(
                name="🔄 Reset",
                value="All materials have been reset, but your prestige level gives permanent bonuses!",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", f"Failed to prestige: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(MiningCog(bot))
