import discord
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv
from datetime import timedelta, datetime, timezone

load_dotenv()

g_TOKEN = getenv("TOKEN")

class AdministratorCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

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