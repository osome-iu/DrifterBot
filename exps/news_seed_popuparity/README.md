The code in this file is for news source popularity analysis, 
done with a paper revision.

Please follow the steps below to repeat the analysis.

1. `news_sources.csv`: the news_sources are from
    https://www.allsides.com/media-bias/media-bias-ratings. It has 64 news sources
    in total when we collecting the data in 10/2020.
1. `create_tbl.sql`: creates postgresql tables used for this analysis.
1. `sampled_twitter_accounts.csv`: a list of sampled twitter users, who are English
   speakers and unlikely bots. See details of the sampling process in the paper.
1. collecting tweets. We collect a sample tweets published from 07/28/2019 - 08/03/2019
   (inclusive) by tweet users defined in `sampled_twitter_accounts.csv`.
1. `parse_tweets.py`: computing url-based political valence for tweets collected
    from above step, and storing the info into db table `TWEET_FOR_REBUTTAL2_2019`.
1. Please use following SQL command to update table `SAMPLED_T_ACCOUNTS2`, which
   keeps the user valence score.
    ```
    INSERT INTO SAMPLED_T_ACCOUNTS2 (user_id, url_valence)
    SELECT tmp.user_id, tmp.mean_url_score
    FROM (
      SELECT user_id,
             AVG(url_score) AS mean_url_score
      FROM TWEET_FOR_REBUTTAL2_2019
      WHERE url_score is not null
      GROUP BY user_id
      ) tmp
    ;
    ```
1. `check_friendships.py`: for each twitter user with url-based valence score,
    checking the friendships between the user and news sources.
1. `news_source_popularity.sql`: computing the news source popularity from users aligned 
    with the news source leaning.
