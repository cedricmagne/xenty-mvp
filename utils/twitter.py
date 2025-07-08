import requests
import time
import json
import sqlite3
import logging
from typing import List, Dict

# Import environment variables module (which auto-loads .env)
from utils.env_loader import get_env_var

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwitterScraper:
    """A class to scrape Twitter data using RapidAPI.
    
    This class provides methods to fetch user data, tweets, and other information
    from Twitter using the Twitter241 RapidAPI endpoint.
    """
    
    BASE_URL = "https://twitter241.p.rapidapi.com"
    
    def __init__(self, api_key: str = None, rate_limit_per_second: int = 1, db_path: str = "data/xenty.db"):
        """Initialize the TwitterScraper with API credentials.
        
        Args:
            api_key: RapidAPI key for authentication
            rate_limit_per_second: Maximum number of requests per second (default: 1)
        """

        # Get API key from environment variable if not provided
        if not api_key:
            api_key = get_env_var('RAPIDAPI_KEY')
            
        if not api_key:
            logger.error("La variable d'environnement RAPIDAPI_KEY n'est pas définie!")
            print("\n🔧 Pour définir vos clés API Twitter/X:")
            print("Créez un fichier .env avec:")
            print("  RAPIDAPI_KEY=votre_api_key")
            print("\n🌐 Obtenez vos clés API sur: https://rapidapi.com/")
            exit(1)

        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "twitter241.p.rapidapi.com"
        }
        self.rate_limit = rate_limit_per_second
        self.last_request_time = 0

        self.logger = logging.getLogger('TwitterScraper')

        # Connect to database
        try:
            self.conn = sqlite3.connect(db_path)
            logger.info(f"Connexion établie avec la base de données: {db_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à la base de données: {e}")
            raise
    
    def _handle_rate_limit(self):
        """Handle rate limiting by adding delay between requests.
        
        Uses rate_limit_per_second to calculate appropriate delay between requests.
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Calculate minimum time between requests in seconds
        min_interval = 1 / self.rate_limit if self.rate_limit > 0 else 0.1
        
        # If we need to wait to respect rate limit
        if elapsed < min_interval and self.last_request_time > 0:
            wait_time = min_interval - elapsed
            self.logger.info(f"Rate limiting: waiting {wait_time:.3f} seconds (rate: {self.rate_limit:.1f}/sec)")
            time.sleep(wait_time)
            
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the Twitter API with rate limiting.
        
        Args:
            endpoint: API endpoint to call (without base URL)
            params: Query parameters for the request
            
        Returns:
            JSON response from the API
            
        Raises:
            Exception: If the API request fails
        """
        self._handle_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            self.logger.info(f"Making request to {endpoint} with params {params}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            if hasattr(response, 'text'):
                self.logger.error(f"Response: {response.text}")
            raise
    
    def get_users(self, user_ids: List[str] = None, usernames: List[str] = None) -> Dict:
        """Get information about Twitter users by their IDs or usernames.
        
        Args:
            user_ids: List of Twitter user IDs
            usernames: List of Twitter usernames (without @)
            
        Returns:
            Dictionary containing user information
            
        Raises:
            ValueError: If neither user_ids nor usernames are provided
        """
        if not user_ids and not usernames:
            raise ValueError("Either user_ids or usernames must be provided")
            
        params = {}
        if user_ids:
            params["users"] = ",".join(user_ids)
        elif usernames:
            params["usernames"] = ",".join(usernames)
            
        return self._make_request("get-users-v2", params)
    
    def get_user_tweets(self, user_id: str, count: str = "1", cursor: str = None) -> Dict:
        """Get tweets from a specific user by their Twitter user ID.
        
        Args:
            user_id: Twitter user ID (numeric string)
            count: Number of tweets to retrieve (default: 20, max: 100)
            cursor: Pagination cursor for fetching more tweets
            
        Returns:
            Dictionary containing user tweets
        """
        params = {
            "user": user_id,
            "count": count
        }
        
        if cursor:
            params["cursor"] = cursor
            
        return self._make_request("user-tweets", params)
    
    def search_tweets(self, query: str, count: str = "20", cursor: str = None) -> Dict:
        """Search for tweets matching a query.
        
        Args:
            query: Search query string
            count: Number of tweets to retrieve (default: 20)
            cursor: Pagination cursor for fetching more results
            
        Returns:
            Dictionary containing search results and pagination information
        """
        params = {
            "query": query,
            "count": count
        }
        
        if cursor:
            params["cursor"] = cursor
            
        return self._make_request("search", params)
    
    def get_tweet_details(self, tweet_id: str) -> Dict:
        """Get detailed information about a specific tweet.
        
        Args:
            tweet_id: ID of the tweet to retrieve
            
        Returns:
            Dictionary containing tweet details
        """
        params = {"tweet_id": tweet_id}
        return self._make_request("tweet-detail", params)
    
    def get_user_by_username(self, username: str) -> Dict:
        """Get detailed information about a user by their username.
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            Dictionary containing user details including profile information
        """
        params = {"username": username}
        return self._make_request("user", params)
    
    def batch_save_users_to_db(self, usernames: List[str], db_path: str = "cryptocurrency_dataset.db", 
                              table_name: str = "x_cryptos", x_name_column: str = "x_name") -> Dict[str, bool]:
        """Fetch and save Twitter data for multiple usernames.
        
        Args:
            usernames: List of Twitter usernames (without @)
            db_path: Path to SQLite database file
            table_name: Name of the table to update
            x_name_column: Name of the column containing Twitter usernames
            
        Returns:
            Dictionary mapping usernames to success status
        """
        results = {}
        total = len(usernames)
        
        for i, username in enumerate(usernames):
            self.logger.info(f"Processing {i+1}/{total}: {username}")
            success = self.save_user_to_db(username, db_path, table_name, x_name_column)
            results[username] = success
            
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"Completed batch processing: {success_count}/{total} successful")
        
        return results
    
    def batch_get_users(self, user_ids: List[str] = None, usernames: List[str] = None, 
                       batch_size: int = 100) -> List[Dict]:
        """Get information about multiple users in batches to respect API limits.
        
        Args:
            user_ids: List of Twitter user IDs
            usernames: List of Twitter usernames
            batch_size: Number of users to request in each batch (default: 100)
            
        Returns:
            List of user information dictionaries
        """
        if not user_ids and not usernames:
            raise ValueError("Either user_ids or usernames must be provided")
            
        source = user_ids if user_ids else usernames
        results = []
        
        # Process in batches
        for i in range(0, len(source), batch_size):
            batch = source[i:i+batch_size]
            
            if user_ids:
                batch_results = self.get_users(user_ids=batch)
            else:
                batch_results = self.get_users(usernames=batch)
                
            if batch_results and 'data' in batch_results:
                results.extend(batch_results['data'])
                
            # Log progress
            self.logger.info(f"Processed batch {i//batch_size + 1}/{(len(source)-1)//batch_size + 1}")
            
        return results
        
    def get_tweet_comments_v2(self, tweet_id: str, ranking_mode: str = "Relevance", count: str = "50") -> Dict:
        """Get comments for a specific tweet using the comments-v2 endpoint.
        
        Args:
            tweet_id: ID of the tweet to get comments for
            ranking_mode: How to rank comments - "Relevance", "Likes", or "Recency"
            count: Number of comments to retrieve (default: 50)
            
        Returns:
            Dictionary containing tweet comments
        """
        params = {
            "pid": tweet_id,
            "rankingMode": ranking_mode,
            "count": count
        }
        
        return self._make_request("comments-v2", params)
    
    def upsert_user_result_to_db(self, user_result: Dict, table_name: str = "x_cryptos") -> bool:
        try:
            # Extract the fields we want to save
            legacy = user_result.get('legacy', {})
            core = user_result.get('core', {})
            name = core.get('name', None)
            id = user_result.get('rest_id', None)
            screen_name = core.get('screen_name', None)
            description = legacy.get('description', None)
            is_blue_verified = user_result.get('is_blue_verified', False)
            followers_count = legacy.get('followers_count', 0)
            following_count = legacy.get('friends_count', 0)
            posts_count = legacy.get('statuses_count', 0)
            created_at = core.get('created_at', None)
            sync_at = int(time.time())

            # Update the database using proper parameterized query
            query = f"""
            INSERT INTO {table_name} (
                id,
                name,
                screen_name,
                description,
                is_blue_verified,
                followers_count,
                following_count,
                posts_count,
                created_at,
                sync_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(screen_name) DO UPDATE SET
                name = ?,
                description = ?,
                is_blue_verified = ?,
                followers_count = ?,
                following_count = ?,
                posts_count = ?,
                sync_at = ?
            """

            # Parameters for both INSERT and UPDATE parts
            params = (
                id, name, screen_name, description, is_blue_verified, 
                followers_count, following_count, posts_count, created_at, sync_at,
                # Parameters for the UPDATE part
                name, description, is_blue_verified, followers_count, 
                following_count, posts_count, sync_at
            )
            
            self.conn.cursor().execute(query, params)
            rows_affected = self.conn.cursor().rowcount
            
            # Commit changes and close connection
            self.conn.commit()
            
            self.logger.info(f"Successfully updated database for username: {screen_name}, {rows_affected} rows affected")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving user data to database: {e}")
            return False
        
    def get_tweets_with_comments(self, usernames: List[str], tweet_count: str = "1", 
                               comment_count: str = "50", ranking_mode: str = "Relevance",
                               table_name: str = "x_cryptos") -> Dict[str, bool]:
        """Get tweets and their comments for a list of usernames and save to database.
        
        Args:
            usernames: List of Twitter usernames (without @)
            tweet_count: Number of tweets to retrieve per user (default: 20)
            comment_count: Number of comments to retrieve per tweet (default: 50)
            ranking_mode: How to rank comments - "Relevance", "Likes", or "Recency"
            table_name: Name of the table to update
            
        Returns:
            Dictionary mapping usernames to success status
        """
        results = {}
        total = len(usernames)
        
        for i, username in enumerate(usernames):
            try:
                self.logger.info(f"Processing {i+1}/{total}: {username}")
                
                # Find user_id from the database
                query = f"SELECT id, posts, sync_at FROM {table_name} WHERE screen_name = ? LIMIT 1"
                result = self.conn.cursor().execute(query, (username,)).fetchone()
                user_id = result[0] if result else None
                posts = result[1] if result else None
                sync_at = result[2] if result else None

                # Check if we have recent posts data
                if result and posts is not None and sync_at is not None and (int(time.time()) - int(sync_at)) < 86400:
                    self.logger.info(f"Using cached posts data for {username} (less than 24 hours old)")
                    results[username] = True
                    continue

                # If we don't have recent posts data, fetch from API
                if not user_id:
                    self.logger.error(f"No user_id found for username: {username} in db, try API")
                    user = self.get_user_by_username(username)
                    if not user:
                        results[username] = False
                        continue
                    
                    user_result = user.get('result', {}).get('data', {}).get('user', {}).get('result', {})
                    self.upsert_user_result_to_db(user_result)
                    user_id = user_result.get('rest_id', None)
                
                # Get tweets for this user
                tweets_data = self.get_user_tweets(user_id, tweet_count)
                
                tweet_ids = []
                timeline_instructions = tweets_data.get('result', {}).get('timeline', {}).get('instructions', [])
                timeline_add_entries = next((instruction for instruction in timeline_instructions 
                                          if instruction.get('type') == 'TimelineAddEntries'), None)
                
                if timeline_add_entries and 'entries' in timeline_add_entries:
                    for entry in timeline_add_entries['entries']:
                        entry_id = entry.get('entryId', '')
                        if entry_id.startswith('tweet-'):
                            tweet_ids.append(entry_id)
                        if entry_id.startswith('profile-conversation-'):
                            all_tweet_ids = entry.get('content', {}).get('metadata', {}).get('conversationMetadata', {}).get('allTweetIds', [])
                            if len(all_tweet_ids) > 0:
                                tweet_ids.append(f'tweet-{all_tweet_ids[0]}')

                if not len(tweet_ids) > 0:
                    self.logger.error(f"No tweets found for user_id: {user_id}")
                    results[username] = False
                    continue
                    
                # Process tweets into the required JSON format
                formatted_tweets = {}

                for i, tweet_entry_id in enumerate(tweet_ids):
                    tweet_id = tweet_entry_id.split('-', 1)[1] if '-' in tweet_entry_id else tweet_entry_id
                    try:
                        comments_data = self.get_tweet_comments_v2(tweet_id, ranking_mode, comment_count)

                        comments_instructions = comments_data.get('result', {}).get('instructions', [])
                        comments_add_entries = next((instruction for instruction in comments_instructions 
                                          if instruction.get('type') == 'TimelineAddEntries'), None)

                        comments_entries = comments_add_entries.get('entries', [])

                        for comment_entry in comments_entries:
                            entry_id = comment_entry.get('entryId', '')
                            if entry_id == tweet_entry_id:
                                tweet_data = comment_entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                                if tweet_data:
                                    try:
                                        self.logger.info(f"Processing tweet data for post: {tweet_id}")
                                        # Extract tweet data
                                        legacy = tweet_data.get('legacy', {})
                                        views = tweet_data.get('views', {})
                                        created_at = legacy.get('created_at', '')
                                        full_text = legacy.get('full_text', '')
                                        views_count = views.get('count', 0)
                                        bookmark_count = legacy.get('bookmark_count', 0)
                                        likes_count = legacy.get('favorite_count', 0)
                                        quote_count = legacy.get('quote_count', 0)
                                        reply_count = legacy.get('reply_count', 0)
                                        retweet_count = legacy.get('retweet_count', 0)

                                        formatted_tweets[tweet_entry_id] = {
                                            "created_at": created_at,
                                            "full_text": full_text,
                                            "views_count": views_count,
                                            "bookmark_count": bookmark_count,
                                            "likes_count": likes_count,
                                            "quote_count": quote_count,
                                            "reply_count": reply_count,
                                            "retweet_count": retweet_count,
                                            "comments": []
                                        }

                                        if i == 0:
                                            self.logger.info(f"Processing user infos for: {tweet_id}")
                                            core = tweet_data.get('core', {})
                                            user_results = core.get('user_results', {})
                                            user = user_results.get('result', {})
                                                
                                            if user:
                                                self.upsert_user_result_to_db(user)
                                            else:
                                                self.logger.warning(f"User data not found for tweet: {tweet_id}")
                                    except Exception as e:
                                        self.logger.error(f"Error processing tweet data or user infos for {tweet_id}: {e}")
                                    continue
                        
                            elif entry_id.startswith('conversationthread-'):
                                self.logger.info(f"Processing comments data for post: {tweet_id}")
                                content_items = comment_entry.get('content', {}).get('items', [])
                                # Safely get the first item from content_items if it exists
                                first_item = content_items[0] if content_items else {}
                                comment_text = first_item.get('item', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {}).get('legacy', {}).get('full_text', '')
                                if 'comments' not in formatted_tweets[tweet_entry_id]:
                                    formatted_tweets[tweet_entry_id]['comments'] = []
                                formatted_tweets[tweet_entry_id]['comments'].append(comment_text)
                    except Exception as e:
                        self.logger.error(f"Error processing comments data for {tweet_id}: {e}")
                        continue
                # Convert to JSON string
                tweets_json = json.dumps(formatted_tweets)
                
                # Update the database
                update_query = f"""
                UPDATE {table_name}
                SET posts = ?,
                sync_at = ?
                WHERE screen_name = ?
                """
                
                self.conn.cursor().execute(update_query, (tweets_json, int(time.time()), username))
                rows_affected = self.conn.cursor().rowcount
                
                # Commit changes for this user
                self.conn.commit()
                
                self.logger.info(f"Successfully saved {len(formatted_tweets)} tweets with comments for {username}, {rows_affected} rows affected")
                results[username] = True
                
            except Exception as e:
                self.logger.error(f"Error processing tweets and comments for {username}: {e}")
                results[username] = False
        
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"Completed batch processing: {success_count}/{total} successful")
        
        return results