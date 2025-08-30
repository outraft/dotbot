import discord
from discord.ext import commands
import datetime
from pathlib import Path
import json
from .utils import embedMaker, has_roles_case_insensitive


class CalendarCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		base_path = Path(__file__).parent.parent
		self.calendar_data = base_path / "data" / "calendar_data.json"

	@discord.app_commands.command(name="calendar", description="Shows the monthly event calendar!")
	async def calendar(self, interaction : discord.Interaction):

		now = datetime.datetime.now()
		m_name = now.strftime("%B")
		m_number = now.month

		try:
			with open(self.calendar_data, "r", encoding='utf-8') as f:
				data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			data = {}

		g_id = str(interaction.guild_id)
		if not data.get(g_id):
			await interaction.response.send_message(f"No events planned yet.")
			return

		fields = []
		for eventid, eventinfo in data[g_id].items():
			event_time = datetime.datetime.strptime(eventinfo["eventdate"], "%d-%m-%Y %H:%M")
			if event_time.month == m_number:
				fields.append({
					"name": eventinfo["eventname"],
					"value": f"{eventinfo["eventdata"]}\nEvent will happen at: {eventinfo["eventdate"]}",
					"inline": False
					})
		embed = await embedMaker(
			title=f"Our event calendar for {m_name}",
			message=f"The calendar is subject to change. If a change is inflicted to the calendar you will be notified.",
			footer=("Made by ersin, with love <3", self.bot.user.display_avatar.url),
			fields=fields,
			isTimestamped=True
		)
		await interaction.response.send_message(embed=embed)
	@discord.app_commands.command(name="addevent", description="Add event to the bot so that people can see.")
	@has_roles_case_insensitive("it", "admin", "staff")
	@discord.app_commands.describe(
		eventdate = "Use strings, and format it as \"day-month-year hour:minutes\""
	)
	async def addevent(self, interaction : discord.Interaction, eventname : str, eventdata : str, eventdate : str, posterurl : str = None):

		try:
			eventdate = datetime.datetime.strptime(eventdate, "%d-%m-%Y %H:%M")
		except ValueError:
			await interaction.response.send_message(f"Wrong format! Use \"day-month-year hour:minutes\"!", ephemeral=True, delete_after=5)
			return

		try:
			with open(self.calendar_data, "r", encoding='utf-8') as f:
				data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			data = {}

		if eventdate <= datetime.datetime.now():
			await interaction.response.send_message(f"You can not set a event in a earlier date!",ephemeral=True, delete_after=5)
			return

		g_id = str(interaction.guild_id)
		posterurl = posterurl or None

		if not data.get(g_id):
			data[g_id] = {}

		event_id = len(data[g_id]) + 1

		data[g_id][event_id] = {
			"eventname": eventname,
			"eventdata": eventdata,
			"eventdate": eventdate.strftime("%d-%m-%Y %H:%M"),
			"eventposter": posterurl
		}

		await interaction.response.send_message(f"Success! The event \"{eventname}\" with event description \"{eventdata}\" is set to \"{eventdate}\"", ephemeral=True, delete_after=10)

		with open(self.calendar_data, "w", encoding='utf-8') as f:
			json.dump(data, f, indent=4)
		self.bot.loop.create_task(self.publish_event(guild_id=interaction.guild_id, eventinfo=data[g_id][event_id]))

	@discord.app_commands.command(name="deleteevent", description="Deletes the given event.")
	@has_roles_case_insensitive("it", "staff", "admin")
	async def deleteevent(self, interaction : discord.Interaction, eventname : str):
		try:
			with open(self.calendar_data, "r", encoding='utf-8') as f:
				data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			data = {}

		found = False
		match data:
			case d if str(interaction.guild_id) in d:
				for eventid, eventinfo in list(data[str(interaction.guild_id)].items()):
					if eventinfo["eventname"] == eventname:
						del data[str(interaction.guild_id)][eventid]
						found = True
						break
			case d if not interaction.guild_id in d:
				await interaction.response.send_message(f"...what?", ephemeral=True, delete_after=5)

		if found == True:
			await interaction.response.send_message(f"Event \"{eventname}\" is deleted successfully!", ephemeral=True, delete_after=7)
		else:
			await interaction.response.send_message(f"Event \"{eventname}\" is not found. Are you sure that you typed the name right? ", ephemeral=True, delete_after=7)

		with open(self.calendar_data, "w", encoding='utf-8') as f:
			json.dump(data, f, indent=4)

	@commands.Cog.listener()
	async def on_ready(self):
		try:
			with open(self.calendar_data, "r", encoding='utf-8') as f:
				data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
				data = {}

		now = datetime.datetime.now()
		for guild_id, events in data.items():
			for eventid, eventinfo in events.items():
				event_time = datetime.datetime.strptime(eventinfo["eventdate"], "%d-%m-%Y %H:%M")
				if event_time > now:
					self.bot.loop.create_task(self.publish_event(guild_id=guild_id, eventinfo=eventinfo))

	async def publish_event(self, guild_id, eventinfo):
		import asyncio

		event_time = datetime.datetime.strptime(eventinfo["eventdate"], "%d-%m-%Y %H:%M")
		delay = (event_time - datetime.datetime.now()).total_seconds()

		if delay > 0:
			await asyncio.sleep(delay)

		guild = self.bot.get_guild(int(guild_id))
		if not guild:
			print("guild broken")
			return

		channel = discord.utils.get(guild.text_channels, name="event-announcements")

		if not channel:
			print("channel broken")
			return
		image = eventinfo.get("posterurl") or None
		embed = await embedMaker(
			title=eventinfo["eventname"],
			message=eventinfo["eventdata"],
			image=image,
			isTimestamped=True,
			footer=(f"Made by ersin, with love <3", self.bot.user.display_avatar.url)
		)
		role = discord.utils.get(guild.roles, name="∘ Jammer ∘")
		await channel.send(f"Event Time! {role.mention}", embed=embed)
		try:
			with open(self.calendar_data, "r", encoding="utf-8") as f:
				data = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			data = {}

		g_id = str(guild_id)
		to_delete = None
		for eventid, e in data.get(g_id, {}).items():
			if (e["eventname"] == eventinfo["eventname"] and
			e["eventdate"] == eventinfo["eventdate"] and
			e["eventdata"] == eventinfo["eventdata"] and
			e.get("posterurl") == eventinfo.get("posterurl")):
				to_delete = eventid
		if to_delete:
			del data[g_id][to_delete]
			with open(self.calendar_data, "w", encoding='utf-8') as f:
				json.dump(data, f, indent=4)