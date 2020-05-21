"""Gets expanded urls of Tweets, resolves short urls and save them to db."""
import requests
from metric import db_for_analysis

def resolved_url(url):
  try:
    final_url = requests.head(url, allow_redirects=True, timeout=10)
    if final_url:
      return final_url.url
  except Exception as e:
      return None

def get_expanded_url():
  rst = db_for_analysis.getURLsPerTweet()  # list of (tweet_id, url_array)
  if not rst:
    return
  for tweet_id, url_arr in rst:
    final_urls = set()
    for url in url_arr:
      tmp_url = resolved_url(url)
      if not tmp_url:
        final_urls.add(url)
      else:
        final_urls.add(tmp_url)
    
    db_for_analysis.saveURLStoTweetTbl(tweet_id, list(final_urls))
