import pandas as pd
import psycopg2
from psycopg2.extensions import AsIs
import tweepy
from tweepy.error import TweepError, RateLimitError
import sys
import hashlib
import networkx as nx
import numpy as np

forbid_account = [1184708720300888070, 1060030411756187650, 3040779334]

customer_API_key = 'sth'
customer_API_secret_key = 'sth'

access_token = 'sth'
access_token_secret = 'sth'
twitter_app_auth = {
  'consumer_key': customer_API_key,
  'consumer_secret': customer_API_secret_key,
  'access_token': access_token,
  'access_token_secret': access_token_secret
}

auth = tweepy.OAuthHandler(
      twitter_app_auth['consumer_key'],
      twitter_app_auth['consumer_secret'])
auth.set_access_token(
      twitter_app_auth['access_token'],
      twitter_app_auth['access_token_secret'])

BOT_SEED_MAP = {
  'bot7':'USATODAY', 
  'bot8':'USATODAY',
  'bot9':'USATODAY', 
  'bot1':'thenation', 
  'bot2':'thenation',
  'bot3':'thenation', 
  'bot4':'washingtonpost', 
  'bot5':'washingtonpost',
  'bot6':'washingtonpost', 
  'bot10':'WSJ', 
  'bot11':'WSJ',
  'bot12':'WSJ', 
  'bot13':'BreitbartNews', 
  'bot14':'BreitbartNews',
  'bot15':'BreitbartNews'
}

bot_dict = {
    # bot_screen_name : bot twitter user id
}

comm = """
with tmp1 as (
select distinct t_usr_id_conn from connections
where t_usr_id_ego = '{}' -- bot twitter id
     and no_connctions=false
     and time > TIMESTAMP '2019-11-29' and time < TIMESTAMP '2019-11-30'
     and random() < 0.4 limit 100
),
tmp2 as(
select distinct t_usr_id_conn, t_usr_id_ego, no_connctions, time from connections
where t_usr_id_ego in (select t_usr_id_conn from tmp1)
     and t_usr_id_conn in (select t_usr_id_conn from tmp1))
select distinct t1.t_usr_id_conn, t2.t_usr_id_ego, t2.no_connctions, t2.time from tmp1 t1 full outer join tmp2 t2 on t1.t_usr_id_conn = t2.t_usr_id_conn;
"""

def DBExecute(
  conn, command, method,
  param_lst=None, need_commit=False,
  return_id=False):
  """operate psql."""
  result = True
  try:
    if not conn:
      return False
    cur = conn.cursor()
    if param_lst:
      cur.execute(command, param_lst)
    else:
      cur.execute(command)
    if not need_commit:
      if return_id:
        result = cur.fetchone()[0]
      else:
        result = cur.fetchall()
    else:
      if return_id:
        result = cur.fetchone()[0]
      conn.commit()
  except (Exception, psycopg2.DatabaseError) as error:
    result = False
    conn.rollback()
    print(error)
  finally:
    if cur:
      cur.close()
  return result


def pull_db_data():
  db_conn = psycopg2.connect('dbname=drifter')
  for bot_name, bot_id in bot_dict.items():
    rst = DBExecute(
            db_conn, comm.format(bot_id), "get conns from db",
            need_commit=False, return_id=False)
    if rst:
      # df = pd.DataFrame(rst, columns=['twitter_id_1, twitter_id_2, no_connctions, time'])
      df  = pd.DataFrame(rst)
      df.columns = ['twitter_id_1', 'twitter_id_2', 'no_connections', 'time']
      print(df)
      df = df.sort_values('time').drop_duplicates(['twitter_id_1', 'twitter_id_2'], keep='last')
      df = df[['twitter_id_1', 'twitter_id_2', 'no_connections']]
      # friend_ids = list(set(df['twitter_id_1'].values.tolist() + df['twitter_id_2'].values.tolist()))
      df.to_csv(bot_name + '@%s' % bot_id + '.conn', index=False)
    else:
      print('fatal! %s has no result' % bot_name)

  if db_conn:
    db_conn.close()


def check_friends():
  tweepy_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
  for bot_name, bot_id in bot_dict.items():
    print(bot_name)
    df = pd.read_csv(bot_name + '@%s' % bot_id + '.conn')
    friend_ids = list(set(df['twitter_id_1'].values.tolist()))
    df = df.dropna(subset=['twitter_id_2'])
    friend_lst = df[['twitter_id_1', 'twitter_id_2']].dropna().values.tolist()
    new_friend_lst = []
    f1_idx = 0
    for f1_idx in range(len(friend_ids)):
      f1 = friend_ids[f1_idx]
      print(f1_idx)
      sys.stdout.flush()
      if f1 in forbid_account:
        continue
      for f2_idx in range(f1_idx + 1, len(friend_ids)):
        f2 = friend_ids[f2_idx]
        if f2 in forbid_account:
          continue
        if f1 == f2:
          continue
        if ([f1, f2] in friend_lst) or ([f2, f1] in friend_lst):
          # print('previous stored')
          continue
        try:
          rst = tweepy_api.show_friendship(source_id=f1, target_id=f2)
        except TweepError as e:
          print('%s, %s missed' % (f1, f2))
          print(e)
          sys.stdout.flush()
          continue
        follow_state = rst[0].following
        followed_state = rst[0].followed_by
        if not (follow_state or followed_state):
          new_friend_lst.append((f1, f2, True))
        else:
          new_friend_lst.append((f1, f2, False))
        if len(new_friend_lst) >= 50:
          with open(bot_name + '@%s' % bot_id + '.conn', 'a+') as fd:
            for f_tuple in new_friend_lst:
              fd.write('%s,%s,%s\n' % (f_tuple[0], f_tuple[1],f_tuple[2]))
          new_friend_lst = []
    if new_friend_lst:
      with open(bot_name + '@%s' % bot_id + '.conn', 'a+') as fd:
        for f_tuple in new_friend_lst:
          fd.write('%s,%s,%s\n' % (f_tuple[0], f_tuple[1],f_tuple[2]))
      new_friend_lst = []


def make_hash(row):
    return pd.Series(
            [str(int(hashlib.sha1(row['twitter_id_1']).hexdigest(), 16) % (10 ** 8)),
             str(int(hashlib.sha1(row['twitter_id_2']).hexdigest(), 16) % (10 ** 8)),
             row['no_connections']], index=['twitter_id_1', 'twitter_id_2', 'no_connections'])

def save_graph(filename, include_bot=False):
  result = []
  for bot_name, bot_id in bot_dict.items():
    df = pd.read_csv('{}@{}.conn'.format(bot_name, bot_id),
                     dtype='str')
    print(bot_name)
    df = df.dropna(subset=['twitter_id_2'])
    df = df.apply(make_hash, axis=1)
    all_ids = list(set(df['twitter_id_1'].values.tolist() + df['twitter_id_2'].values.tolist()))
    final_df = df[df.no_connections == 'False']
    edges = final_df[['twitter_id_1', 'twitter_id_2']].values.tolist()
    if include_bot:
      edges += [['bot', t] for t in all_ids]
      all_ids + ['bot']
    G = nx.Graph()
    G.add_edges_from(edges)
    G.add_nodes_from(all_ids)
    nx.write_gexf(G, "result/{}_{}.gexf".format(bot_name, filename))


def compute_metrics(dir_path, output_filename, cc_func,number_randoms=100, include_bot=False):
  result = []
  for bot_name, bot_id in bot_dict.items():
    G = nx.read_gexf("{}{}_graph_without_bot.gexf".format(dir_path, bot_name))
    if include_bot:
      G.add_node('bot')
      for node in G.nodes():
        if node == 'bot':
            continue
        G.add_edge('bot', node)
    metric_g = cc_func(G)
    density_g = nx.density(G)
    number_nodes = len(G.nodes)
    number_edges = len(G.edges)
    random_rst = []
    for _ in range(number_randoms):
      random_G = nx.gnm_random_graph(number_nodes, number_edges)
      random_rst.append(cc_func(random_G))

    random_metric = np.mean(random_rst)
    result.append((
      bot_name, BOT_SEED_MAP[bot_name],
      number_nodes, number_edges,density_g,
      metric_g, random_metric, metric_g / random_metric))
  result_df = pd.DataFrame(result)
  result_df.columns = ['bot', 'seed', 'num_nodes', 'num_edges','density', 'metric', 'random_metric', 'ratio']
  result_df.to_csv(output_filename+'.csv', index=False)
  return result_df

#pull_db_data()
#check_friends()
#result_df = save_graph(
#  'graph_without_bot',
#  include_bot=False)

#result_df = compute_metrics('.', 'transitivity_has_bot', cc_func=nx.transitivity, number_randoms=100, include_bot=True)
