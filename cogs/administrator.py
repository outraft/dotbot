import discord
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv
from datetime import timedelta, datetime, timezone
from .utils import has_roles_case_insensitive
from pathlib import Path
import json

load_dotenv()

g_TOKEN = getenv("TOKEN")

class AdministratorCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		base_path = Path(__file__).parent.parent
		self.warn_data = base_path / "data" / "warn_data.json"

	@discord.app_commands.command(name="ban", description="Bans the requested person")
	async def ban(self, interaction : discord.Interaction, target : discord.Member, reason : str = None):
		if not interaction.user.guild_permissions.ban_members or interaction.user.guild_permissions.administrator:
			await interaction.response.send_message("You do not have the required permissions!", ephemeral= True)
		try:
			if reason is not None:
				await target.ban(reason=f"Banned by {interaction.user}, reason being: {reason} If you think this is a false ban, open a ticket!")
			else:
				await target.ban(reason=f"Banned by {interaction.user}, no reason given. If you think this is a false ban, open a ticket!")
			await interaction.response.send_message(f"{target.mention} is banned successfully! Reason: {reason}")
		except Exception as e:
			await interaction.response.send_message(f"Ban failed! Reason given: {e}", ephemeral=True)

	@discord.app_commands.command(name="kick", description="Kicks the requested person")
	async def kick(self, interaction : discord.Interaction, target : discord.Member, reason : str = None):
		if not interaction.user.guild_permissions.kick_members or interaction.user.guild_permissions.administrator:
			await interaction.response.send_message("You do not have the required permissions!", ephemeral=True)
		try:
			if reason is not None:
				await target.kick(reason=f"Kicked by {interaction.user}, reason being: {reason}. If you think this is a false kick, rejoin and open a ticket!")
			else:
				await target.kick(reason=f"Kicked by {interaction.user}, no reason given. If you think this is a false kick, rejoin and open a ticket!")
			await interaction.response.send_message(f"Kicked {target.mention}! Reason: {reason}")
		except Exception as e:
			await interaction.response.send_message(f"Kick failed! Reason given: {e}", ephemeral=True)

	@discord.app_commands.command(name="timeout", description="Timeouts the person!")
	@discord.app_commands.describe(time="Time is in minutes, not seconds or hours! Use \"requested hours\"*60 for hours and so on")
	async def timeout(self, interaction : discord.Interaction, target : discord.Member, time : int, reason : str = None):
		# shitty command line, does not work sometimes, shittier hack...
		if not interaction.user.guild_permissions.moderate_members or interaction.user.guild_permissions.administrator:
			await interaction.response.send_message("You do not have the required permissions!", ephemeral= True)
		until_time = datetime.now(timezone.utc) + timedelta(minutes=time)
		try:
			if reason is not None:
				await target.timeout(until_time, reason=reason)
				await interaction.response.send_message(f"Timeouted {target.mention} for {time} minutes. Reason: {reason}")
			else:
				await target.timeout(until_time)
				await interaction.response.send_message(f"Timeouted {target.mention} for {time} minutes. No reason given.")
		except Exception as e:
			await interaction.response.send_message(f"Timeout failed! Reason: {e}", ephemeral=True)
	@discord.app_commands.command(name="warn", description="Warns the person for given amount!")
	@discord.app_commands.describe(
		target = "Who to warn, use like you are pinging.",
		amount = "How many warnings was the offense? If warning exceeds 3, consider kicking or banning.",
		reason = "Reason of warn. Example: \"spamming\""
	)
	@has_roles_case_insensitive("it", "admin", "staff")
	async def warn(self, interaction : discord.Interaction, target : discord.Member, reason:str = None, amount : int = None):
		warn_data = self.warn_data
		roles = [role.name.lower() for role in target.roles]
		alerts = discord.utils.get(interaction.guild.text_channels, name="alerts")
		try:
			with open(warn_data, "r", encoding='utf-8') as f:
				data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			data = {}

		if any("admin" in r for r in roles):
			await interaction.response.send_message(f"You can not warn a admin. This incident has been noted.")
			await alerts.send(f"{interaction.user.mention} has attempted to warn a admin ({target.mention})")
			await target.send(f"You were attempted to be warned by another staff, {interaction.user}")
			return

		key = str(target.id)
		exists = data.get(key, {})

		if not exists:
				count = 0
				data[key] = {
					"count": count + 1,
					"reason": [reason]
				}
		else:
			count = exists.get("count", 0)
			data[key]["count"] = count + 1
			data[key]["reason"].append(reason)
		await interaction.response.send_message(f"Success! The target ({target.mention}) was warned! Reason: {reason}")
		await alerts.send(f"User warned: {target.mention} by {interaction.user.mention}, reason being: {reason}")
		await target.send(f"You have been warned by {interaction.user}! Reason: {reason}. If you think this is a false warn open a ticket to appeal!")
		# warn_data
		# {user{count=a, reason(s)}}

