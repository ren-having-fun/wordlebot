#!/usr/bin/env python3
import os
import discord
from datetime import datetime
import re
import asyncio
import wordleServer
from wordleServer import wordleServer
import wordleCast
from discord.ext import commands, tasks
from discord.ext.commands import MemberConverter

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)
converter = MemberConverter()

@bot.event
async def on_ready():
  time_check.start()

@bot.event
async def on_disconnect():
  time_check.stop()

@bot.command(name='stats', description="Prints stats of user, leave blank to call for self")
async def stats(ctx, member=None):
  print("printing stats")
  if member == None:
    user = ctx.author
  else:
    try:
      user = await converter.convert(ctx, member)
    except MemberNotFound:
      await ctx.send("That user is not in this server! They should join and play some wordle ;)")
      return
  if(user):
    our_guild = ctx.guild
    if server.is_guild(our_guild):
      stats = server.get_wordler_stats(our_guild, user)
      print(stats)
      if stats == []:
        await ctx.send("This user has not played any wordle (or hasn't registered) yet!")
      else: 
        await ctx.send("{} has a high score of {}, an average score of {}, and has won {} times!".format(stats[0], stats[1], stats[2], stats[3]))
    else:
      await ctx.send("This discord server has not been added to my database yet!  Someone needs to ?register and/or play some wordle to start :)")
      
    
@bot.command()
async def register(ctx):
  user = ctx.author
  our_guild = ctx.guild
  ret = False
  if server.is_guild(our_guild):
    if server.is_wordler(our_guild, user):
      await ctx.send("You are already registered!")
    else:
      ret = server.add_new_wordler(our_guild, user)
  else:
    ret = server.make_new_wordle_guild(our_guild)
    if ret:
      print("Guild {} created".format(ctx.guild.name))
      ret = server.add_new_wordler(our_guild, user)
  if not ret:
    print("User registration failed")
    await ctx.send("Error occurred!")
  else: 
    print("User {} registered".format(ctx.author.name))
    await ctx.send("Thank you for registering!")
    
@bot.event
async def on_message(message):
  score = re.search("\d\/6", message.content)
  if score is not None:
    score = int(score.group(0)[0])
    print("Adding score: {} to user".format(score))
    (old_winners, new_winners) = server.add_score_to_guild(message.guild, message.author, message)
    for msg in old_winners:
      try:
        msg = await message.channel.fetch_message(msg)
        await msg.clear_reaction('👑')
      except (NotFound, Forbidden, HTTPException):
        continue
    for msg in new_winners:
      try:
        msg = await message.channel.fetch_message(msg)
        await msg.add_reaction('👑')
      except (NotFound, Forbidden, HTTPException):
        continue
  else:
    await bot.process_commands(message)

@tasks.loop(seconds=10)
async def time_check():
  now = datetime.strftime(datetime.now(), '%H:%M')
  print(now)

server = wordleServer()
bot.run(os.getenv("TOKEN"))
