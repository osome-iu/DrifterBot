-- The sql creates tables used for the analysis in this folder.
CREATE TABLE news_source (
     site_name varchar(50),
     url varchar(50),
     twitter_handle  PRIMARY KEY,
     follower_number integer,
     leaning varchar(10),
     sort integer
     twitter_id varchar(50)
);

CREATE TABLE SAMPLED_T_ACCOUNTS2 (
  user_id varchar(50) PRIMARY KEY,
  url_valence float
);

-- hold tweets in one week published by users in SAMPLED_T_ACCOUNTS
CREATE TABLE TWEET_FOR_REBUTTAL2_2019 (
     tweet_id varchar(50) PRIMARY KEY,
     user_id varchar(50) NOT NULL,
     tweet_obj JSON NOT NULL,
     created_at timestamp NOT NULL,
     url_score numeric,
     hashtag_score numeric,
     resolved_urls TEXT []
);

CREATE TABLE CONN_REB22 (
  twitter_user_id varchar(50),
  new_source_twitter_id varchar(50)
);
