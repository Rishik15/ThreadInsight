import pandas as pd

def preprocessposts(posts):
    df_posts = pd.DataFrame(posts)
    df_posts["created_utc"] = pd.to_datetime(df_posts["created_utc"], unit="s")
    df_posts["created_date"] = df_posts["created_utc"].dt.date
    df_posts["created_time"] = df_posts["created_utc"].dt.time
    df_posts.drop(columns = ["created_utc"], axis = 1, inplace = True)
    df_posts["has_link"] = df_posts["selftext"].str.contains(r'http[s]?://', na=False)
    df_posts["engagement_score"] = df_posts["upvotes"] + df_posts["num_comments"].fillna(0)

    return df_posts

def preprocesscomments(comments):
    df_comments = pd.DataFrame(comments)
    df_comments["comment_created_utc"] = pd.to_datetime(df_comments["comment_created_utc"], unit="s")
    df_comments["comment_created_date"] = df_comments["comment_created_utc"].dt.date
    df_comments["comment_created_time"] = df_comments["comment_created_utc"].dt.time
    df_comments.drop(columns = ["comment_created_utc"], axis = 1, inplace = True)

    return df_comments
