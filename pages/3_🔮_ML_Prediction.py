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
    screen_name = st.text_input("Enter Twitter screen name (with or without @)")
    submit_button = st.form_submit_button("Analyze")

# Process the form submission outside the form context
if submit_button and screen_name:
        tweets_data = get_twitter_data(screen_name)
        
        
        if tweets_data:
            # Clean the screen name (remove @ if present)
            if screen_name.startswith('@'):
                screen_name = screen_name[1:]
            st.success(f"Successfully retrieved data for @{screen_name}")
            
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
                
                if results_df is not None and not results_df.empty:
                    # Generate account summary
                    summary = predictor.get_account_engagement_summary(results_df)
                    
                    # Display engagement analysis results
                    st.header("📊 Engagement Analysis Results")

                    st.metric("Dominant Cluster", f"{engagement_clusters_4[0]['cluster_color']} {summary['dominant_cluster']}")

                    st.write(engagement_clusters_4[0]['cluster_description'])
                    
                    # Account Overview
                    st.subheader("Account Overview")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Tweets Analyzed", summary['total_tweets'])
                    with col2:
                        st.metric("Total Views", f"{summary['total_views']:,}")
                    with col3:
                        st.metric("Total Likes", f"{summary['total_likes']:,}")
                    
                    # Engagement Ratios
                    st.subheader("Average Engagement Ratios")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Likes per View", f"{summary['avg_likes_per_views']:.4f}")
                    with col2:
                        st.metric("Retweets per View", f"{summary['avg_retweets_per_views']:.4f}")
                    with col3:
                        st.metric("Replies per View", f"{summary['avg_replies_per_views']:.4f}")
                    
                    # Cluster Distribution Chart
                    st.subheader("📈 Engagement Cluster Distribution")
                    cluster_df = pd.DataFrame(list(summary['cluster_distribution'].items()), 
                                            columns=['Cluster', 'Count'])
                    
                    fig_pie = px.pie(cluster_df, values='Count', names='Cluster', 
                                   title="Distribution of Tweets by Engagement Level")
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Engagement Features Scatter Plot
                    st.subheader("🎯 Engagement Features Analysis")
                    fig_scatter = px.scatter(results_df, 
                                           x='likes_per_views', 
                                           y='retweets_per_views',
                                           size='views',
                                           color='cluster_label',
                                           hover_data=['replies_per_views', 'views', 'likes'],
                                           title="Engagement Patterns: Likes vs Retweets per View")
                    fig_scatter.update_layout(height=500)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    # Individual Tweet Analysis
                    st.subheader("🔍 Individual Tweet Analysis")
                    
                    # Sort tweets by cluster for better organization
                    sorted_df = results_df.sort_values(['cluster', 'likes_per_views'], ascending=[True, False])
                    
                    for _, row in sorted_df.iterrows():
                        tweet_info = filtered_tweets[row['tweet_id']]
                    
                        with st.expander(f"Tweet (Cluster: {row['cluster_label']}) - Likes/Views: {row['likes_per_views']:.4f}"):
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
                                st.write(f"Likes/Views: {row['likes_per_views']:.4f}")
                            with col2:
                                st.write(f"Retweets/Views: {row['retweets_per_views']:.4f}")
                            with col3:
                                st.write(f"Replies/Views: {row['replies_per_views']:.4f}")
                            
                            # Cluster information
                            cluster_color = {
                                "Low Engagement": "🔴",
                                "Moderate Engagement": "🟡", 
                                "High Engagement": "🟢",
                                "Very High Engagement": "🔵"
                            }
                            st.markdown(f"**Engagement Level:** {cluster_color.get(row['cluster_label'], '⚪')} {row['cluster_label']}")
                            
                            # Comments section
                            if tweet_info.get('comments'):
                                st.markdown(f"**Comments ({len(tweet_info['comments'])}):**")
                                for j, comment in enumerate(tweet_info['comments'][:3]):  # Show first 3 comments
                                    st.markdown(f"• {comment}")
                                if len(tweet_info['comments']) > 3:
                                    st.markdown(f"... and {len(tweet_info['comments']) - 3} more comments")
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
