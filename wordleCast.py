import discord
import pickle
import json
import re

not_winner = 0
new_winner = 1
already_winner = 2


class wordleUser:
  """
  User object, conatins information about the guild member and wordle stats
  """
  def __init__(self, member):
    try:
      self.name = member.nick
    except TypeError:
      self.name = member.name
    if self.name is None:
      self.name = member.name
    self.id = member.id
    self.wins = 0
    self.high_score = 7
    self.avg_score = 0
    self.all_scores = []
    print(self.name)

  def return_user_stats(self):
    """
    Returns wordle stats in the form of [
    """
    if(self.all_scores == []):
      ret = []
    else:
      ret = [self.name, self.high_score, self.avg_score, self.wins]
    return ret

  def add_new_score(self, new_score: int):
    """
    Adds a new score to a user
    """
    self.all_scores.append(new_score)
    scores = 0
    tot_score = sum(self.all_scores)
    if(new_score < self.high_score):
      self.high_score = new_score
    scores = len(self.all_scores)
    self.avg_score = tot_score/scores
    return
    
  def pickle_user(self):
    return pickle.dumps(self)


class wordleGuild:
  """
  Guild Object, contains information about the current wordle users for the guild and today's high score and winners
  """
  def __init__(self, guild):
    self.current_winners = {}
    self.todays_high = 7
    self.users = {}
    self.id = guild.id
    self.cur_msgs = []
    
  def add_score(self, member, message):
    print("Adding score to member {}".format(member.id))
    if member.id not in self.users:
      print("new user!")
      member = make_new_user(member)
      self.users.update({member.id: member.pickle_user()})
    else:
      member = depickle_user(self.users[member.id])
    score = int(re.search("\d\/6", message.content).group(0)[0])
    member.add_new_score(score)
    self.users.update({member.id: member.pickle_user()})
    if score == self.todays_high:
      print("additional winner!")
      if member.id not in self.current_winners:
        self._add_winner(member, message)
    elif score < self.todays_high:
      print("new high score!")
      if member.id not in self.current_winners:
        self._new_high_score(member, message)
    return self.cur_msgs
      
  def add_user(self, member):
    print("member = {}".format(member.name))
    if member.id not in self.users:
      member = make_new_user(member)
      self.users.update({member.id: member.pickle_user()})
      return True
    else:
      return False
      
  def get_user(self, id):
    if id in self.users:
      return depickle_user(self.users[id])
    else:
      return None
      
  async def refresh(self):
    for winner in self.current_winners:
      winner.wins += 1
    self.current_winners = {}
    for msg in self.cur_msgs:
      msg = pickle.loads(msg)
      await msg.clear_reaction("👑")
    self.cur_msgs = []
    self.todays_high = 7
      
  def _new_high_score(self, member, message):
    score = int(re.search("\d\/6", message.content).group(0)[0])
    self.todays_high = score
    self.current_winners = {}
    self.current_winners.update({member.id: member.pickle_user()})
    self.cur_msgs = []
    self.cur_msgs.append(message.id)
    
  def _add_winner(self, member, message):
    self.current_winners.update({member.id: member.pickle_user()})
    self.cur_msgs.append(message.id)
    
  def check_high_score(self):
    return self.todays_high
  def guild_pickle(self):
    return pickle.dumps(self)
  def is_active_member(self, member):
    return member.id in self.users


def make_new_guild(guild):
  return wordleGuild(guild)
  
def make_new_user(member):
  return wordleUser(member)
  
def depickle_guild(guild):
  return pickle.loads(guild)
  
def depickle_user(user):
  return pickle.loads(user)
