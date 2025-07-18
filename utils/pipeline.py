import os
import json
import joblib
import sqlite3
import pandas as pd
from typing import Dict, Optional
import logging
from pathlib import Path
from utils.clusters import engagement_clusters_4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EngagementKMeansPredictor:
    """
    KMeans Engagement Clustering Model for Social Media Analysis
    """
    
    def __init__(self, model_dir: str = None):
        """
        Initialize the engagement predictor.
        
        Args:
            model_dir (str): Directory containing the saved model files
        """
        if model_dir is None:
            # Default to the project's models directory
            self.model_dir = Path(__file__).parent.parent / "models" / "engagement_kmeans"
        else:
            self.model_dir = Path(model_dir)
            
        self.scaler = None
        self.kmeans_model = None
        self.cluster_labels = {k: v["cluster_label"] for k, v in engagement_clusters_4.items()}
        
    def load_models(self) -> bool:
        """
        Load the saved scaler and KMeans model.
        
        Returns:
            bool: True if models loaded successfully, False otherwise
        """
        try:
            scaler_path = self.model_dir / "scaler.joblib"
            kmeans_path = self.model_dir / "kmeans.joblib"
            
            if not scaler_path.exists() or not kmeans_path.exists():
                logger.error(f"Model files not found in {self.model_dir}")
                return False
                
            self.scaler = joblib.load(scaler_path)
            self.kmeans_model = joblib.load(kmeans_path)
            
            logger.info("Models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def calculate_engagement_features(self, tweets_data: Dict) -> pd.DataFrame:
        """
        Calculate engagement features from tweets data using aggregated metrics across all tweets.
        Similar to the notebook approach with calculate_view_normalized_metric.
        
        Args:
            tweets_data (Dict): Dictionary containing tweet data
            
        Returns:
            pd.DataFrame: DataFrame with aggregated engagement features
        """
        logger = logging.getLogger(__name__)
        
        # Initialize totals
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_views = 0
        valid_tweets_count = 0
        
        # Aggregate metrics across all tweets
        for tweet_id, tweet_info in tweets_data.items():
            try:
                # Convert string values to integers with safe fallback
                try:
                    views = int(tweet_info.get('views_count', 0)) if tweet_info.get('views_count') else 0
                    likes = int(tweet_info.get('likes_count', 0)) if tweet_info.get('likes_count') else 0
                    retweets = int(tweet_info.get('retweet_count', 0)) if tweet_info.get('retweet_count') else 0
                    replies = int(tweet_info.get('reply_count', 0)) if tweet_info.get('reply_count') else 0
                except (ValueError, TypeError):
                    # Skip tweets with invalid metric data
                    continue
                
                # Only include tweets with views > 0
                if views > 0:
                    total_views += views
                    total_likes += likes
                    total_retweets += retweets
                    total_replies += replies
                    valid_tweets_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing tweet {tweet_id}: {e}")
                continue
        
        # Calculate view-normalized metrics
        if total_views > 0:
            likes_per_views = total_likes / total_views
            retweets_per_views = total_retweets / total_views
            replies_per_views = total_replies / total_views
        else:
            likes_per_views = 0
            retweets_per_views = 0
            replies_per_views = 0
            
        # Return single row DataFrame with aggregated features
        return pd.DataFrame([{
            'likes_per_views': likes_per_views,
            'retweets_per_views': retweets_per_views,
            'replies_per_views': replies_per_views,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_retweets': total_retweets,
            'total_replies': total_replies,
            'valid_tweets_count': valid_tweets_count
        }])
    
    def predict_engagement_clusters(self, tweets_data: Dict) -> Optional[pd.DataFrame]:
        """
        Predict engagement clusters for the given tweets data.
        
        Args:
            tweets_data (Dict): Dictionary containing tweet data
            
        Returns:
            pd.DataFrame: DataFrame with features and cluster predictions
        """
        # Load models if not already loaded
        if self.scaler is None or self.kmeans_model is None:
            if not self.load_models():
                return None
        
        # Calculate features
        df = self.calculate_engagement_features(tweets_data)
        
        if df.empty:
            logger.warning("No valid tweets found for clustering")
            return None
            
        # Prepare features for prediction
        feature_columns = ['likes_per_views', 'retweets_per_views', 'replies_per_views']
        features_df = df[feature_columns]
        
        # Scale features (using DataFrame to preserve feature names)
        features_scaled = self.scaler.transform(features_df)
        
        # Predict clusters
        clusters = self.kmeans_model.predict(features_scaled)
        
        # Add predictions to dataframe
        df['cluster'] = clusters
        df['cluster_label'] = df['cluster'].map(self.cluster_labels)
        
        return df

def filter_valid_tweets(tweets_data: Dict) -> Dict:
    """
    Filter tweets to remove invalid entries (like retweets or tweets without views).
    
    Args:
        tweets_data (Dict): Raw tweets data
        
    Returns:
        Dict: Filtered tweets data
    """
    filtered_tweets = {}
    
    for tweet_id, tweet_info in tweets_data.items():
        try:

            # Skip retweets/reposts as they don't have original interaction data
            if 'RT @' in tweet_info.get('full_text', ''):
                continue

            # Skip tweets without views but with interactions
            # Convert string values to integers with safe fallback
            try:
                views = int(tweet_info.get('views_count', 0)) if tweet_info.get('views_count') else 0
                likes = int(tweet_info.get('likes_count', 0)) if tweet_info.get('likes_count') else 0
                retweets = int(tweet_info.get('retweet_count', 0)) if tweet_info.get('retweet_count') else 0
                replies = int(tweet_info.get('reply_count', 0)) if tweet_info.get('reply_count') else 0
            except (ValueError, TypeError):
                # Skip tweets with invalid metric data
                continue
            
            # Skip if no views but has interactions (likely invalid data)
            if views == 0 and (likes > 0 or retweets > 0 or replies > 0):
                continue
                
            # Skip if no engagement metrics at all
            if views == 0 and likes == 0 and retweets == 0 and replies == 0:
                continue
                
            filtered_tweets[tweet_id] = tweet_info
            
        except Exception as e:
            logger.warning(f"Error filtering tweet {tweet_id}: {e}")
            continue
            
    #logger.info(f"Filtered {len(tweets_data)} tweets down to {len(filtered_tweets)} valid tweets")
    return filtered_tweets

# Fonction pour modifier le type de l'attribut views_count string -> int
def cast_views_count_to_int(post_json_str):
    if pd.isna(post_json_str):
        return post_json_str
    
    # Charger le JSON
    try:
        posts_dict = json.loads(post_json_str)
    except json.JSONDecodeError:
        # Si le JSON est invalide, retourner la valeur originale
        return post_json_str
    
    # Parcourir chaque tweet dans le dictionnaire
    for _, tweet_data in posts_dict.items():
        if 'views_count' in tweet_data:
            tweet_data['views_count'] = int(tweet_data.pop('views_count'))
    
    # Reconvertir en JSON string
    return posts_dict

def get_dl_training_data():
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "xenty.db")
    conn = sqlite3.connect(db_path)
    query = "SELECT screen_name, posts FROM x_cryptos WHERE posts IS NOT NULL"
    df = pd.read_sql_query(query, conn)
    conn.close()
    print("📊 Dataset créé avec", len(df), "comptes crypto")
    df['posts'] = df['posts'].apply(cast_views_count_to_int)
    df_filtered = df.copy()
    
    # Appliquer un filtre sur les tweets
    df_filtered["filtered_posts"] = df_filtered["posts"].apply(filter_valid_tweets)

    # Get reply count (comments) for each post
    df_filtered['total_replies_original'] = df_filtered['posts'].apply(
        lambda x: sum(len(tweet_data.get('comments', [])) for tweet_data in x.values())
    )

    # Get reply count (comments) for each post
    df_filtered['total_replies_filtered'] = df_filtered['filtered_posts'].apply(
        lambda x: sum(len(tweet_data.get('comments', [])) for tweet_data in x.values())
    )

    # Remove all row with total_replies_filtered = 0
    df_filtered = df_filtered[df_filtered['total_replies_filtered'] > 0].reset_index(drop=True)

    return df_filtered
    
    
    