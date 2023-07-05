#!/usr/bin/env python3
import discord
import os
import re
import asyncio
from datetime import datetime
import yaml

intents = discord.Intents.all()
client = discord.Client(intents=intents)
day_done = 0

def debug_print(message, guild):
  with open("wordle_server/debug.txt", "a+") as debug_file:
    now = datetime.strftime(datetime.now(), "%m:%d:%Y %H:%M:%S")
    try:
      debug_file.write(now + " " + guild.replace(" ", "_") + ": " + message + "\n")
    except UnicodeEncodeError as e:
      debug_print(e, "None")

class WordleUser:
  def __init__(self, info):
    self.user = info[0]
    self.wins = int(info[1])
    self.high_score = int(info[2])
    self.avg_score = float(info[3])
    self.all_scores = info[4]

  def print_user_stats(self):
    try:
      return self.user + " has a high score of " + str(self.high_score) + ", an average score of " + str(self.avg_score) + " and has won " + str(self.wins) + " times"
    except TypeError:
      return self.user + " has a high score of " + str(self.high_score) + ", an average score of " + str(self.avg_score) + " and has won " + str(self.wins) + " times"

  def add_new_score(self, new_score):
    self.all_scores.append(new_score)
    scores = 0
    tot_score = 0
    if(new_score < self.high_score):
      self.high_score = new_score
    for score in self.all_scores:
      tot_score += score
      scores += 1
    self.avg_score = tot_score/scores

  def return_user_list(self):
    return [self.user, self.wins, self.high_score, self.avg_score, self.all_scores]

async def send_user_stats(message, user_to_find):
  try:
    win_yaml = yaml.load(open("wordle_server/wordle_" + message.guild.name.replace(" ", "_"), 'r'))
    for user in win_yaml["users"]:
      if(user[0] == user_to_find):
        userStats = WordleUser(user)
        await message.channel.send(userStats.print_user_stats())
        debug_print("Sending wordle stats for " + userStats.user, message.guild.name)
        del(userStats)
        return
    await message.channel.send("No stats exist for this user! sorry!")
  except TypeError as e:
    debug_print("Error in finding user stats: " + e, message.guild.name)
    await message.channel.send("No stats exist for this user! sorry!")
  except FileNotFoundError as e:
    debug_print("Stats requested in non existent server", message.guild.name)
    await message.channel.send("Sorry, this server has no stats yet! Play some wordle first, then request stats :)")

@client.event
async def on_message(message):
  if(message.content.startswith("?stats")):
    if(len(message.content.split()) == 1):
      await send_user_stats(message, message.author.name)
    else:
      await send_user_stats(message, message.content.split()[1])

  if(message.content.startswith("Wordle ")):
    result = re.search("\d\/6", message.content)
    if(result):
      debug_print("Wordle score received from " + message.author.name, message.guild.name)
      current_user = None
      try:
        with open("wordle_server/wordle_" + message.guild.name.replace(" ", "_"), 'r+') as cur_win:
          win_yaml = yaml.load(cur_win)
        if not win_yaml:
          win_yaml = {'todays_high_score': '7', "current_winners": [], "old_winners": [], "users": [], "channel_id": message.channel.id, "guild_id": message.guild.id}
          debug_print("New server found, generating new server file for " + message.guild.name.replace(" ", "_"), message.guild.name)
      except FileNotFoundError:
        win_yaml = {'todays_high_score': '7', "current_winners": [], "old_winners": [], "users": [], "channel_id": message.channel.id, "guild_id": message.guild.id}
        debug_print("New server found, generating new server file for " + message.guild.name.replace(" ", "_"), message.guild.name)
      current_winners = []
      if(message.channel.id != win_yaml["channel_id"]):
        return
      for id in win_yaml["current_winners"]:
        tmp_msg = await message.channel.fetch_message(id)
        current_winners.append(tmp_msg)
      high_score = int(win_yaml["todays_high_score"])
      usr_index = 0
      for usr in win_yaml["users"]:
        usrr = WordleUser([usr[0], usr[1], usr[2], usr[3], usr[4]])
        if(usrr.user == message.author.name):
          current_user = usrr
          current_user.add_new_score(int(result.group(0)[0]))
          break
        usr_index += 1
        del(usrr)
      if(current_user is None):
        current_user = WordleUser([message.author.name, 0, int(result.group(0)[0]), int(result.group(0)[0]), [int(result.group(0)[0])]])
        win_yaml["users"].append(current_user.return_user_list())
        debug_print("Creating new wordle user " + current_user.user + " in server " + message.guild.name.replace(" ", "_"), message.guild.name)
      if(int(result.group(0)[0]) == high_score):
        for msg in current_winners:
          if msg.author == message.author:
            return
        await message.add_reaction("⭐")
        debug_print("Adding " + current_user.user + " to today's winners", message.guild.name)
        current_winners.append(message)
      elif(int(result.group(0)[0]) < high_score):
        for msg in current_winners:
          await msg.remove_reaction("⭐", client.user)
        current_winners.clear()
        high_score = int(result.group(0)[0])
        await message.add_reaction("⭐")
        current_winners.append(message)
        debug_print("New high score, adding " + current_user.user + " to today's winners", message.guild.name)
      new_users_ids = []
      for msg in current_winners:
        new_users_ids.append(msg.id)
      with open("wordle_server/wordle_" + message.guild.name.replace(" ", "_"), 'w') as cur_win:
        win_yaml["todays_high_score"] = high_score
        win_yaml["current_winners"] = new_users_ids
        win_yaml["users"][usr_index] = current_user.return_user_list()
        del(current_user)
        debug_print(str(win_yaml), message.guild.name)
        cur_win.write(yaml.dump(win_yaml))
  return

async def time_check():
  await client.wait_until_ready()
  global day_done
  while not client.is_closed():
    now = datetime.strftime(datetime.now(), '%H:%M')
    if(now == "00:01" and day_done == 0):
      debug_print("Calculating today's winners", "None")
      high_score = 7
      current_winners = []
      old_winners = []
      day_done = 1
      cur_guild = 0
      cur_yaml = {}
      for server_file in os.listdir("wordle_server"):
        if(not server_file.startswith("wordle_")):
          continue
        with open("wordle_server/" + server_file, 'r') as cur_file:
          cur_yaml = yaml.load(cur_file)
        old_win_yaml = cur_yaml["old_winners"]
        cur_win_yaml = cur_yaml["current_winners"]
        high_score = cur_yaml["todays_high_score"]
        cur_guild = cur_yaml["guild_id"]
        cur_channel = cur_yaml["channel_id"]
        for msg in old_win_yaml:
          tmp_id = client.get_guild(cur_guild).get_channel(cur_channel)
          to_append = await tmp_id.fetch_message(msg)
          old_winners.append(to_append)
        for msg in cur_win_yaml:
          tmp_id = client.get_guild(cur_guild).get_channel(cur_channel)
          to_append = await tmp_id.fetch_message(msg)
          current_winners.append(to_append)
        for msg in old_winners:
          await msg.guild.get_member_named(msg.author.name).remove_roles(discord.utils.get(msg.guild.roles, name="Wordle Winner!!"))
        old_winners.clear()
        for msg in current_winners:
          usr_index = 0
          for usr in cur_yaml["users"]:
            if(msg.author.name == usr[0]):
              cur_yaml["users"][usr_index][1] += 1
              break
          old_winners.append(msg.id)
          debug_print(msg.author.name + " added to today's winners", msg.guild.name)
          await msg.guild.get_member_named(msg.author.name).add_roles(discord.utils.get(msg.guild.roles, name="Wordle Winner!!"))
          await msg.remove_reaction("⭐", client.user)
          if(high_score == 1):
            try:
              await msg.channel.send(msg.author.nick + " is a wordle champion, and holy cow got it in 1 guess!!!")
            except TypeError:
              await msg.channel.send(msg.author.name + " is a wordle champion, and holy cow got it in 1 guess!!!")
          else:
            try:
              await msg.channel.send(msg.author.nick + " is a wordle champion for today, with a score of " + str(high_score) + "!")
            except TypeError:
              await msg.channel.send(msg.author.name + " is a wordle champion for today, with a score of " + str(high_score) + "!")
        current_winners.clear()
        high_score = 7
        cur_yaml["old_winners"] = old_winners
        cur_yaml["current_winners"] = current_winners
        cur_yaml["todays_high_score"] = high_score
        with open("wordle_server/" + server_file, 'w') as cur_file:
          debug_print(str(cur_yaml), server_file)
          cur_file.write(yaml.dump(cur_yaml))
    elif(now != "00:01" and day_done == 1):
      day_done = 0
    await asyncio.sleep(10)

client.loop.create_task(time_check())

client.run(os.getenv("TOKEN"))
