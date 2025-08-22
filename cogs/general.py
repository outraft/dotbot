import discord
from discord.ext import commands, tasks
from os import getenv
from dotenv import load_dotenv
import json
import random
from pathlib import Path
from .utils import embedMaker

load_dotenv()

g_TOKEN = getenv("TOKEN")

class GeneralCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		base_path = Path(__file__).parent.parent
		self.status_json = base_path / "data" / "status.json"

	@commands.Cog.listener()
	async def on_ready(self):
		print("started status!")
		self.change_status.start()

	@tasks.loop(minutes=20)
	async def change_status(self):
		status_json = self.status_json
		with open(file=status_json, mode="r", encoding='utf-8') as f:
			data = json.load(f)
		statuses = data["statuses"]
		status = random.choice(statuses)
		status = status[:128]
		print(f"found status: \"{status}\"")
		try:
			await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=(status)))
		except Exception as e:
			print(e)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		wchat = discord.utils.get(member.guild.text_channels, name="welcome")
		if not wchat:
			print(f"no channel as wchat: {wchat}")
			return

		embed = await embedMaker(f"We hope you have a fantastic day!", "Don't forget to read the rules!", isTimestamped=True, footer=f"{member.guild.icon.url}\tAt {member.guild.name}, we love making games!")
		try:
			await wchat.send(f"Welcome, {member.mention} to {member.guild.name}!", embed=embed)
		except Exception as e:
			print(e)