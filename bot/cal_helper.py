"""Some helper functions."""
import json
import numpy as np
import random
import vocabulary as tweet_vocal


def RandomizeAnTweetFromFile():
  """Used in PostTweet. Randomize a sentence from a list."""
  tweet_lst = tweet_vocal.tweet_lst
  samples = 1
  if random.random() > 0.5:
    samples = 2
  sentence = ''
  for i in range(samples):
    sentence += np.random.choice(tweet_lst, 1)[0]
  return sentence


# key_dict = {entities:{user_mentions:[id]}, user:id}
# same_level_obj = [retweeted_status]
def RetriveUserIds(json_obj):
  """Get all user ids in a list of Tweet objects."""
  rst_set = set()

  def _helper(current_obj):
    if 'entities' in current_obj:
      if 'user_mentions' in current_obj['entities']:
        if current_obj['entities']['user_mentions']:
          for user_obj in current_obj['entities']['user_mentions']:
            rst_set.add(user_obj['id'])

    if 'user' in current_obj:
      rst_set.add(current_obj['user']['id'])

    if 'retweeted_status' in current_obj:
      _helper(current_obj['retweeted_status'])

  for tweet_obj in json_obj:
    _helper(tweet_obj)

  return list(rst_set)


def randomizeSource(prob_dict):
  """ Weighted randomized an item in prob_dict according to their weight.

  Args:
    prob_dict: item (str) -> probability (float)

  Returns:
    item (str)
  """
  keys = list(prob_dict)
  probs = [prob_dict[k] for k in keys]
  draw = np.random.choice(keys, 1, p=probs)[0]
  return draw


def randomizeObjs(
  obj_list, num_returns=1, return_key=None,
  whether_weighted=False, weighted_key=None,
  weighted_order=False):
  """ Randomize objects from a list of objects.

  All objects should have same structure.
  Args:
    obj_list: a list of objects.
    return_key: if it's none, the function returns the selected object.
                Otherwise, return the value of the return_key in this selected
                object. We don't support nested keys
    whether_weighted: if it's False, the function would randomize one uniformly.
                      Else, the function will take weighted_key as the key to
                      randomize one item. To enable the weighted randomization,
                      weighted_key or weighted_order must be defined.
    weighted_key: A key in object. We don't support nested keys, and the values
                  associating with the key must be numbers.
    weighted_order: weighted probability based on the order(index) of the objects
                    in this list. The smaller index (such 0, 1) has a higher
                    probability

  Returns:
    An object or an attribute in object

  """
  if not obj_list:
    return None
  if not whether_weighted:
    selected_obj = np.random.choice(obj_list, num_returns)
  else:
    if weighted_key:
      weight_lst = [float(o[weighted_key]) for o in obj_lst]
    elif weighted_order:
      lst_len = len(obj_list)
      weight_lst = [lst_len - idx for idx in range(lst_len)]
    total_weight = sum(weight_lst)
    weight_lst = [w/total_weight for w in weight_lst]
    selected_obj = np.random.choice(obj_list, num_returns, weight_lst)

  if num_returns == 1:
    if return_key:
      selected_obj = selected_obj[0][return_key]
    else:
      selected_obj = selected_obj[0]
  else:
    if return_key:
      tmp_obj = []
      for obj in selected_obj:
        tmp_obj.append(obj[return_key])
      selected_obj = tmp_obj
  return selected_obj
