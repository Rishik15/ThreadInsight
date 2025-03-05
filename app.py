import streamlit as st
import time
import pandas as pd
from pathlib import Path
import base64
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

image_path = Path(__file__).parent / "images"

def get_image_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

gmail_icon = get_image_base64(image_path / "gmail.png")
linkedin_icon = get_image_base64(image_path / "linkedin.png")
github_icon = get_image_base64(image_path / "github.png")

st.markdown("""
<style>
.about-container {
    border: 1px solid #5c5c5c;
    border-radius: 10px;
    padding: 15px;
    margin-top: 20px;
    margin-bottom: 20px;
}
.contact-icon {
    vertical-align: middle;
    margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="about-container">

**ThreadInsight** is a Reddit analysis tool designed to provide deep insights into any subreddit.  It visualizes post and comment activity, top contributors, engagement metrics, heatmaps of active times, common keywords, and more — helping you easily understand the dynamics of online communities.

---

**Creator:** Rishik Reddy Yesgari  

<a href="https://www.linkedin.com/in/rishikreddyyesgari/" target="_blank">
    <img class="contact-icon" src="data:image/png;base64,{linkedin_icon}" width="18"> LinkedIn
</a>  
<br>
<a href="https://github.com/Rishik15" target="_blank">
    <img class="contact-icon" src="data:image/png;base64,{github_icon}" width="18"> GitHub
</a>
<br>
<a href="mailto:rishikreddy.yesgari@gmail.com">
    <img class="contact-icon" src="data:image/png;base64,{gmail_icon}" width="18"> Email
</a>  


</div>
""", unsafe_allow_html=True)


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

            st.subheader("Comment Frequency by Date (Bar)")
            st.plotly_chart(px.bar(
                x=comment_summary["comments_per_date"].index,
                y=comment_summary["comments_per_date"].values,
                labels={"x": "Date", "y": "Frequency"},
                color_discrete_sequence=['#003366']
            ), use_container_width=True)

            st.subheader("Comment Frequency by Date (Line)")
            st.plotly_chart(px.line(
                x=comment_summary["comments_per_date"].index,
                y=comment_summary["comments_per_date"].values,
                labels={"x": "Date", "y": "Frequency"},
                line_shape='linear',
                markers=True
            ), use_container_width=True)

            st.subheader("Comment Frequency by Hour (Bar)")
            st.plotly_chart(px.bar(
                x=comment_summary["comments_per_hour"].index,
                y=comment_summary["comments_per_hour"].values,
                labels={"x": "Hour", "y": "Frequency"},
                color_discrete_sequence=['#003366']
            ), use_container_width=True)

            st.subheader("Comment Frequency by Hour (Line)")
            st.plotly_chart(px.line(
                x=comment_summary["comments_per_hour"].index,
                y=comment_summary["comments_per_hour"].values,
                labels={"x": "Hour", "y": "Frequency"},
                line_shape='linear',
                markers=True
                ), use_container_width=True)
            
            st.header("User Insights")

            most_active_users, avg_account_age, new_account_percentage = user_insights(df_posts, df_comments)

            st.subheader("Top 5 Most Active Users")
            for user, count in most_active_users.items():
                st.write(f"- **{user}**: {count} total activities")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Average Account Age of Top Contributors (days)", avg_account_age)
            
            with col2:
                 st.metric("Percentage of Posts from New Accounts", f"{new_account_percentage}%")

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

            st.plotly_chart(px.line(
                post_hours, x="hour", y="count", title="Post Frequency by Hour (Line Chart)",
                markers=True
            ), use_container_width=True)

            st.plotly_chart(px.bar(
                post_days, x="date", y="count", title="Posts per Day",
                color_discrete_sequence=['#003366']
            ), use_container_width=True)

            st.plotly_chart(px.line(
                post_days, x="date", y="count", title="Posts per Day (Line Chart)",
                markers=True
            ), use_container_width=True)

            st.header("Post Activity Heatmap (Date vs Hour)")

            heatmap_posts = df_posts.copy()
            heatmap_posts['hour'] = pd.to_datetime(heatmap_posts['created_time'], format='%H:%M:%S').dt.hour
            heatmap_posts['date'] = heatmap_posts['created_date']

            post_heatmap_grouped = heatmap_posts.groupby(['date', 'hour']).size().reset_index(name='count')

            fig_post_heatmap = px.density_heatmap(
                post_heatmap_grouped,
                x="hour",
                y="date",
                z="count",
                color_continuous_scale="Blues",
                labels={'hour': 'Hour of Day', 'date': 'Date', 'count': 'Post Count'},
                nbinsx=24
            )

            st.plotly_chart(fig_post_heatmap, use_container_width=True)

            st.header("Comment Activity Heatmap (Date vs Hour)")

            heatmap_comments = df_comments.copy()
            heatmap_comments['hour'] = pd.to_datetime(heatmap_comments['comment_created_time'], format='%H:%M:%S').dt.hour
            heatmap_comments['date'] = heatmap_comments['comment_created_date']

            comment_heatmap_grouped = heatmap_comments.groupby(['date', 'hour']).size().reset_index(name='count')

            fig_comment_heatmap = px.density_heatmap(
                comment_heatmap_grouped,
                x="hour",
                y="date",
                z="count",
                color_continuous_scale="Blues",
                labels={'hour': 'Hour of Day', 'date': 'Date', 'count': 'Comment Count'},
                nbinsx=24
            )

            st.plotly_chart(fig_comment_heatmap, use_container_width=True)


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

