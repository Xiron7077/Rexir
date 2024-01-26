import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from pymongo import *
from main import is_owner
from dotenv import load_dotenv
import random
import asyncio

# creates a mongo client to connect to mongo database
load_dotenv()
client = MongoClient('MONGO_CLIENT')
discord_data = client.get_database("DiscordData")
economy_data = discord_data.Economy


# checks if user exists in the database
def check_player(player_id):
    coin_data = economy_data.find_one({"type": "coins"})
    player_coin_list = coin_data["player_coins_list"]
    for player in player_coin_list:
        if player_id == player["id"]:
            return True
    return False


# adds currency to the specified user
def add_coins(player_id, coins):
    coins_data = economy_data.find_one({"type": "coins"})
    player_coins_list = coins_data["player_coins_list"]
    for player in player_coins_list:
        if player_id == player["id"]:
            player["coins"] += coins
            break
    new_player_list = {
        "player_coins_list": player_coins_list
    }
    economy_data.update_one({"type": "coins"}, {"$set": new_player_list})


# noinspection PyUnresolvedReferences
# Economy class for game currency system
class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection PyUnresolvedReferences
    # Button used to initiate new user account
    class InitiateButton(View):
        def __init__(self):
            super().__init__(timeout=None)

        @button(label="Initiate", style=discord.ButtonStyle.blurple, custom_id="initiate")
        async def initiate_button(self, interaction: discord.Interaction, button: Button):
            if check_player(interaction.user.id):
                await interaction.response.send_message("Your account is already initiated.", ephemeral=True)
            else:
                coin_data = economy_data.find_one({"type": "coins"})
                previous_coin_data = coin_data["player_coins_list"]
                new_coin_data = {
                    "player_coins_list": previous_coin_data + [{"id": int(interaction.user.id), "coins": 500}]
                }
                economy_data.update_one({"type": "coins"}, {"$set": new_coin_data})
                await interaction.response.send_message(
                    "Your account has been successfully initiated with initial value of 500", ephemeral=True)

    # noinspection PyUnresolvedReferences
    # button for selection in rock paper scissors game
    class RpsButton(View):
        def __init__(self, user_id):
            super().__init__(timeout=60)
            self.user_id = user_id

        player_choice = ""
        game_output = 2
        rps_list = ["🪨", "📜", "✂️"]
        bot_choice = random.choice(rps_list)

        # checks if the interaction user is the same as that who used the command
        async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
            return interaction.user.id == self.user_id

        # disables all the buttons
        async def disable_buttons(self):
            for item in self.children:
                if isinstance(item, Button):
                    item.disabled = True

        # shows output after the game ends
        async def output(self, interaction: discord.Interaction):
            if self.game_output == 0:
                await interaction.message.edit(
                    content=f"You: {self.player_choice}\nBot: {self.bot_choice}\nYou Lost.", view=None, embed=None)
            elif self.game_output == 1:
                await interaction.message.edit(
                    content=f"You: {self.player_choice}\nBot: {self.bot_choice}\nYou Won.", view=None, embed=None)
            else:
                await interaction.message.edit(
                    content=f"You: {self.player_choice}\nBot: {self.bot_choice}\nIt's Draw.", view=None, embed=None)

        # button for selecting rock
        @button(style=discord.ButtonStyle.red, custom_id="rock", emoji="🪨")
        async def rock(self, interaction: discord.Interaction, button: Button):
            self.player_choice = "🪨"
            if self.bot_choice == "📜":
                self.game_output = 0
            elif self.bot_choice == "✂️":
                self.game_output = 1
            await self.output(interaction)

        # button for selecting paper
        @button(style=discord.ButtonStyle.blurple, custom_id="paper", emoji="📜")
        async def paper(self, interaction: discord.Interaction, button: Button):
            self.player_choice = "📜"
            if self.bot_choice == "✂️":
                self.game_output = 0
            elif self.bot_choice == "🪨":
                self.game_output = 1
            await self.output(interaction)

        # button for selecting scissor
        @button(style=discord.ButtonStyle.green, custom_id="scissor", emoji="✂️")
        async def scissors(self, interaction: discord.Interaction, button: Button):
            self.player_choice = "✂️"
            if self.bot_choice == "🪨":
                self.game_output = 0
            elif self.bot_choice == "📜":
                self.game_output = 1
            await self.output(interaction)

        # disables all the buttons on timeout
        async def on_timeout(self) -> None:
            for item in self.children:
                if isinstance(item, Button):
                    item.disabled = True

    # slash command that sends the initiate embed for initiating new economy account
    @app_commands.command(name="initiate_embed", description="Sends an embed for initiating account")
    @app_commands.check(is_owner)
    @commands.guild_only()
    async def initiate(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Initiate your account",
            colour=discord.Colour.gold(),
            description="Click on initiate button to initiate your rexir economy account"
        )
        await interaction.response.send_message("embed sent!", ephemeral=True)
        await interaction.channel.send(embed=embed, view=Economy.InitiateButton())

    # slash command that adds currency to a specific user
    @app_commands.command(name="add_coins", description="Adds coins to the specified user.")
    @app_commands.describe(player_id="Please enter the id of user.", coins="Please enter the amount of coins to add.")
    @app_commands.check(is_owner)
    @commands.guild_only()
    async def add_coins(self, interaction: discord.Interaction, player_id: str, coins: int):
        player_id = float(player_id)
        if not check_player(player_id):
            await interaction.response.send_message(f"The player has not initiated their account.", ephemeral=True)
        else:
            add_coins(player_id, coins)
            await interaction.response.send_message(f"{coins} coins have been added to the player account", ephemeral=True)

    # slash command to check your available currency
    @app_commands.command(name="check_coins", description="Shows you the amount of coins you have.")
    @commands.guild_only()
    async def check_coins(self, interaction: discord.Interaction):
        if not check_player(interaction.user.id):
            await interaction.response.send_message(f"You have not initiated your account yet. Click on initiate button.")
        else:
            coins_data = economy_data.find_one({"type": "coins"})
            player_coins_list = coins_data["player_coins_list"]
            for player in player_coins_list:
                if player["id"] == interaction.user.id:
                    coins = player["coins"]
                    await interaction.response.send_message(f"Coins: {coins}")

    # slash command for playing rock paper scissor
    @app_commands.command(name="rps", description="Play rock paper scissor game.")
    @app_commands.describe(game_mode="Please choose your game mode", player_id="Please enter id of opponent")
    @app_commands.choices(
        game_mode=[
            discord.app_commands.Choice(name="Single Player", value=1),
            discord.app_commands.Choice(name="Multi Player", value=2)
        ]
    )
    @commands.guild_only()
    async def rps(self, interaction: discord.Interaction, game_mode: int, player_id: str = None):
        user_id = interaction.user.id
        if game_mode == 1:  # initiates game for single player mode
            if not check_player(interaction.user.id):
                await interaction.response.send_message(f"The player has not initiated their account.", ephemeral=True)
            else:
                embed = discord.Embed(
                    title="Rock Paper Scissors",
                    colour=discord.Colour.red(),
                    description="Please choose your option:\n\n1.Rock - 🪨\n2.Paper - 📜\n3.Scissors - ✂️"
                )
                await interaction.response.send_message(embed=embed, view=Economy.RpsButton(user_id))
        else:
            player_id = float(player_id)
            if not check_player(player_id):
                await interaction.response.send_message(f"The player has not initiated their account.", ephemeral=True)


# adds the economy cog to main file
async def setup(bot):
    await bot.add_cog(Economy(bot))
