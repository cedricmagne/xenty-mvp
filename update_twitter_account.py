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

def update_accounts(db_path: str, table_name: str = "x_cryptos", screen_names: List[str] = None) -> List[str]:
    """
    Update all screen names from the database.
    
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
        if screen_names is None:
            logger.error("screen_names parameter must be NOT NULL")
            return []
        
        # Create proper SQL placeholders for the IN clause
        placeholders = ','.join(['?' for _ in screen_names])
        cursor.execute(f"SELECT id, screen_name FROM {table_name} WHERE screen_name IN ({placeholders})", screen_names)
        
        results = [row[1] for row in cursor.fetchall()]  # Get screen_name (index 1), not id (index 0)
        
        logger.info(f"Found {len(results)} screen names in the database")
        return results
    
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
    Main function to update tweet account ids in the database.
    """
    parser = argparse.ArgumentParser(description="Update tweet account ids in the database")
    parser.add_argument("--db-path", default="data/xenty.db", help="Path to the SQLite database")
    parser.add_argument("--table", default="x_cryptos", help="Name of the table to query")
    parser.add_argument("--accounts", default=None, help="Screen name of the account to update")
    
    args = parser.parse_args()
    
    # Ensure database file exists
    if not os.path.exists(args.db_path):
        logger.error(f"Database file not found: {args.db_path}")
        return
    
    # Check if accounts parameter is provided
    if args.accounts is None:
        logger.error("No accounts specified. Please provide account names using the --accounts parameter.")
        return

    # Get all screen names from the database
    screen_names = update_accounts(args.db_path, args.table, args.accounts.split(","))
    
    if not screen_names:
        logger.error("No screen names found in the database")
        return
    
    logger.info(f"Processing {len(screen_names)} users")
    
    # Initialize TwitterScraper
    try:
        scraper = TwitterScraper(db_path=args.db_path)
        
        # Update all accounts ids
        users = []
        for screen_name in screen_names:
            response = scraper.get_user_by_username(screen_name)
            user_id = response.get("result", {}).get("data", {}).get("user", {}).get("result", {}).get("rest_id", None)
            users.append((user_id, screen_name))

        # Update all accounts ids in the database
        conn = sqlite3.connect(args.db_path)
        cursor = conn.cursor()
        
        # Execute batch update using executemany
        cursor.executemany(f"UPDATE {args.table} SET id = ? WHERE screen_name = ?", users)
        conn.commit()
        conn.close()
        
        # Print summary
        logger.info(f"Completed processing: {len(screen_names)} successful")
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()
