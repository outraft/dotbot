import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from cogs import GeneralCommands, AdministratorCommands, TicketCommands, AdminTicketCommands, CalendarCommands

load_dotenv()

client = getenv("TOKEN")
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

async def setup_hooks():
	await bot.add_cog(GeneralCommands(bot))
	await bot.add_cog(AdministratorCommands(bot))
	await bot.add_cog(TicketCommands(bot))
	await bot.add_cog(AdminTicketCommands(bot))
	await bot.add_cog(CalendarCommands(bot))

@bot.event
async def on_ready():
	sync = await bot.tree.sync()
	print(f"Logged in as {bot.user.name} and synced {len(sync)} commands")

bot.setup_hook = setup_hooks
bot.run(client)