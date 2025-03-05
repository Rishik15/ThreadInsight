import pandas as pd
from collections import Counter
import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def get_most_common_words(df_posts, top_n=20):
    stop_words = ENGLISH_STOP_WORDS
    combined_text = (df_posts['title'].fillna('') + ' ' + df_posts['selftext'].fillna('')).str.lower()
    all_text = ' '.join(combined_text)

    words = re.findall(r'\b\w+\b', all_text)
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]

    word_counts = Counter(filtered_words).most_common(top_n)

    word_df = pd.DataFrame(word_counts, columns=['Word', 'Frequency'])

    return word_df

def fetch_stats(df_posts, df_comments):
    posts_count = len(df_posts)
    comments_count = len(df_comments)
    start_date = df_posts["created_date"].min()
    end_date = df_posts["created_date"].max() 
    post_authors = set(df_posts['author'])
    comment_authors = set(df_comments['comment_author'])
    unique_users = len(post_authors.union(comment_authors)) 


    return posts_count, comments_count, start_date, end_date, unique_users


def fetch_post_summary(df_posts):
    total_posts = len(df_posts)
    avg_upvotes = round(df_posts["upvotes"].mean(), 2)
    avg_comments = round(df_posts["num_comments"].mean(), 2)
    link_posts = df_posts["has_link"].sum()
    nsfw_posts = df_posts["over_18"].sum()
    spoiler_posts = df_posts["spoiler"].sum()
    locked_posts = df_posts["locked"].sum()
    gilded_posts = df_posts["gilded"].sum()
    
    return {
        "total_posts": total_posts,
        "avg_upvotes": avg_upvotes,
        "avg_comments": avg_comments,
        "link_posts": link_posts,
        "nsfw_posts": nsfw_posts,
        "spoiler_posts": spoiler_posts,
        "locked_posts": locked_posts,
        "gilded_posts": gilded_posts
    }


def fetch_comment_summary(df_comments):
    total_comments = len(df_comments)
    avg_upvotes = round(df_comments["comment_upvotes"].mean(), 2)

    excluded_authors = ["[deleted]", "AutoModerator"]
    author_counts = (
        df_comments[~df_comments["comment_author"].isin(excluded_authors)]
        .groupby("comment_author")
        .size()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    comments_per_date = df_comments["comment_created_date"].value_counts().sort_index()

    df_comments["comment_hour"] = pd.to_datetime(df_comments["comment_created_time"], format="%H:%M:%S").dt.hour
    comments_per_hour = df_comments["comment_hour"].value_counts().sort_index()

    return {
        "total_comments": total_comments,
        "avg_upvotes": avg_upvotes,
        "top_authors": author_counts,
        "comments_per_date": comments_per_date,
        "comments_per_hour": comments_per_hour
    }

def top_performers(df_posts, df_comments):
    top_posts_upvotes = df_posts.nlargest(5, 'upvotes')[['title', 'author', 'upvotes', 'num_comments']].reset_index(drop=True)
    df_posts['engagement'] = df_posts['upvotes'] + df_posts['num_comments']
    top_posts_engagement = df_posts.nlargest(5, 'engagement')[['title', 'author', 'engagement']].reset_index(drop=True)

    filtered_comments = df_comments[df_comments['comment_author'].str.lower() != 'automoderator']
    top_comments_upvotes = filtered_comments.nlargest(5, 'comment_upvotes')[['comment_author', 'comment_upvotes']].reset_index(drop=True)

    return top_posts_upvotes, top_posts_engagement, top_comments_upvotes




def activity_analysis(df_posts, df_comments):
    post_hours = (
        df_posts["created_time"]
        .apply(lambda x: x.hour)
        .value_counts()
        .sort_index()
        .reset_index()
    )
    post_hours.columns = ["hour", "count"]
    post_days = (
        df_posts["created_date"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    post_days.columns = ["date", "count"]
    comment_hours = (
        df_comments["comment_created_time"]
        .apply(lambda x: x.hour)
        .value_counts()
        .sort_index()
        .reset_index()
    )
    comment_hours.columns = ["hour", "count"]

    return post_hours, post_days, comment_hours


def user_insights(df_posts, df_comments, new_threshold_days=30):
    post_authors = df_posts['author'].dropna()
    comment_authors = df_comments['comment_author'].dropna()
    
    combined_authors = pd.concat([post_authors, comment_authors])
    most_active_users = combined_authors.value_counts().head(5)
    
    top_contributors = df_posts[df_posts['author'].isin(most_active_users.index)]
    avg_account_age = int(top_contributors['account_age_days'].mean())
    
    new_accounts = df_posts['account_age_days'].le(new_threshold_days).sum()
    total_accounts = df_posts['account_age_days'].count()
    new_account_percentage = round((new_accounts / total_accounts) * 100, 2) if total_accounts else 0
    
    return most_active_users, avg_account_age, new_account_percentage

