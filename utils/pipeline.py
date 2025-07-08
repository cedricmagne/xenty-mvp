import joblib
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
        Calculate engagement features from tweets data.
        
        Args:
            tweets_data (Dict): Dictionary containing tweet data
            
        Returns:
            pd.DataFrame: DataFrame with engagement features
        """
        features_list = []
        
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
                
                # Avoid division by zero
                if views > 0:
                    likes_per_views = likes / views
                    retweets_per_views = retweets / views
                    replies_per_views = replies / views
                else:
                    # Skip tweets with no views
                    continue
                    
                features_list.append({
                    'tweet_id': tweet_id,
                    'likes_per_views': likes_per_views,
                    'retweets_per_views': retweets_per_views,
                    'replies_per_views': replies_per_views,
                    'views': views,
                    'likes': likes,
                    'retweets': retweets,
                    'replies': replies
                })
                
            except Exception as e:
                logger.warning(f"Error processing tweet {tweet_id}: {e}")
                continue
                
        return pd.DataFrame(features_list)
    
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
    
    def get_account_engagement_summary(self, tweets_df: pd.DataFrame) -> Dict:
        """
        Generate an engagement summary for the account.
        
        Args:
            tweets_df (pd.DataFrame): DataFrame with tweet features and clusters
            
        Returns:
            Dict: Summary statistics and insights
        """

        if tweets_df.empty:
            return {}
            
        summary = {
            'total_tweets': len(tweets_df),
            'avg_likes_per_views': tweets_df['likes_per_views'].mean(),
            'avg_retweets_per_views': tweets_df['retweets_per_views'].mean(),
            'avg_replies_per_views': tweets_df['replies_per_views'].mean(),
            'total_views': tweets_df['views'].sum(),
            'total_likes': tweets_df['likes'].sum(),
            'total_retweets': tweets_df['retweets'].sum(),
            'total_replies': tweets_df['replies'].sum(),
            'cluster_distribution': tweets_df['cluster_label'].value_counts().to_dict(),
            'dominant_cluster': tweets_df['cluster_label'].mode().iloc[0] if not tweets_df.empty else None
        }
        
        return summary

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
            
    logger.info(f"Filtered {len(tweets_data)} tweets down to {len(filtered_tweets)} valid tweets")
    return filtered_tweets
