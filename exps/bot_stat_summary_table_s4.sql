-- Two helper tables used in this sql

--1. a table hashtag_score to store all hashtag scores defined in https://raw.githubusercontent.com/IUNetSci/DrifterBot/master/data/all_hashtag_political_alignment.csv
--2. a table url_2018 to store all url scores defined in https://github.com/IUNetSci/DrifterBot/blob/master/data/url_bias_score.csv

-- bool (0 is friend, 1 is follower)

create or replace function getBotID (screen_name text)
returns integer as
$$
declare 
  bot_id integer;
begin
case screen_name
  when 'TachikomasC' then bot_id=13;
  when 'auto_bender' then bot_id=7;
  when 'voidman2009' then bot_id=8;
  when 'weak_ultron' then bot_id=9;
  when 'rd2d_remaker' then bot_id=1;
  when 'frankenstein_tw' then bot_id=2;
  when 'trooper_tester' then bot_id=3;
  when 'tik_tok_2019' then bot_id=4;
  when 'halin2019' then bot_id=5;
  when 'metal_talos' then bot_id=6;
  when 'TheMoonMike' then bot_id=10;
  when 'GalateaVV' then bot_id=11;
  when 'TWTbackrub' then bot_id=12;
  when 'ParanoidMarvin4' then bot_id=14;
  else bot_id=15;
end case;
return bot_id;
end;
$$ language plpgsql;



-- number of political hashtags (allow duplication) : 1190
-- all hahstags:
-- all urls:3868
With sub_bot AS 
  (select getBotID(screen_name) as bot_id_inpaper,
          twitter_user_id from bot),
detected_hashtags as (
  select LOWER(
    json_array_elements(tweet_obj -> 'entities' -> 'hashtags')->>'text')
  as hashtag
  from tweet right join sub_bot on sub_bot.twitter_user_id = user_id
  where created_at < '2019-11-15'
)
select count(detected_hashtags.hashtag) from detected_hashtags
where detected_hashtags.hashtag in 
  (select hashtag from hashtag_score)
;

With sub_bot AS 
  (select getBotID(screen_name) as bot_id_inpaper,
          twitter_user_id from bot)
select sub_bot.bot_id_inpaper as bot_id,
       count(hashtag_score) as num_tweets_hashtags,
       count(url_score) as num_tweets_urls
from tweet right join sub_bot on sub_bot.twitter_user_id = user_id
where created_at < '2019-11-15'
group by sub_bot.bot_id_inpaper
order by sub_bot.bot_id_inpaper;



-- all urls (exclusive twitter)
With sub_bot AS 
  (select getBotID(screen_name) as bot_id_inpaper,
          twitter_user_id from bot),
detected_urls as (
  select 
    json_array_elements(tweet_obj -> 'entities' -> 'urls')->>'expanded_url'
    as url
  from tweet right join sub_bot on sub_bot.twitter_user_id = user_id
  where created_at < '2019-11-15'
)
select count(detected_urls.url) from detected_urls
where detected_urls.url NOT LIKE 'https://twitter.com%';



-- political related urls
With sub_bot AS 
  (select getBotID(screen_name) as bot_id_inpaper,
          twitter_user_id from bot),
detected_urls as (
  select split_part(
    LOWER(REPLACE(REPLACE(UNNEST(resolved_urls), 'https://', ''), 'http://', '')),
    '/', 1)
  as url
  from tweet right join sub_bot on sub_bot.twitter_user_id = user_id
  where created_at < '2019-11-15'
)
select count(*) from detected_urls 
where detected_urls.url NOT LIKE 'twitter.com%'
and detected_urls.url in (select url from url_2018)
;
ALTER TABLE tweet 
RENAME COLUMN url_score_2018 TO url_score;

UPDATE tweet SET url_score_2018 = null WHERE url_score_2018 = -10000;

-- number of followers
select sub_bot.bot_id, time::TIMESTAMP::DATE, count(t_usr_id_conn) from connections
right join (select getBotID(screen_name) as bot_id, twitter_user_id from bot) as sub_bot
on sub_bot.twitter_user_id = t_usr_id_ego
and conn_type = true
where time::TIMESTAMP::DATE < '2019-11-15' and no_connctions is false
group by time::TIMESTAMP::DATE,sub_bot.bot_id
order by time::TIMESTAMP::DATE desc;

-- number of actions
select sub_bot.bot_id_inpaper, count(action) from action
right join (select getBotID(screen_name) as bot_id_inpaper, bot_id from bot) as sub_bot
on sub_bot.bot_id = action.bot_id
where timestamp::TIMESTAMP::DATE < '2019-11-15'
group by sub_bot.bot_id_inpaper
order by sub_bot.bot_id_inpaper;

select count(action) as tweet_count from action
right join (
  select getBotID(screen_name) as bot_id_inpaper,
         bot_id from bot)
as sub_bot
on sub_bot.bot_id = action.bot_id
where
timestamp::TIMESTAMP::DATE < '2019-11-15';
and result::text like '%%restore result object failed via using Twitter API%%';

-- number of hashtags
With sub_bot AS 
  (select getBotID(screen_name) as bot_id_inpaper,
          twitter_user_id from bot)
select sub_bot.bot_id_inpaper,
       sum(json_array_length(tweet_obj -> 'entities' -> 'hashtags')) as hashtag_count
from tweet
right join sub_bot on sub_bot.twitter_user_id = user_id
where created_at < '2019-11-15'
group by sub_bot.bot_id_inpaper
order by sub_bot.bot_id_inpaper;

-- number of urls
With sub_bot AS 
  (select getBotID(screen_name) as bot_id_inpaper,
          twitter_user_id from bot)
select sub_bot.bot_id_inpaper,
       sum(json_array_length(tweet_obj -> 'entities' -> 'urls')) as url_count
from tweet
right join sub_bot on sub_bot.twitter_user_id = user_id
where created_at < '2019-11-15'
group by sub_bot.bot_id_inpaper
order by sub_bot.bot_id_inpaper;

--

-- The following are post-process python code
/*
data = [
    ('Left',1,159,53,509,351,1218,169,275,3413),
    ('Left',2,230,118,499,342,1179,326,317,3357),
    ('Left',3,237,124,475,341,1177,339,281,3360),
    ('C. Left', 4, 137,24,540,345,1258,213,300,3507),
    ('C. Left', 5,269,150,492,345,1142,180,251,3237),
    ('C. Left', 6,184,73,511,339,1233,143,257,3494),
    ('Center', 7,151,38,502,312,1117,171,232,3192),
    ('Center', 8,152,38,472,355,1236,182,261,3446),
    ('Center', 9,148,34,565,343,1195,158,265,3581),
    ('C. Right', 10,200,87,489,336,1205,171,273,3385),
    ('C. Right', 11,291,177,461,318,1151,150,240,3254),
    ('C. Right', 12,271,164,491,302,1108,154,233,3159),
    ('Right', 13,332,225,453,325,1051,203,210,3104),
    ('Right',14,322,211,468,348,1072,178,224,3107),
    ('Right',15,255,145,542,360,1256,179,249,3586)       
]

def get_mean_std(data):
    groups = ['Left','C. Left','Center','C. Right','Right']
    metrics = ['friends','followers','original_tweets', 'retweets',
               'likes', 'hashtags','links', 'actions']
    df = pd.DataFrame(data,
                      columns=['group', 'bot','friends',
                               'followers','original_tweets', 'retweets',
                               'likes', 'hashtags','links', 'actions'])
    stat_row = {'group':'all', 'bot': 'all'}
    for metric in metrics:
        avg_metric = np.mean(df[metric])
        std_metric = np.std(df[metric])
        stat_row[metric] = '{} ({})'.format(round(avg_metric,1), round(std_metric, 1))
    df = df.append(stat_row, ignore_index=True)
    for group in groups:
        tmp_df = df[df['group'] == group]
        group_stat_row = {'group': group, 'bot': 'all'}
        for metric in metrics:
            avg_metric = np.mean(tmp_df[metric])
            std_metric = np.std(tmp_df[metric])
            group_stat_row[metric] = '{} ({})'.format(round(avg_metric,1), round(std_metric, 1))
        df = df.append(group_stat_row, ignore_index=True)
    df = df.set_index(['group', 'bot'])
    df = df.sort_index()
    return df
    
get_mean_std(data)
*/
