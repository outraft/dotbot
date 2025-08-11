import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from cogs import GeneralCommands, AdministratorCommands

load_dotenv()

client = getenv("TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

async def setup_hooks():
	await bot.add_cog(GeneralCommands(bot))
	await bot.add_cog(AdministratorCommands(bot))

@bot.event
async def on_ready():
	sync = await bot.tree.sync()
	print(f"Logged in as {bot.user.name} and synced {len(sync)} commands")

bot.setup_hook = setup_hooks
bot.run(client)