import discord
from discord.ext import commands, tasks
from os import getenv
from dotenv import load_dotenv
import json
import random
from pathlib import Path
from .utils import embedMaker, has_roles_case_insensitive
import discord.ui
import asyncio

load_dotenv()

g_TOKEN = getenv("TOKEN")

class GeneralCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		base_path = Path(__file__).parent.parent
		self.status_json = base_path / "data" / "status.json"
		self.role_data_json = base_path / "data" / "role_data.json"

	@commands.Cog.listener()
	async def on_ready(self):
		self.change_status.start()
		# React for role
		for guild in self.bot.guilds:
			channel = discord.utils.get(guild.text_channels, name="role-chat")
			if not channel:
				continue
			g_id = str(guild.id)
			try:
				with open(self.role_data_json, "r", encoding='utf-8') as f:
					data = json.load(f)
			except:
				data = {}
			m_id = data.get(g_id, {}).get("m_id")
			if m_id:
				try:
					msg = await channel.fetch_message(m_id)
					return
				except:
					pass

			coder_r = discord.utils.get(guild.roles, name="∘ Coder ∘")
			coder_length = len(coder_r.members) if coder_r else 0
			artist_r = discord.utils.get(guild.roles, name="∘ Artist ∘")
			artist_length = len(artist_r.members) if artist_r else 0
			game_night_r = discord.utils.get(guild.roles, name="∘ Game Night ∘")
			game_night_length = len(game_night_r.members) if game_night_r else 0
			embed = await embedMaker(
			title="Use this message to get your specified roles!",
			message= "If you haven't got it by answering the questionnare or want to get rid of it.",
			fields=[
				{"name": "", "value":"React with 🖌️ to get the \"Artist\" role."},
				{"name": "", "value": "React with 💻 to get the \"Coder\" role."},
				{"name": "", "value": "React with 🎮 to get the \"Game Night\" role."},
				{"name": "", "value": "To remove the role you got, unreact to the role."}]
			)
			msg = await channel.send(embed=embed)
			await msg.add_reaction("🖌️")
			await msg.add_reaction("💻")
			await msg.add_reaction("🎮")

			data[g_id] = {
				"m_id": msg.id,
				"count": {
					"∘ Artist ∘": artist_length,
					"∘ Coder ∘": coder_length,
					"∘ Game Night ∘": game_night_length
					}
				}

			with open(self.role_data_json, "w", encoding='utf-8') as f:
				json.dump(data, f, indent=4)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		guild = self.bot.get_guild(payload.guild_id)
		member = guild.get_member(payload.user_id)
		if payload.member.bot:
			return
		with open(self.role_data_json, "r", encoding='utf-8') as f:
			data = json.load(f)

		g_id = str(payload.guild_id)
		m_id = data.get(g_id, {}).get("m_id")

		if not m_id or m_id != payload.message_id:
			return

		role_map = {
			"🖌️": "∘ Artist ∘",
			"💻": "∘ Coder ∘",
			"🎮": "∘ Game Night ∘"
		}

		role_name = role_map.get(str(payload.emoji))
		role = discord.utils.get(guild.roles, name=role_name)

		if role in member.roles:
			old_count = data[g_id]["count"][role_name]
			data[g_id]["count"][role_name] = old_count + 1
			return

		if role_name:
			role = discord.utils.get(guild.roles, name=role_name)
			if member and role:
				await member.add_roles(role)
				old_count = data[g_id]["count"][role_name]
				data[g_id]["count"][role_name] = old_count + 1

		with open(self.role_data_json, "w", encoding='utf-8') as f:
			json.dump(data, f, indent=4)

	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, payload):
		guild = self.bot.get_guild(payload.guild_id)
		member = guild.get_member(payload.user_id)

		if member.bot:
			return

		with open(self.role_data_json, "r", encoding='utf-8') as f:
			data = json.load(f)

		g_id = str(payload.guild_id)
		m_id = data.get(g_id, {}).get("m_id")

		if not m_id or m_id != payload.message_id:
			return

		role_map = {
			"🖌️": "∘ Artist ∘",
			"💻": "∘ Coder ∘",
			"🎮": "∘ Game Night ∘"
		}

		role_name = role_map.get(str(payload.emoji))
		role = discord.utils.get(guild.roles, name=role_name)

		if role_name:
			member = guild.get_member(payload.user_id)
			role = discord.utils.get(guild.roles, name=role_name)
			if member and role:
				try:
					await member.remove_roles(role)
				except Exception as e:
					print(f"{e}")
				old_count = data[g_id]["count"][role_name]
				data[g_id]["count"][role_name] = old_count - 1

		with open(self.role_data_json, "w", encoding='utf-8') as f:
			json.dump(data, f, indent=4)

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
	@has_roles_case_insensitive("it", "admin", "staff")
	@discord.app_commands.command(name="clearchat", description="Clears chat for given amount")
	@discord.app_commands.describe(
		count = "Number of messages that will be deleted after the use of command. Use a integer OR \"all\""
		)
	async def clearchat(self, interaction : discord.Interaction, count : str = "all"):
		if count.lower() == "all":
			view = self.confirmpurge(interaction.user)
			await interaction.response.send_message(f"This is a irrevertable command. Are you sure to purge all of the chat? Click \"Yes\" below to continue.", view=view, ephemeral=True)
			await view.wait()

			if view.value is None:
				await interaction.followup.send("Timed out.", ephemeral=True, delete_after=10)
			elif view.value:
				deleted = await interaction.channel.purge()
				msg = await interaction.followup.send(f"Deleted every message sent, which equals to {len(deleted)}", ephemeral=True)
				await asyncio.sleep(5)
				await msg.delete()
		else:
			try:
				count = int(count)
				deleted = await interaction.channel.purge(limit=count)
				await interaction.response.send_message(f"Deleted {len(deleted)} messages!", ephemeral=True, delete_after=5)
			except ValueError:
				await interaction.response.send_message("Are you sure that you used a integer or \"all\"?")
	class confirmpurge(discord.ui.View):
		def __init__(self, author, timeout = 10):
			super().__init__(timeout=timeout)
			self.author = author
			self.value = None

		@discord.ui.button(label="Yes ✔️", style=discord.ButtonStyle.danger)
		async def confirm(self, interaction : discord.Interaction, button : discord.ui.Button):
			if interaction.user.id != self.author.id:
				await interaction.response.send_message("How did you even access this? The message was supposed to be ephemeral!", ephemeral=True, delete_after=5)
				return

			self.value = True
			await interaction.response.defer()
			self.stop()

		@discord.ui.button(label="No ❌", style=discord.ButtonStyle.secondary)
		async def deny(self, interaction : discord.Interaction, button : discord.ui.Button):
			if interaction.user.id != self.author.id:
				await interaction.response.send_message("How did you even access this? The message was supposed to be ephemeral!", ephemeral=True, delete_after=5)
				return

			self.value = True
			await interaction.response.defer()
			self.stop()