import streamlit as st
import logging
import json
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)

from utils.twitter import TwitterScraper

# Set page title
st.set_page_config(page_title="Twitter Prediction", layout="wide")

# Page header
st.title("Twitter Account Analysis")
st.write("Enter a Twitter screen name to analyze tweets and comments.")

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
    
    if submit_button and screen_name:
        tweets_data = get_twitter_data(screen_name)
        
        if tweets_data:
            # Clean the screen name (remove @ if present)
            if screen_name.startswith('@'):
                screen_name = screen_name[1:]
            st.success(f"Successfully retrieved data for @{screen_name}")
            
            # Display the tweets and comments
            st.subheader("Tweets and Comments")
            
            # Create tabs for each tweet
            tabs = st.tabs([f"Tweet {i+1}" for i in range(len(tweets_data))])
            
            # Populate each tab with tweet data
            for i, (tweet_id, tweet_info) in enumerate(tweets_data.items()):
                with tabs[i]:
                    # Tweet content
                    st.markdown(f"**Tweet:** {tweet_info['full_text']}")
                    
                    # Tweet metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Likes", tweet_info['likes_count'])
                    with col2:
                        st.metric("Retweets", tweet_info['retweet_count'])
                    with col3:
                        st.metric("Replies", tweet_info['reply_count'])
                    with col4:
                        st.metric("Views", tweet_info['views_count'])
                    
                    # Comments section
                    st.subheader(f"Comments ({len(tweet_info['comments'])})")
                    
                    if tweet_info['comments']:
                        for j, comment in enumerate(tweet_info['comments']):
                            st.markdown(f"**Comment {j+1}:** {comment}")
                    else:
                        st.info("No comments found for this tweet.")
