from discord import app_commands, Interaction
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv

load_dotenv()

g_TOKEN = getenv("TOKEN")

class GeneralCommands(commands.Cog):
	def __init__(bot, self):
		self.bot = bot

	@app_commands.command(name="test", description="test")
	async def test(self, interaction: Interaction):
		await interaction.response.send_message("Test complete!")

		#TODO: check server for more details
		#TODO: oh and do a custom status stuff...