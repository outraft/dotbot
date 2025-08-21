import discord
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv
import json
from .utils import embedMaker, has_roles_case_insensitive
from pathlib import Path
import asyncio

load_dotenv()

g_TOKEN = getenv("TOKEN")

class TicketCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		base_path = Path(__file__).parent.parent
		self.json_path = base_path / "data" / "ticket_data.json"
		try:
			with open(self.json_path, "r") as f:
				self.ticket_data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			self.ticket_data = {}

	async def cog_load(self):
		for guild_id, data in self.ticket_data.items():
			guild = await self.bot.fetch_guild(int(guild_id))
			if not guild:
				continue
			channel = await guild.fetch_channel(data["channel_id"])
			if not channel:
				continue
			try:
				msg = await channel.fetch_message(data["message_id"])
				view = self.TicketView(self, guild_id=guild_id)
				self.bot.add_view(view, message_id=msg.id)
			except:
				continue

	@commands.Cog.listener()
	async def on_ready(self):
		for guild in self.bot.guilds:
			channel = discord.utils.get(guild.text_channels, name="ticket")
			if not channel:
				continue
			guild_id = str(guild.id)
			message_id = self.ticket_data.get(guild_id, {}).get("message_id")
			ticket_counter = self.ticket_data.get(guild_id, {}).get("ticket_counter", 0)
			if message_id:
				try:
					msg = await channel.fetch_message(message_id)
					continue
				except:
					pass
			embed = await embedMaker(
				title="To open a ticket react to the message with \"🎫\"",
				message="This will notify admins and IT Team, use with caution, as false tickets is a rule-breaking offense!")
			view = self.TicketView(self, guild_id)
			msg = await channel.send(embed=embed, view=view)
			self.ticket_data[guild_id] = {"message_id": msg.id, "channel_id": channel.id, "ticket_counter": ticket_counter, "tickets": {}}
			with open(self.json_path, "w", encoding='utf-8') as f:
				json.dump(self.ticket_data, f, indent=4)


	class TicketView(discord.ui.View):
		def __init__(self, cog, guild_id):
			super().__init__(timeout=None)
			self.cog = cog
			self.guild_id = guild_id
		@discord.ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket_button")
		async def open_ticket(self, interaction : discord.Interaction, button : discord.ui.Button):
			guild_id = self.guild_id
			guild_data = self.cog.ticket_data.get(guild_id, {})
			tickets = guild_data.get("tickets", {})

			for ticket in tickets.values():
				if ticket["user"] == interaction.user.id:
					channel_id = ticket["ticket_channel"]
					await interaction.response.send_message(f"You have already opened a ticket | <#{channel_id}>", ephemeral=True)
					return

			ticket_counter = guild_data.get("ticket_counter", 0) + 1
			channel = await interaction.guild.create_text_channel(f"ticket-{ticket_counter:03}",
			overwrites={
				interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
				interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
			}
			)
			user = interaction.user.id
			status = "open"

			guild_data["ticket_counter"] = ticket_counter
			guild_data["tickets"][str(ticket_counter)] = {
				"user": user,
				"ticket_channel": channel.id,
				"status": status,
				"escalation": {}
			}
			self.cog.ticket_data[guild_id] = guild_data
			with open(self.cog.json_path, "w", encoding="utf-8") as f:
				json.dump(self.cog.ticket_data, f, indent=4)

			await interaction.response.send_message(f"Ticket has been opened at {channel.mention}", ephemeral=True)
			await channel.send(embed= await embedMaker(title="Staff has been notified of your ticket!", message="Describe your problem in a few, simple sentences. A staff will arrive soon to help you out!", isTimestamped=True))
			admin_cog = self.cog.bot.get_cog("AdminTicketCommands")
			if admin_cog:
				await admin_cog.notifyAdmins(interaction.guild, channel)

class AdminTicketCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.ticket_cog = self.bot.get_cog("TicketCommands")
		base_path = Path(__file__).parent.parent
		self.json_path = base_path / "data" / "admin_ticket_data.json"
		try:
			with open(self.json_path, "r") as f:
				self.admin_data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			self.admin_data = {}

	async def cog_load(self):
		ticket_cog = self.ticket_cog
		for guild_id, data in ticket_cog.ticket_data.items():
			guild = self.bot.get_guild(int(guild_id))
			if not guild:
				continue
			channel = guild.get_channel(data["channel_id"])
			if not channel:
				continue
			#escalator = data[]
			try:
				msg = await channel.fetch_message(data["message_id"])
				view1 = self.AdminTicketView(self, guild_id, channel)
				view2 = self.AdminEscalateView(guild_id, channel)
				self.bot.add_view(view1, message_id=msg.id)
				#self.bot.add_view(view2, message_id=)
			except:
				continue

	async def notifyAdmins(self, guild, ticket_channel):
		admin_channel = discord.utils.get(guild.text_channels, name="alerts")
		view = self.AdminTicketView(self, guild.id, ticket_channel)
		ticket_cog = self.ticket_cog
		ticket_id = str(int((ticket_channel.name).split("-")[-1]))
		user_id = ticket_cog.ticket_data[str(guild.id)]["tickets"][ticket_id]["user"]
		if admin_channel:
			await admin_channel.send(f"New ticket: {ticket_channel.mention} by <@{user_id}>", view=view)

	@discord.app_commands.command(name="closeticket", description="Closes the ticket opened by the user.")
	@has_roles_case_insensitive("admin", "it")
	async def closeticket(self, interaction : discord.Interaction):
		if "ticket" in interaction.channel.name.lower():
			await interaction.response.send_message(f"This ticket is closed by {interaction.user.mention}, the channel will be closed in 5 seconds.")
			await asyncio.sleep(5)

			ticket_cog = self.ticket_cog
			guild_id = interaction.guild.id
			channel_name = interaction.channel.name
			ticket_id = str(int(channel_name.split("-")[-1]))
			status = "closed"

			ticket_cog.ticket_data[str(guild_id)]["tickets"][ticket_id]["status"] = status
			with open(ticket_cog.json_path, "w", encoding='utf-8') as f:
				json.dump(ticket_cog.ticket_data, f, indent=4)

			await interaction.channel.delete()

	@discord.app_commands.command(name="escalate", description="Escalates ticket to admins.")
	@has_roles_case_insensitive("it")
	async def escalate(self, interaction : discord.Interaction):
		if "ticket" in interaction.channel.name.lower():
			await interaction.response.send_message(f"This ticket has been escalated to admins by {interaction.user.mention}, please wait for a admin.")

			ticket_cog = self.ticket_cog
			guild_id = interaction.guild.id
			channel_name = interaction.channel.name
			ticket_id = str(int(channel_name.split("-")[-1]))
			editable = ticket_cog.ticket_data[str(guild_id)]["tickets"][ticket_id]

			editable["status"] = "escalated"


			admin_channel = discord.utils.get(interaction.guild.text_channels, name="alerts")
			view = self.AdminEscalateView(self, interaction.guild.id, interaction.channel, interaction.user)

			msg = await admin_channel.send(f"The ticket {interaction.channel.mention} has been escalated. A administrative staff needs to take a look!", view=view)
			editable["escalation"] = {
				"escalator": interaction.user.id,
				"escalation_id": msg.id
			}
			with open(ticket_cog.json_path, "w", encoding='utf-8') as f:
				json.dump(ticket_cog.ticket_data, f, indent=4)

	class AdminTicketView(discord.ui.View):
		def __init__(self, cog, guild_id, ticket_channel):
			super().__init__(timeout=0)
			self.cog = cog
			self.guild_id = guild_id
			self.ticket_channel = ticket_channel
		@discord.ui.button(label="📨 Take Ticket", custom_id="take_ticket_button")
		async def take_ticket(self, interaction: discord.Interaction, button : discord.ui.Button):
			ticket_channel = self.ticket_channel

			roles = [role.name.lower() for role in interaction.user.roles]
			if any("admin" in r for r in roles):
				await ticket_channel.send(f"Your ticket has been taken by {interaction.user.mention}, which is a admin.")
			elif any("it" in r for r in roles):
				await ticket_channel.send(f"Your ticket has been taken by {interaction.user.mention}, which is a IT Staff. This ticket can be escalated by the staff member.")
			else:
				await interaction.response.send_message("You do not have the permission to take tickets!", ephemeral=True)
	class AdminEscalateView(discord.ui.View):
		def __init__(self, cog, guild_id, ticket_channel, escalator):
			super().__init__(timeout=0)
			self.cog = cog
			self.guild_id = guild_id
			self.ticket_channel = ticket_channel
			self.escalator = escalator
		@discord.ui.button(label=":exclamation: Escalate Ticket", custom_id="escalate_button")
		async def escalate(self, interaction : discord.Interaction, button : discord.ui.Button):
			ticket_channel = self.ticket_channel
			escalator = self.escalator
			roles = [role.name.lower() for role in interaction.user.roles]
			if any("admin" in r for r in roles):
				await ticket_channel.send(f"The escalation has been taken by {interaction.user.mention}, which is a admin.")
				await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
			elif any("it" in r for r in roles):
				await interaction.response.send_message(f"This ticket has already been escalated by {escalator.mention}", ephemeral=True)
			else:
				await interaction.response.send_message("You do not have the permission to escalate tickets!", ephemeral=True)



