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
	@has_roles_case_insensitive("staff", "it", "admin")
	async def ban(self, interaction : discord.Interaction, target : discord.Member, reason : str = None):
		match target:
			case _ if not interaction.user.guild_permissions.ban_members or interaction.user.guild_permissions.administrator:
				await interaction.response.send_message("You do not have the required permissions!", ephemeral= True)
			case t if t.id == interaction.user.id:
				await interaction.response.send_message("... can you like, elaborate why would you want yourself banned..?")
		reason = reason or "No reason given."
		try:
			await target.ban(reason=f"Banned by {interaction.user}, reason being: {reason} If you think this is a false ban, open a ticket!")
			await interaction.response.send_message(f"{target.mention} is banned successfully! Reason: {reason}")
		except Exception as e:
			await interaction.response.send_message(f"Ban failed! Reason given: {e}", ephemeral=True)

	@discord.app_commands.command(name="kick", description="Kicks the requested person")
	@has_roles_case_insensitive("staff", "it", "admin")
	async def kick(self, interaction : discord.Interaction, target : discord.Member, reason : str = None):
		match target:
			case t if not interaction.user.guild_permissions.kick_members or interaction.user.guild_permissions.administrator:
				await interaction.response.send_message("You do not have the required permissions!", ephemeral=True)
			case t if t.id == interaction.user.id:
				await interaction.response.send_message("We wouldn't want to kick ourselves now, do we?", ephemeral=True)
		reason = reason or "No reason given."
		try:
			await target.kick(reason=f"Kicked by {interaction.user}, reason being: {reason}. If you think this is a false kick, rejoin and open a ticket!")
			await interaction.response.send_message(f"Kicked {target.mention}! Reason: {reason}")
		except Exception as e:
			await interaction.response.send_message(f"Kick failed! Reason given: {e}", ephemeral=True)

	@discord.app_commands.command(name="timeout", description="Timeouts the person!")
	@discord.app_commands.describe(time="Time is in minutes, not seconds or hours! Use \"requested hours\"*60 for hours and so on")
	@has_roles_case_insensitive("staff", "admin", "it")
	async def timeout(self, interaction : discord.Interaction, target : discord.Member, time : int, reason : str = None):
		# shitty command line, does not work sometimes, shittier hack...
		match target:
			case _ if not interaction.user.guild_permissions.moderate_members or interaction.user.guild_permissions.administrator:
				await interaction.response.send_message("You do not have the required permissions!", ephemeral= True)
				return
			case t if t.id == interaction.user.id:
				await interaction.response.send_message("Why would you want to timeout yourself?", ephemeral=True)
				return
		reason = reason or "No reason given."
		until_time = datetime.now(timezone.utc) + timedelta(minutes=time)
		try:
			await target.timeout(until_time, reason=reason)
			await interaction.response.send_message(f"Timeouted {target.mention} for {time} minutes. Reason: \"{reason}\"")

		except Exception as e:
			await interaction.response.send_message(f"Timeout failed! Reason: {e}", ephemeral=True)
	@discord.app_commands.command(name="warn", description="Warns the person for given amount!")
	@discord.app_commands.describe(
		target = "Who to warn, use like you are pinging.",
		amount = "How many warnings was the offense? If warning exceeds 3, consider kicking or banning.",
		reason = "Reason of warn. Example: \"spamming\""
	)
	@has_roles_case_insensitive("it", "admin", "staff")
	async def warn(self, interaction : discord.Interaction, target : discord.Member, amount : int, reason : str = None):
		warn_data = self.warn_data
		roles = [role.name.lower() for role in target.roles]
		alerts = discord.utils.get(interaction.guild.text_channels, name="alerts")
		reason = reason or "No reason provided."

		match target:
			case t if not isinstance(t, (discord.User, discord.Member)):
				await interaction.response.send_message("Target is invalid.", ephemeral=True)
				return
			case t if t.bot:
				await interaction.response.send_message("You can not warn a bot.", ephemeral=True)
				return
			case t if t.id == interaction.user.id:
				await interaction.response.send_message("You can not warn yourself, why did you even try this?", ephemeral=True)
			case _ if any("admin" in r for r in roles):
				await interaction.response.send_message(f"You can not warn a admin. This incident has been noted.", ephemeral=True)
				await alerts.send(f"{interaction.user.mention} has attempted to warn a admin ({target.mention})")
				await target.send(f"You were attempted to be warned by another staff, {interaction.user}.")
				return
		try:
			with open(warn_data, "r", encoding='utf-8') as f:
				data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			data = {}

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

		ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
		ordinal_count = ordinals.get(count + 1, f"{count + 1}th")

		await interaction.response.send_message(f"Success! The target ({target.mention}) was warned! Reason: \"{reason}\"")
		await alerts.send(f"User warned: {target.mention} by {interaction.user.mention}, reason being: \"{reason}\". This is their {ordinal_count} violation.")
		try:
			await target.send(f"You have been warned by {interaction.user}! Reason: \"{reason}\". This is your {ordinal_count} strike. If you think this is a false warn open a ticket to appeal!")
		except discord.Forbidden:
			await interaction.followup.send(f"The user was unavailable, but the incident was noted.")
		if count + 1 > 3:
			await interaction.followup.send(f"This user's ({target.mention}) warn count has surpassed 3. You should really take a different penalizing option!", ephemeral=True)
			await alerts.send(f"This user's ({target.mention}) warn count has surpassed 3.")

		with open(warn_data, "w", encoding='utf-8') as f:
			json.dump(data, f, indent=4)

