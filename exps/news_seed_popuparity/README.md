The current folder contains the scripts for the news source popularity analysis. 
The goal of the ananalysis is to find news seed accounts that are popular on Twitter among their political leaning groups.
We have two ways to measure the popularity of the news seed accounts: 1. the number of followers on Twitter; 2. Twitter users with congruent political leaning tend to follow these seeds.

Here are the steps to implement the first measure:

1. Collect the news sources from https://www.allsides.com/media-bias/media-bias-ratings together with their political leaning
1. Find their corresponding Twitter handles if exist
1. Compile a list of the news sources, their political leaning, Twitter handles, number of followers

Our list is available at `news_sources.csv`. It has 64 news sources in total.
The data collection was performed in Oct. 2020.

Here are the steps to implement the second measure:
    
1. Use `create_tbl.sql` to creates postgresql tables used for this analysis.
1. Sample a group of English-speaking Twitter accounts that are not bot-like. We share our list in `sampled_twitter_accounts.csv`. Details of the sampling process can be found in the paper.
1. Collect tweets published from 07/28/2019 - 08/03/2019 (inclusive) by tweet users defined in `sampled_twitter_accounts.csv` from Decahose.
1. Use `parse_tweets.py` to compute url-based political valence for the tweets collected; store the info into db table `TWEET_FOR_REBUTTAL2_2019`.
1. Use following SQL command to update table `SAMPLED_T_ACCOUNTS2`, which
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
1. Use `check_friendships.py` on each twitter user with url-based valence score to check their friendships with all the news sources.
1. Use `news_source_popularity.sql` to compute the news source popularity from users aligned with the news source leaning
