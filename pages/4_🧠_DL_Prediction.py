import streamlit as st
import logging
import json
import pandas as pd
import plotly.express as px
import os
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)

from utils.twitter import TwitterScraper
from utils.init import *  # Initialize environment and logging
from utils.distilbert_sentiment import XentySentimentAnalyzer

@st.cache_resource
def load_sentiment_analyzer():
    model_path = "./models/dl/best_distilbert_model.h5"  # relatif au dossier de l'app
    return XentySentimentAnalyzer(model_path)

analyzer = load_sentiment_analyzer()
st.success("Analyseur de sentiment chargé ✅")

# Set page title
st.set_page_config(page_title="Comment Sentiment Analysis", layout="wide")

# Page header
st.title("💬 Comment Sentiment Analysis")
st.write("Analyse du sentiment des commentaires Twitter à l'aide du Deep Learning.")

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
        with st.spinner(f"Récupération des tweets et commentaires pour @{screen_name}..."):

            # Query the database to get the saved tweets
            query = f"SELECT posts FROM x_cryptos WHERE screen_name = ? LIMIT 1"
            result = scraper.conn.cursor().execute(query, (screen_name,)).fetchone()
            
            if not result or not result[0]:
                st.error(f"Aucun tweet trouvé pour @{screen_name}")
                return None
                
            # Parse the JSON string from the database
            tweets_data = json.loads(result[0])
            
            # Close the database connection
            scraper.conn.close()
            
            return tweets_data
            
    except Exception as e:
        st.error(f"Erreur: {e}")
        logging.error(f"Error fetching Twitter data: {e}")
        return None

# Create the input form
with st.form("twitter_form"):
    screen_name = st.text_input("Entrez un compte X/Twitter (avec ou sans @)")
    submit_button = st.form_submit_button("Analyser")

# Process the form submission outside the form context
if submit_button and screen_name:
    tweets_data = get_twitter_data(screen_name)

    if tweets_data:
        # Clean the screen name (remove @ if present)
        if screen_name.startswith('@'):
            screen_name = screen_name[1:]

        tweet_ids = list(tweets_data.keys())
        last_tweet_id = tweet_ids[-1]

        for tweet_id, tweet_data in tweets_data.items():
            if len(tweet_data.get('comments', [])) == 0:
                if last_tweet_id == tweet_id:
                    st.warning("Aucun tweet trouvé avec un commentaire.")
                continue
    
            # Initialize sentiment analyzer
            try:        
                # Display the tweet with the most comments
                st.header(f"Tweet le plus récent")
                st.markdown(f"**Tweet:** {tweets_data[tweet_id]['full_text']}")
                    
                # Analyze sentiment of comments
                comments = tweets_data[tweet_id].get('comments', [])
                    
                with st.spinner("Analyse du sentiment des commentaires..."):
                    
                    # Predict sentiment for all comments
                    sentiment_results = analyzer.predict_sentiment(comments)
                        
                    # Count sentiments
                    sentiment_counts = {'bearish': 0, 'bullish': 0}
                    for sentiment, _ in sentiment_results:
                        if sentiment in sentiment_counts:
                            sentiment_counts[sentiment] += 1
                        
                    # Display sentiment distribution
                    st.subheader("📊 Distribution des sentiments")
                        
                    # Create a DataFrame for the pie chart
                    sentiment_df = pd.DataFrame({
                        'Sentiment': list(sentiment_counts.keys()),
                        'Count': list(sentiment_counts.values())
                    })
                    sentiment_df = sentiment_df[sentiment_df['Count'] > 0]  # Remove sentiments with zero count
                        
                    # Create color map
                    color_map = {'bullish': 'green', 'bearish': 'red'}
                        
                    # Create pie chart
                    fig = px.pie(
                        sentiment_df, 
                        values='Count', 
                        names='Sentiment',
                        color='Sentiment',
                        color_discrete_map=color_map,
                        title='Distribution des sentiments dans les commentaires'
                    )
                    st.plotly_chart(fig)
                        
                    # Display comments with sentiment
                    st.subheader("Analyse des commentaires")
                        
                    # Create a DataFrame with comments and their sentiment
                    comments_df = pd.DataFrame({
                        'Comment': comments,
                        'Sentiment': [result[0] for result in sentiment_results],
                        'Confidence': [result[1] for result in sentiment_results]
                    })
                        
                    # Sort by sentiment and confidence
                    comments_df = comments_df.sort_values(by=['Sentiment', 'Confidence'], ascending=[True, False])
                        
                    # Display comments in expandable sections grouped by sentiment
                    for sentiment in ['bullish', 'bearish']:
                        sentiment_comments = comments_df[comments_df['Sentiment'] == sentiment]
                        if not sentiment_comments.empty:
                            with st.expander(f"{sentiment.capitalize()} Comments ({len(sentiment_comments)})", expanded=sentiment == 'bullish'):
                                for _, row in sentiment_comments.iterrows():
                                    sentiment_color = {'bullish': 'green', 'bearish': 'red'}.get(row['Sentiment'], 'blue')
                                    sentiment_emoji = {'bullish': '📈', 'bearish': '📉'}.get(row['Sentiment'], '')
                                        
                                    st.markdown(f"<div style='background-color: rgba(0,0,0,0.05); padding: 10px; border-radius: 5px; margin-bottom: 10px;'>"
                                                f"<span style='color:{sentiment_color};'>{sentiment_emoji} {row['Sentiment'].capitalize()} ({row['Confidence']:.2f})</span><br>"
                                                f"{row['Comment']}</div>", unsafe_allow_html=True)
                # Download option
                if comments:
                    # Create a DataFrame with comments and their sentiment for download
                    download_df = pd.DataFrame({
                        'Comment': comments,
                        'Sentiment': [result[0] for result in sentiment_results],
                        'Confidence': [result[1] for result in sentiment_results]
                    })
                    
                    csv_data = download_df.to_csv(index=False)
                    st.download_button(
                        label="Télécharger l'analyse en CSV",
                        data=csv_data,
                        file_name=f"{screen_name}_comment_sentiment_analysis.csv",
                        mime="text/csv"
                    )
                    break

            except Exception as e:
                st.error(f"Erreur lors du chargement du modèle: {e}")
                logging.error(f"Error loading sentiment model: {e}")
