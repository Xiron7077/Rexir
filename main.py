import discord
from discord.ext import commands
from discord import app_commands, ui
from dotenv import load_dotenv
import os

# Load token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup bot
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix='>')


# Checks if user is owner
def is_owner(interaction: discord.Interaction):
    return interaction.user.id == 501005884537831424 or interaction.user.guild_permissions.administrator


# Refreshes the buttons to keep them functioning
class PersistentViewBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=">", intents=intents)

    async def setup_hook(self) -> None:
        await bot.load_extension("cogs.economy")
        cog_instance = bot.get_cog("Economy")
        button_instance1 = cog_instance.InitiateButton()
        bot.add_view(button_instance1)


# Redeclaration of bot after made presistant
bot = PersistentViewBot()


# Creates an on_ready event that loads all the cogs and syncs slash commands
@bot.event
async def on_ready():
    print(f"{bot.user} has successfully connected to discord.")
    await bot.change_presence(activity=discord.Game("Xiron"))
    for file_name in os.listdir("./cogs"):
        if file_name.endswith(".py"):
            if file_name == "economy.py":
                continue
            await bot.load_extension(f"cogs.{file_name[:-3]}")
    try:
        synced = await bot.tree.sync()
        print(f"{bot.user} has synced {len(synced)} commands")
    except:  # Error if it fails to sync all the slash commands
        print(f"Anomaly Detected!\n{bot.user} could not sync commands")


@bot.event
async def on_message(message: discord.Message) -> None:
    user_message = message.content.lower()
    if user_message == "hello":
        await message.channel.send("hey there mate")


# slash command that performs loading functions
@bot.tree.command(name="load", description="Performs load actions.")
@app_commands.check(is_owner)
@app_commands.describe(load_action="Please enter the load action you want to perform.", extension="Please enter the extension.")
@app_commands.choices(
    load_action=[
        discord.app_commands.Choice(name="Load", value=1),
        discord.app_commands.Choice(name="UnLoad", value=2),
        discord.app_commands.Choice(name="ReLoad", value=3),
        discord.app_commands.Choice(name="Load All", value=4),
        discord.app_commands.Choice(name="UnLoad All", value=5),
        discord.app_commands.Choice(name="ReLoad All", value=6)
    ]
)
async def load(interaction: discord.Interaction, load_action: int, extension: str = None):
    if load_action == 1:  # loads specific cog
        await bot.load_extension(f'cogs.{extension}')
        await interaction.response.send_message(f'The extension `{extension}` is loaded.')
    elif load_action == 2:  # unloads specific cog
        await bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f'The extension `{extension}` is unloaded.')
    elif load_action == 3:  # reloads specific cog
        await bot.unload_extension(f"cogs.{extension}")
        await bot.load_extension(f'cogs.{extension}')
        await interaction.response.send_message(f'The extension `{extension}` is reloaded.')
    elif load_action == 4:  # loads all the cogs
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                await bot.load_extension(f'cogs.{file[:-3]}')
        await interaction.response.send_message(f'All the extension `{extension}` is loaded.')
    elif load_action == 5:  # unloads all the cogs
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                await bot.unload_extension(f'cogs.{file[:-3]}')
        await bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f'All the extension `{extension}` is unloaded.')
    elif load_action == 6:  # reloads all the cogs
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                await bot.unload_extension(f'cogs.{file[:-3]}')
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                await bot.load_extension(f'cogs.{file[:-3]}')
        await bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f'All the extension `{extension}` is reloaded.')
    try:  # syncs all the slash commands
        synced = await bot.tree.sync()
        print(f"{bot.user} has synced {len(synced)} commands")
    except:  # Error if it fails to sync all the slash commands
        print(f"Anomaly Detected!\n{bot.user} could not sync commands")


# Performs specified function on command error
@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error):
    await interaction.response.send_message("You don't have permissions for this command.", ephemeral=True)
    print(error)

# runs the bot
bot.run(TOKEN)
