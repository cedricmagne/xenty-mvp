import streamlit as st
import logging
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)

from utils.twitter import TwitterScraper
from utils.pipeline import EngagementKMeansPredictor, filter_valid_tweets
from utils.init import *  # Initialize environment and logging
from utils.clusters import engagement_clusters_4

# Set page title
st.set_page_config(page_title="Twitter Engagement Analysis", layout="wide")

# Page header
st.title("🐦 Twitter Engagement Analysis")
st.write("Enter a Twitter screen name to analyze engagement patterns using ML clustering.")

def get_twitter_data(screen_name: str) -> Dict:
    """
    Get tweets and comments for a Twitter screen name.
    
    Args:
        screen_name (str): Twitter screen name (without @)
    
    Returns:
        Dict: Dictionary containing tweets and comments data
    """
    try:
        
        # Initialize the Twitter scraper
        scraper = TwitterScraper(rate_limit_per_second=10)
        
        # Clean the screen name (remove @ if present)
        if screen_name.startswith('@'):
            screen_name = screen_name[1:]
            
        # Get tweets with comments
        with st.spinner(f"Fetching tweets and comments for @{screen_name}..."):
            result = scraper.get_tweets_with_comments(
                usernames=[screen_name],
                tweet_count="20",  # Number of tweets to fetch
                comment_count="50",  # Number of comments per tweet
                ranking_mode="Relevance"  # Can be "Relevance", "Likes", or "Recency"
            )
            
            # Check if the operation was successful
            if not result.get(screen_name, False):
                st.error(f"Failed to fetch data for @{screen_name}")
                return None
                
            # Query the database to get the saved tweets
            query = f"SELECT posts FROM x_cryptos WHERE screen_name = ? LIMIT 1"
            result = scraper.conn.cursor().execute(query, (screen_name,)).fetchone()
            
            if not result or not result[0]:
                st.error(f"No tweets found for @{screen_name}")
                return None
                
            # Parse the JSON string from the database
            tweets_data = json.loads(result[0])
            
            # Close the database connection
            scraper.conn.close()
            
            return tweets_data
            
    except Exception as e:
        st.error(f"Error: {e}")
        logging.error(f"Error fetching Twitter data: {e}")
        return None

# Create the input form
with st.form("twitter_form"):
    screen_name = st.text_input("Enter X/Twitter account (with or without @ case sensitive)")
    submit_button = st.form_submit_button("Analyze")

# Process the form submission outside the form context
if submit_button and screen_name:
        tweets_data = get_twitter_data(screen_name)

        if tweets_data:
            # Clean the screen name (remove @ if present)
            if screen_name.startswith('@'):
                screen_name = screen_name[1:]

            # Filter valid tweets for analysis
            filtered_tweets = filter_valid_tweets(tweets_data)
            
            if not filtered_tweets:
                st.warning("No valid tweets found for engagement analysis after filtering.")
            else:
                # Initialize the engagement predictor
                predictor = EngagementKMeansPredictor()
                
                # Perform engagement clustering
                with st.spinner("Analyzing engagement patterns..."):
                    results_df = predictor.predict_engagement_clusters(filtered_tweets)

                    if results_df.empty:
                        result = None
                    else:
                        result = results_df.iloc[0]
                
                if result is not None:
                    
                    # Display engagement analysis results
                    st.header(f"📊 Engagement Analysis")

                    st.subheader("Means for each cluster")
                    # Load the CSV file
                    cluster_means_df = pd.read_csv('models/engagement_kmeans/cluster_means.csv', index_col=0)
                    # Add cluster labels and format for better readability
                    cluster_means_df['cluster_label'] = [engagement_clusters_4[i]['cluster_label'] for i in range(len(cluster_means_df))]
                    
                    st.dataframe(cluster_means_df)

                    st.subheader(f"Score for @{screen_name} -- {engagement_clusters_4[result['cluster']]['cluster_color']} {engagement_clusters_4[result['cluster']]['cluster_label']}")
                    st.dataframe(results_df[['likes_per_views', 'retweets_per_views', 'replies_per_views', 'cluster_label']])

                    st.write(engagement_clusters_4[result['cluster']]['cluster_description'])
                    
                    # Account Overview
                    st.subheader("Account Overview")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Tweets Analyzed", result['valid_tweets_count'])
                    with col2:
                        st.metric("Total Views", f"{result['total_views']:,}")
                    with col3:
                        st.metric("Total Likes", f"{result['total_likes']:,}")
                    
                    # Engagement Ratios
                    st.subheader("Average Engagement Ratios")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Likes per View", f"{result['likes_per_views']:.4f}")
                    with col2:
                        st.metric("Retweets per View", f"{result['retweets_per_views']:.4f}")
                    with col3:
                        st.metric("Replies per View", f"{result['replies_per_views']:.4f}")
                    
                    # Individual Tweet Analysis
                    st.subheader("🔍 Individual Tweet Analysis")

                    for tweet_id, row in filtered_tweets.items():
                        tweet_info = row
                    
                        with st.expander(f"Tweet {tweet_id}"):
                            # Tweet content
                            st.markdown(f"**Tweet:** {tweet_info['full_text']}")
                            
                            # Engagement metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                views_count = int(tweet_info.get('views_count', 0)) if tweet_info.get('views_count') else 0
                                st.metric("Views", f"{views_count:,}")
                            with col2:
                                likes_count = int(tweet_info.get('likes_count', 0)) if tweet_info.get('likes_count') else 0
                                st.metric("Likes", f"{likes_count:,}")
                            with col3:
                                retweet_count = int(tweet_info.get('retweet_count', 0)) if tweet_info.get('retweet_count') else 0
                                st.metric("Retweets", f"{retweet_count:,}")
                            with col4:
                                reply_count = int(tweet_info.get('reply_count', 0)) if tweet_info.get('reply_count') else 0
                                st.metric("Replies", f"{reply_count:,}")
                            
                            # Engagement ratios
                            st.markdown("**Engagement Ratios:**")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"Likes/Views: {row['likes_count'] / int(row['views_count']):.4f}")
                            with col2:
                                st.write(f"Retweets/Views: {row['retweet_count'] / int(row['views_count']):.4f}")
                            with col3:
                                st.write(f"Replies/Views: {row['reply_count'] / int(row['views_count']):.4f}")
                            
                            # Comments section
                            if tweet_info.get('comments'):
                                st.markdown(f"**Comments ({len(tweet_info['comments'])}):**")
                                for j, comment in enumerate(tweet_info['comments']):
                                    bg_color = "#333" if j % 2 == 0 else "#000"
                                    st.markdown(
                                        f'<div style="background-color: {bg_color}; padding: 5px; border-radius: 3px;">{comment}</div>', 
                                        unsafe_allow_html=True
                                    )
                                # if len(tweet_info['comments']) > 3:
                                #     st.markdown(f"... and {len(tweet_info['comments']) - 3} more comments")
                            else:
                                st.info("No comments found for this tweet.")
                    
                    # Raw Data Download
                    st.subheader("📥 Download Analysis Data")
                    csv_data = results_df.to_csv(index=False)
                    st.download_button(
                        label="Download Analysis Results as CSV",
                        data=csv_data,
                        file_name=f"{screen_name}_engagement_analysis.csv",
                        mime="text/csv"
                    )
                    
                else:
                    st.error("Failed to perform engagement analysis. Please check the data and try again.")
