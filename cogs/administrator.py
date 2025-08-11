from discord import app_commands, Interaction
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv

load_dotenv()

g_TOKEN = getenv("TOKEN")

class AdministratorCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		#TODO: add ban, kick, and more staff stuff
		#TODO: maybe add ticket here? or split idk?