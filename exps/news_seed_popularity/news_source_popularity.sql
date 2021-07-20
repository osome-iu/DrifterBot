-- summarize the #users in each political buckets
select count(distinct SAMPLED_T_ACCOUNTS2.user_id) from SAMPLED_T_ACCOUNTS2
right join CONN_REB22 on CONN_REB22.twitter_user_id = SAMPLED_T_ACCOUNTS2.user_id
where SAMPLED_T_ACCOUNTS2.url_valence >= 0.5;

select count(distinct SAMPLED_T_ACCOUNTS2.user_id) from SAMPLED_T_ACCOUNTS2
right join CONN_REB22 on CONN_REB22.twitter_user_id = SAMPLED_T_ACCOUNTS2.user_id
where SAMPLED_T_ACCOUNTS2.url_valence >= 0.1 and SAMPLED_T_ACCOUNTS2.url_valence < 0.5;

select count(distinct SAMPLED_T_ACCOUNTS2.user_id) from SAMPLED_T_ACCOUNTS2
right join CONN_REB22 on CONN_REB22.twitter_user_id = SAMPLED_T_ACCOUNTS2.user_id
where SAMPLED_T_ACCOUNTS2.url_valence >= -0.1 and SAMPLED_T_ACCOUNTS2.url_valence < 0.1;

select count(distinct SAMPLED_T_ACCOUNTS2.user_id) from SAMPLED_T_ACCOUNTS2
right join CONN_REB22 on CONN_REB22.twitter_user_id = SAMPLED_T_ACCOUNTS2.user_id
where SAMPLED_T_ACCOUNTS2.url_valence >= -0.5 and SAMPLED_T_ACCOUNTS2.url_valence < -0.1;

select count(distinct SAMPLED_T_ACCOUNTS2.user_id) from SAMPLED_T_ACCOUNTS2
right join CONN_REB22 on CONN_REB22.twitter_user_id = SAMPLED_T_ACCOUNTS2.user_id
where SAMPLED_T_ACCOUNTS2.url_valence < -0.5;

-- The following are some helper view/type/function.
CREATE MATERIALIZED VIEW UserValenceBucketView AS
  select
  -0.5 as left_bound,
  -0.1 as c_left_bound,
  0.1 as center_bound,
  0.5 as c_right_bound,
  1 as right_bound;

CREATE TYPE val_buckets AS (
    left_leaning FLOAT,
    cleft_leaning FLOAT,
    center_leaning FLOAT,
    cright_leaning FLOAT,
    right_leaning FLOAT
); 

create function find_leaning(score float, val_boundaries val_buckets)
returns int
language plpgsql
as
$$
declare
   leaning_id integer;
begin
  if score < val_boundaries.left_leaning then
    leaning_id = 1;
  else 
    if score < val_boundaries.cleft_leaning then
      leaning_id = 2;
    else
      if score < val_boundaries.center_leaning then
        leaning_id = 3;
      else
        if score < val_boundaries.cright_leaning then
          leaning_id = 4;
        else
          leaning_id = 5;
        END if;
      END if;
    END if;
  END if;
  RETURN leaning_id;
end;
$$;

CREATE MATERIALIZED VIEW user_leaning_buckets AS
  SELECT t.user_id,
         find_leaning(t.url_valence, bounds.val_buckets) as leaning
  FROM SAMPLED_T_ACCOUNTS2 as t,
       (select ROW(left_bound, c_left_bound,
                   center_bound, c_right_bound,
                   right_bound)::val_buckets as val_buckets
        from UserValenceBucketView) as bounds;

CREATE VIEW availableUserNewsPair AS
  SELECT leaning_tbl.user_id as twitter_user_id,
         news_source.twitter_handle as news_source,
         news_source.leaning as news_leaning,
         leaning_tbl.leaning as user_leaning
  FROM CONN_REB22,
       news_source,
       user_leaning_buckets as leaning_tbl
  WHERE leaning_tbl.user_id = CONN_REB22.twitter_user_id AND
       CONN_REB22.new_source_twitter_id = news_source.twitter_id;

-- Get news source popularity in each political bucket.

-- left
With LeftUserInfo AS (
  select twitter_user_id, news_source, news_leaning
  from availableUserNewsPair where user_leaning = 1
),
LeftNewsCount AS (
  select news_source, news_leaning, count(*) as num_users
  from LeftUserInfo
  group by news_source, news_leaning)
select news_source, news_leaning, num_users as left_user_count
from LeftNewsCount
where news_leaning = 'left'
order by news_leaning;

-- cleft
With CLeftUserInfo AS (
  select twitter_user_id, news_source, news_leaning
  from availableUserNewsPair where user_leaning = 2
),
CLeftNewsCount AS (
  select news_source, news_leaning, count(*) as num_users
  from CLeftUserInfo
  group by news_source, news_leaning)
select news_source, news_leaning, num_users as cleft_user_count
from CLeftNewsCount
where news_leaning = 'cleft'
order by news_leaning;

-- center
With CenterUserInfo AS (
  select twitter_user_id, news_source, news_leaning
  from availableUserNewsPair where user_leaning = 3
),
CenterNewsCount AS (
  select news_source, news_leaning, count(*) as num_users
  from CenterUserInfo
  group by news_source, news_leaning)
select news_source, news_leaning, num_users as center_user_count
from CenterNewsCount
where news_leaning = 'center'
order by news_leaning;

-- cright
With CRightUserInfo AS (
  select twitter_user_id, news_source, news_leaning
  from availableUserNewsPair where user_leaning = 4
),
CRightNewsCount AS (
  select news_source, news_leaning, count(*) as num_users
  from CRightUserInfo
  group by news_source, news_leaning)
select news_source, news_leaning, num_users as cright_user_count
from CRightNewsCount
where news_leaning = 'cright'
order by news_leaning;

-- right
With RightUserInfo AS (
  select twitter_user_id, news_source, news_leaning
  from availableUserNewsPair where user_leaning = 5
),
RightNewsCount AS (
  select news_source, news_leaning, count(*) as num_users
  from RightUserInfo
  group by news_source, news_leaning)
select news_source, news_leaning, num_users as right_user_count
from RightNewsCount
where news_leaning = 'right'
order by news_leaning;

