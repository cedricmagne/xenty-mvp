#!/usr/bin/env python3
import sqlite3
import logging
import argparse
import os
from typing import List
from utils.twitter import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

def get_all_screen_names(db_path: str, table_name: str = "x_cryptos") -> List[str]:
    """
    Get all screen names from the database.
    
    Args:
        db_path: Path to the SQLite database
        table_name: Name of the table to query
        
    Returns:
        List of screen names
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            logger.error(f"Table {table_name} does not exist in the database")
            return []
        
        # Check if screen_name column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        if "screen_name" not in columns:
            logger.error(f"Column 'screen_name' does not exist in table {table_name}")
            return []
        
        # Get all screen names
        cursor.execute(f"SELECT screen_name FROM {table_name} WHERE screen_name IS NOT NULL AND market_cap_rank IS NOT NULL ORDER BY market_cap_rank ASC LIMIT 1000")
        screen_names = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(screen_names)} screen names in the database")
        return screen_names
    
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error getting screen names: {e}")
        return []
    finally:
        if conn:
            conn.close()

def main():
    """
    Main function to fetch tweets with comments for 1000 ranked users in the database.
    """
    parser = argparse.ArgumentParser(description="Fetch tweets with comments for 1000 ranked users in the database")
    parser.add_argument("--db-path", default="data/xenty.db", help="Path to the SQLite database")
    parser.add_argument("--table", default="x_cryptos", help="Name of the table to query")
    parser.add_argument("--tweet-count", default="20", help="Number of tweets to retrieve per user")
    parser.add_argument("--comment-count", default="50", help="Number of comments to retrieve per tweet")
    parser.add_argument("--ranking-mode", default="Relevance", choices=["Relevance", "Likes", "Recency"], 
                        help="How to rank comments")
    
    args = parser.parse_args()
    
    # Ensure database file exists
    if not os.path.exists(args.db_path):
        logger.error(f"Database file not found: {args.db_path}")
        return
    
    # Get all screen names from the database
    screen_names = get_all_screen_names(args.db_path, args.table)
    
    if not screen_names:
        logger.error("No screen names found in the database")
        return
    
    logger.info(f"Processing {len(screen_names)} users")
    
    # Initialize TwitterScraper
    try:
        scraper = TwitterScraper(db_path=args.db_path)
        
        # Get tweets with comments for all users
        results = scraper.get_tweets_with_comments(
            usernames=screen_names,
            tweet_count=args.tweet_count,
            comment_count=args.comment_count,
            ranking_mode=args.ranking_mode,
            table_name=args.table
        )
        
        # Print summary
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Completed processing: {success_count}/{len(screen_names)} successful")
        
        # Print failures if any
        failures = [username for username, success in results.items() if not success]
        if failures:
            logger.warning(f"Failed to process {len(failures)} users: {', '.join(failures)}")
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()
