from discord.ext import commands
import discord
import asyncio
import json
import git
import os

class Admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def is_mod(ctx):
		return ctx.author.guild_permissions.manage_channels

	@commands.command(aliases=['quit'], hidden=True)
	@commands.check(is_mod)
	async def forceexit(self, ctx, password):
		if password == "abort":
			await ctx.message.delete()
			exit()

	@commands.command()
	@commands.check(is_mod)
	async def pull(self, ctx):
		"""Update the bot from github"""
		g = git.cmd.Git(os.getcwd())
		try:
			await ctx.send(f"Probably pulled.\n```bash\n{g.pull()}```")
		except git.exc.GitCommandError as e:
			await ctx.send(f"An error has occured when pulling```bash\n{e}```")

	@commands.command(aliases=['addcommand', 'newcommand'])
	@commands.check(is_mod)
	async def setcommand(self, ctx, command, *, message):
		self.bot.custom_commands[ctx.prefix + command] = message
		with open('custom_commands.json', 'w') as f:
			json.dump(self.bot.custom_commands, f, indent=4)

		await ctx.send(f"Set message for command {command}")

	@commands.command(aliases=['deletecommand'])
	@commands.check(is_mod)
	async def removecommand(self, ctx, command):
		del self.bot.custom_commands[ctx.prefix + command]
		with open('custom_commands.json', 'w') as f:
			json.dump(self.bot.custom_commands, f, indent=4)

		await ctx.send(f"Removed command {command}")

	@commands.check(is_mod)
	@commands.command(name='reload', hidden=True, usage='<extension>')
	async def _reload(self, ctx, ext):
		"""Reloads an extension"""
		try:
			self.bot.reload_extension(f'cogs.{ext}')
			await ctx.send(f'The extension {ext} was reloaded!')
		except commands.ExtensionNotFound:
			await ctx.send(f'The extension {ext} doesn\'t exist.')
		except commands.ExtensionNotLoaded:
			await ctx.send(f'The extension {ext} is not loaded! (use {ctx.prefix}load)')
		except commands.NoEntryPointError:
			await ctx.send(f'The extension {ext} doesn\'t have an entry point (try adding the setup function) ')
		except commands.ExtensionFailed:
			await ctx.send(f'Some unknown error happened while trying to reload extension {ext} (check logs)')
			self.bot.logger.exception(f'Failed to reload extension {ext}:')

	@commands.check(is_mod)
	@commands.command(name='load', hidden=True, usage='<extension>')
	async def _load(self, ctx, ext):
		"""Loads an extension"""
		try:
			self.bot.load_extension(f'cogs.{ext}')
			await ctx.send(f'The extension {ext} was loaded!')
		except commands.ExtensionNotFound:
			await ctx.send(f'The extension {ext} doesn\'t exist!')
		except commands.ExtensionAlreadyLoaded:
			await ctx.send(f'The extension {ext} is already loaded.')
		except commands.NoEntryPointError:
			await ctx.send(f'The extension {ext} doesn\'t have an entry point (try adding the setup function)')
		except commands.ExtensionFailed:
			await ctx.send(f'Some unknown error happened while trying to reload extension {ext} (check logs)')
			self.bot.logger.exception(f'Failed to reload extension {ext}:')

	@commands.check(is_mod)
	@commands.command(name='unload', hidden=True, usage='<extension>')
	async def _unload(self, ctx, ext):
		"""Loads an extension"""
		try:
			self.bot.unload_extension(f'cogs.{ext}')
			await ctx.send(f'The extension {ext} was unloaded!')
		except commands.ExtensionNotFound:
			await ctx.send(f'The extension {ext} doesn\'t exist!')
		except commands.NoEntryPointError:
			await ctx.send(f'The extension {ext} doesn\'t have an entry point (try adding the setup function)')
		except commands.ExtensionFailed:
			await ctx.send(f'Some unknown error happened while trying to reload extension {ext} (check logs)')
			self.bot.logger.exception(f'Failed to unload extension {ext}:')

	@commands.command()
	@commands.check(is_mod)
	async def clear(self, ctx, number):
		await ctx.message.channel.purge(limit=int(number) + 1, bulk=True)

	@commands.check(is_mod)
	@commands.command()
	async def mute(self, ctx, members: commands.Greedy[discord.Member] = False,
				   mute_minutes: int = 0,
				   *, reason: str = "absolutely no reason"):
		if not members:
			await ctx.send("You need to name someone to mute")
			return
		elif type(members) == str:
			members = self.bot.get_user(int(members))

		# muted_role = discord.utils.find(ctx.guild.roles, name="Muted")
		muted_role = ctx.guild.get_role(int(self.bot.config[str(ctx.guild.id)]["mute_role"]))
		for member in members:
			if self.bot.user == member:  # what good is a muted bot?
				embed = discord.Embed(title="You can't mute me, I'm an almighty bot")
				await ctx.send(embed=embed)
				continue
			await member.add_roles(muted_role, reason=reason)
			await ctx.send(f"{member} has been muted by {ctx.author} for *{reason}*")

		if mute_minutes > 0:
			await asyncio.sleep(mute_minutes * 60)
			for member in members:
				await member.remove_roles(muted_role, reason="time's up ")

	@commands.check(is_mod)
	@commands.command()
	async def unmute(self, ctx, members: commands.Greedy[discord.Member]):
		if not members:
			await ctx.send("You need to name someone to unmute")
			return
		elif type(members) == str:
			members = self.bot.get_user(int(members))

		muted_role = ctx.guild.get_role(int(self.bot.config[str(ctx.guild.id)]["mute_role"]))
		for i in members:
			await i.remove_roles(muted_role)
			await ctx.send(f"{i} has been unmuted by {ctx.author}")

	@commands.command(aliases=['ban'], hidden=True)
	@commands.check(is_mod)
	async def blacklist(self, ctx, members: commands.Greedy[discord.Member] = None):
		if not members:
			await ctx.send("You need to name someone to blacklist")
			return
		elif type(members) == "str":
			members = self.bot.get_user(int(user))

		with open('config.json', 'w') as f:
			for i in members:
				if i.id in self.bot.config['blacklist']:
					self.bot.config['blacklist'].remove(i.id)
					json.dump(self.bot.config, f, indent=4)
					await ctx.send(f"{i} has been un-blacklisted.")
				else:
					self.bot.config['blacklist'].append(i.id)
					json.dump(self.bot.config, f, indent=4)
					await ctx.send(f"{i} has been blacklisted.")

	@commands.check(is_mod)
	@commands.command()
	async def activity(self, ctx, *, activity=None):
		if activity:
			game = discord.Game(activity)
		else:
			activity = "Mining away"
			game = discord.Game(activity)
		await self.bot.change_presence(activity=game)
		await ctx.send(f"Activity changed to {activity}")

	@commands.check(is_mod)
	@commands.command(hidden=True)
	async def setvar(self, ctx, key, *, value):
		with open('config.json', 'w') as f:
			self.bot.config[str(ctx.message.guild.id)][key] = value
			json.dump(self.bot.config, f, indent=4)

	@commands.check(is_mod)
	@commands.command(hidden=True)
	async def setversion(self, ctx, *, value):
		with open('config.json', 'w') as f:
			self.bot.config['version'] = value
			json.dump(self.bot.config, f, indent=4)

	@commands.check(is_mod)
	@commands.command(hidden=True)
	async def delvar(self, ctx, key):
		with open('config.json', 'w') as f:
			del self.bot.config[str(ctx.message.guild.id)][key]
			json.dump(self.bot.config, f, indent=4)

	@commands.check(is_mod)
	@commands.command(hidden=True)
	async def printvar(self, ctx, key):
		await ctx.send(self.bot.config[str(ctx.message.guild.id)][key])

	@commands.command()
	@commands.check(is_mod)
	async def logs(self, ctx, *, password):
		if password == "beep boop":
			await ctx.message.delete()
			file = discord.File("discord.log")
			await ctx.send(file=file)

	@commands.command()
	@commands.check(is_mod)
	async def addemote(self, ctx, name=None, *, reason='No reason provided'):
		emote_pic = None
		for attachement in ctx.message.attachments:
			emote_pic = await attachement.read()
		if not emote_pic:
			ctx.send('You need to add an image as attachment to this message')
			return
		if not name:
			ctx.send('You need a name for this emote')
			return
		if len(name) < 2:
			ctx.send('The name of this emote needs a length of 2 or more characters')
			return
		added_emote = await ctx.guild.create_custom_emoji(name=name, image=emote_pic, reason=reason)
		await ctx.send(f'Added the emote {str(added_emote)} `:{name}:` to this server!')

	@commands.command(aliases=['slow'])
	@commands.check(is_mod)
	async def slowmode(self, ctx, time_seconds):
		if ctx.channel.type == discord.ChannelType.text:
			try:
				await ctx.channel.edit(slowmode_delay=int(time_seconds))
				await ctx.message.add_reaction('👍')
			except ValueError:
				ctx.send(f'{ctx.author.mention}, the delay needs to be a number!')


def setup(bot):
	bot.add_cog(Admin(bot))
