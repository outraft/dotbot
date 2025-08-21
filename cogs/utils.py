import discord.ext
import discord
import datetime
from typing import List, Tuple, Optional, Union

async def embedMaker(
	title: str,
	message: str,
	footer: Optional[str] = None,
	color : Optional[discord.Color] = None,
	isTimestamped : Optional[bool] = None,
	image : Optional[str] = None,
	fields : Optional[List[Union[Tuple[str, str, bool], dict]]] = None
	) -> discord.Embed:

	"""
	Creates a Discord embed with title, message, optional footer, color, and fields.

	Params:
	title (str): As the name suggests, is the title.
	message (str): The main message, will appear on top of fields, but under title.
	footer (str | optional): Footer text, will appear on the bottom most place, as a footer.
	color (discord.Color | optional): Color of the embed. Default: discord.Color.blurple()
	isTimestamped (bool | optional): If the embed will be timestamped or not.
	image (str | optional): This is kinda quirky, needs a hyperlink (https://example.com/exampleimage.png) or a local file (attachment://localexample.png) to work
	fields (list | optional): Embed fields.
		Every field must be determined as a tuple {name (str), value (str), inline (bool)} or a dict {"name": name (str), "value": value (str), "inline": inline (bool) [default: true]}. Use tuple for safer approach as dict might get depricated.
	Usage:
	>>> await embedMaker(
	>>>		title = "Test"
	>>>		message = "this is a message"
	>>>		fields=[("Field1", "Value1", True)]
	>>> )
	"""

	embed = discord.Embed(title=title)
	embed.description = message
	if color:
		embed.color = color
	if footer:
		embed.footer = footer
	if isTimestamped:
		embed.timestamp = datetime.datetime.now()
	if image:
		embed.set_image(url=image)
	if fields:
		for field in fields:
			if isinstance(field, tuple):
				name, value, inline = field
				embed.add_field(field)
			elif isinstance(field, dict):
				embed.add_field(
					name=field.get("name", ""),
					value=field.get("value", ""),
					inline=field.get("inline", True)
				)
	return embed

def has_roles_case_insensitive(*role_names):
	def predicate(interaction: discord.Interaction):
		user_roles = [role.name.lower() for role in interaction.user.roles]
		if any(rn.lower() in r for r in user_roles for rn in role_names):
			return True
		raise discord.app_commands.CheckFailure("You do not have the required permissions!")
	return discord.app_commands.check(predicate=predicate)
