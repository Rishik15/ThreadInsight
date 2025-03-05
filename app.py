import streamlit as st
import time
from datetime import datetime
from src.fetch import fetch_recent_posts, fetch_comments_parallel
from src.preprocess import preprocessposts, preprocesscomments
from dotenv import load_dotenv
from helper import (
    fetch_stats, fetch_post_summary, fetch_comment_summary, 
    top_performers, activity_analysis, user_insights, get_most_common_words
)
import plotly.express as px
import wordcloud
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import matplotlib.pyplot as plt

load_dotenv()
st.set_page_config(page_title="ThreadInsight")
st.title('ThreadInsight')

with st.form("subreddit_form"):
    subreddit_name = st.text_input("Enter the subreddit name (without r/):", placeholder="e.g., learnpython")
    submitted = st.form_submit_button("Get Insights")

if submitted:
    if subreddit_name:
        with st.spinner(f"Fetching data from the past 3 days in r/{subreddit_name}. Please wait..."):
            posts, subscribers = fetch_recent_posts(subreddit_name)
            comments = fetch_comments_parallel(posts)
            status_placeholder = st.empty()

            if not posts:
                status_placeholder.warning(f"No posts found in r/{subreddit_name} from the past 3 days.")
            else:
                df_posts = preprocessposts(posts)
                df_comments = preprocesscomments(comments)
                st.session_state["df_posts"] = df_posts
                st.session_state["df_comments"] = df_comments

                status_placeholder.success(f"Successfully fetched {len(posts)} posts and {len(comments)} comments.")
        time.sleep(2)
        status_placeholder.empty()

        with st.spinner(f"Analyzing Data..."):
            posts_count, comments_count, start_date, end_date, unique_users = fetch_stats(df_posts, df_comments)
            st.header(f"Subreddit \"r/{subreddit_name}\" Overview")

            col1, col2, col3 = st.columns(3)
            col1.metric("Subscribers", f"{subscribers:,}")
            col1.metric("Unique Users", f"{unique_users}")
            col2.metric("Total Posts", f"{posts_count}")
            col2.metric("Total Comments", f"{comments_count}")
            col3.metric("Start Date", start_date.strftime("%Y-%m-%d"))
            col3.metric("End Date", end_date.strftime("%Y-%m-%d"))

            post_summary = fetch_post_summary(df_posts)
            st.header("Posts Summary Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg. Upvotes", post_summary["avg_upvotes"])
            col1.metric("Locked Posts", post_summary["locked_posts"])
            col2.metric("Avg. Comments/Post", post_summary["avg_comments"])
            col2.metric("NSFW Posts", post_summary["nsfw_posts"])
            col3.metric("Posts with Links", post_summary["link_posts"])
            col3.metric("Gilded Posts", post_summary["gilded_posts"])

            post_types = df_posts['post_type'].value_counts().reset_index()
            post_types.columns = ['post_type', 'count']  

            fig_post_types = px.pie(
                post_types,
                names='post_type',  
                values='count',      
                title='Post Types Distribution',
                color_discrete_sequence=['#003366']
            )
            st.plotly_chart(fig_post_types, use_container_width=True)


            comment_summary = fetch_comment_summary(df_comments)
            st.header("Comments Summary Metrics")
            st.metric("Avg. Upvotes per Comment", comment_summary["avg_upvotes"])

            st.subheader("Top 5 Commenters")
            if comment_summary["top_authors"]:
                for author, count in comment_summary["top_authors"].items():
                    st.write(f"- **{author}**: {count} comments")
            else:
                st.write("No active commenters found.")

            st.subheader("Comment Activity by Date")
            st.plotly_chart(px.bar(
                x=comment_summary["comments_per_date"].index,
                y=comment_summary["comments_per_date"].values,
                labels={"x": "Date", "y": "Comments"},
                color_discrete_sequence=['#003366']
            ), use_container_width=True)

            st.subheader("Comment Activity by Hour")
            st.plotly_chart(px.bar(
                x=comment_summary["comments_per_hour"].index,
                y=comment_summary["comments_per_hour"].values,
                labels={"x": "Hour", "y": "Comments"},
                color_discrete_sequence=['#003366']
            ), use_container_width=True)

            st.header("Top Performers")
            top_posts_upvotes, top_posts_engagement, top_comments_upvotes = top_performers(df_posts, df_comments)
            col1, col2 = st.columns(2)
            col1.subheader("Top Posts by Upvotes")
            col1.dataframe(top_posts_upvotes)
            col2.subheader("Top Posts by Engagement")
            col2.dataframe(top_posts_engagement)

            st.subheader("Top Comments by Upvotes")
            st.dataframe(top_comments_upvotes)

            st.header("Activity Analysis")
            post_hours, post_days, comment_hours = activity_analysis(df_posts, df_comments)

            st.plotly_chart(px.bar(
                post_hours, x="hour", y="count", title="Post Frequency by Hour",
                color_discrete_sequence=['#003366']
            ), use_container_width=True)
            st.plotly_chart(px.bar(
                post_days, x="date", y="count", title="Posts per Day",
                color_discrete_sequence=['#003366']
            ), use_container_width=True)


            st.header("Most Common Words in Posts")

            common_words = get_most_common_words(df_posts)

            fig_words = px.bar(
                common_words, 
                x='Frequency', 
                y='Word', 
                orientation='h',
                title='Top 20 Most Common Words in Posts',
                color='Frequency',
                color_continuous_scale='Blues',
                labels={'Frequency': 'Frequency', 'Word': 'Word'}
            )

            fig_words.update_layout(
                yaxis={'categoryorder':'total ascending'}
            )

            st.plotly_chart(fig_words, use_container_width=True)

            st.header("Word Cloud of the Entire Subreddit")
            full_text = ' '.join(df_posts['title'].fillna('')) + ' ' + ' '.join(df_posts['selftext'].fillna(''))

            wordcloud = wordcloud.WordCloud(
                width=1000,
                height=500,
                background_color='black',
                colormap='Blues',
                stopwords=ENGLISH_STOP_WORDS 
            ).generate(full_text)

            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)




    else:
        st.warning("Please enter a subreddit name.")
