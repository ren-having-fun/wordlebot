from redis import Redis
import pickle
import json
import discord
import wordleCast 
from wordleCast import wordleGuild, wordleUser, make_new_guild, depickle_guild


class wordleServer:
  def __init__(self):
    self.redis_server = Redis(host='localhost', port=6379, decode_responses=False, username="pi", password="TheRealSlimShady")

  def is_guild(self, guild):
    return self.redis_server.get(guild.id) is not None

  def is_wordler(self, guild, member):
    our_guild = self.redis_server.get(guild.id)
    if our_guild is None:
      return False
    else:
      our_guild = depickle_guild(our_guild)
    return member.id in our_guild.users

  def make_new_wordle_guild(self, guild):
    new_guild = make_new_guild(guild)
    if new_guild is not None:
      self.redis_server.set(guild.id, new_guild.guild_pickle())
      return True
    else:
      return False

  def add_new_wordler(self, guild, member):
    print(guild.id)
    our_guild = self.redis_server.get(guild.id)
    ret = False
    if our_guild is None:
      our_guild = make_new_wordle_guild(guild)
    else:
      our_guild = depickle_guild(our_guild)
    ret = our_guild.add_user(member)
    if ret:
      self.redis_server.set(guild.id, our_guild.guild_pickle())
    return ret

  def get_wordler_stats(self, guild, member):
    our_guild = self.redis_server.get(guild.id)
    if our_guild is None:
      return []
    else:
      our_guild = depickle_guild(our_guild)
    our_user = our_guild.get_user(member.id)
    if our_user is not None:
      return our_user.return_user_stats()
    else:
      return []

  def get_highest_score(self, guild):
    return depickle_guild(self.redis_server.get(guild.id)).todays_high

  def add_score_to_guild(self, guild, member, message):
    our_guild = self.redis_server.get(guild.id)
    if our_guild is None:
      print("New score from new guild!")
      our_guild = make_new_guild(guild)
    else:
      our_guild = depickle_guild(our_guild)
      print("Adding score to guild {}".format(our_guild.id))
    winning_messages = our_guild.add_score(member, message)
    self.redis_server.set(our_guild.id, our_guild.guild_pickle())
    old_winners = self.redis_server.get(str(our_guild.id) + "_winners")
    if old_winners is not None:
      old_winners = json.loads(old_winners.decode())
    else:
      old_winners = []
    self.redis_server.set(str(our_guild.id) + "_winners", json.dumps(old_winners))
    print (old_winners, winning_messages)
    return (old_winners, winning_messages)
    
  async def calculate_winners(self):
    winners = {}
    for guild_id in self.redis_server.keys():
      our_guild = self.redis_server.get(guild_id)
      if our_guild is not None:
        our_guild = depickle_guild(our_guild)
      else:
        return {}
      winners.update({our_guild: [our_guild.users, our_guild.current_winners, self.todays_high]})
      await our_guild.refresh()
      self.redis_server.set(our_guild.id, our_guild.guild_pickle())
    return winners

  def __del__(self):
    self.redis_server.close()
