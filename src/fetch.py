import time
import praw
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import prawcore

days_to_fetch = 3
max_posts = 500
post_workers = 2
comment_workers = 3


def create_reddit_instance(client_id, client_secret, user_agent):
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )


def fetch_recent_posts(subreddit_name, reddit):
    all_posts = []

    try:
        subreddit_instance = reddit.subreddit(subreddit_name)
        subreddit_instance.id
    except prawcore.exceptions.NotFound:
        raise ValueError(f"Subreddit '{subreddit_name}' does not exist.")

    start_time = datetime.now(timezone.utc) - timedelta(days=days_to_fetch)
    start_timestamp = int(start_time.timestamp())

    post_list = []
    backoff_time = 1

    subscribers = subreddit_instance.subscribers
    time.sleep(1)

    while True:
        try:
            for post in subreddit_instance.new(limit=max_posts):
                if post.created_utc < start_timestamp:
                    break
                post_list.append(post)

            post_list.sort(key=lambda x: x.created_utc, reverse=True)
            break

        except praw.exceptions.APIException as e:
            if "RATELIMIT" in str(e):
                time.sleep(backoff_time)
                backoff_time *= 2
            else:
                raise e

    def process_post(post):
        post_type = "Text"
        if post.url.endswith((".jpg", ".png", ".gif", ".jpeg")):
            post_type = "Image"
        elif "v.redd.it" in post.url:
            post_type = "Video"

        try:
            account_age_days = (
                (datetime.now(timezone.utc) - datetime.fromtimestamp(post.author.created_utc, tz=timezone.utc)).days
                if post.author and hasattr(post.author, "created_utc")
                else None
            )
        except:
            account_age_days = None

        return {
            "id": post.id,
            "author": post.author.name if post.author else "[deleted]",
            "title": post.title,
            "selftext": post.selftext,
            "is_self": post.is_self,
            "num_comments": post.num_comments,
            "over_18": post.over_18,
            "spoiler": post.spoiler,
            "locked": post.locked,
            "gilded": post.gilded,
            "upvotes": post.score,
            "created_utc": post.created_utc,
            "post_type": post_type,
            "account_age_days": account_age_days
        }

    with ThreadPoolExecutor(max_workers=post_workers) as executor:
        futures = [executor.submit(process_post, post) for post in post_list]

        for count, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            if result:
                all_posts.append(result)

            if count % 100 == 0:
                time.sleep(1)

    return all_posts, subscribers


def fetch_comments(post_id, reddit):
    backoff_time = 2
    while True:
        try:
            submission = reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)

            comments = []
            for comment in submission.comments.list():
                comments.append({
                    "comment_id": comment.id,
                    "comment_author": comment.author.name if comment.author else "[deleted]",
                    "comment_upvotes": comment.score,
                    "comment_created_utc": comment.created_utc,
                    "post_id": post_id
                })

            return comments

        except praw.exceptions.APIException as e:
            if "RATELIMIT" in str(e):
                time.sleep(backoff_time)
                backoff_time *= 2
            else:
                return []


def fetch_comments_parallel(posts, reddit):
    all_comments = []
    with ThreadPoolExecutor(max_workers=comment_workers) as executor:
        future_to_post = {executor.submit(fetch_comments, post["id"], reddit): post["id"] for post in posts}

        for count, future in enumerate(as_completed(future_to_post), start=1):
            post_id = future_to_post[future]
            all_comments.extend(future.result())

            if count % 50 == 0:
                time.sleep(0.5)

    return all_comments
