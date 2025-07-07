import os
import pandas as pd
import streamlit as st
import kagglehub
import json
import sqlite3
from constants.config import DATASET_NAME, DATASET_KAGGLE_SOURCE
from utils.kaggle_auth import setup_kaggle_credentials
from utils.ui_helpers import show_message, auto_dismiss_toast

# Global configuration for data source
# Can be changed programmatically with set_data_source()
DEFAULT_DATA_SOURCE = "sqlite"

class DataLoader:
    """Class to handle data loading from different sources"""
    
    def __init__(self, data_source=None):
        """Initialize DataLoader with specified data source or use global default"""
        self.data_source = data_source if data_source is not None else DEFAULT_DATA_SOURCE
    
    def _load_from_sqlite(self):
        """Load data from the local SQLite database."""
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "xenty.db")
        
        try:
            if not os.path.exists(db_path):
                return None, "SQLite database not found", False, False
            
            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            
            # Query the x_cryptos table which contains the Twitter/X data
            query = "SELECT * FROM x_cryptos ORDER BY CASE WHEN market_cap_rank IS NULL THEN 999999 ELSE market_cap_rank END ASC"
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Convert posts JSON string to actual JSON objects
            #if 'posts' in df.columns:
            #    df['posts'] = df['posts'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            return df, "Data loaded from SQLite database", True, False
        except Exception as e:
            return None, f"Error loading data from SQLite: {e}", False, False
    
    def _load_from_kaggle(self):
        """Load data from Kaggle or local CSV cache."""
        local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", DATASET_NAME)
        
        try:
            # Check if file exists locally first
            if os.path.exists(local_path):
                # Return with a flag indicating this was loaded from cache (not newly downloaded)
                return pd.read_csv(local_path), "Using locally cached dataset", True, False
            
            # Set up Kaggle credentials before downloading
            try:
                credentials_ready = setup_kaggle_credentials()
                if not credentials_ready:
                    return None, "Kaggle credentials are required to download the dataset", False, False
            except Exception as e:
                return None, f"Error setting up Kaggle credentials: {e}", False, False
            
            # If not available locally, download from Kaggle
            try:
                # Download the dataset from Kaggle
                path = kagglehub.dataset_download(DATASET_KAGGLE_SOURCE)
                kaggle_file_path = os.path.join(path, DATASET_NAME)
                df = pd.read_csv(kaggle_file_path)
                
                # Save to local cache
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                df.to_csv(local_path, index=False)
                
                # Return with a flag indicating this was newly downloaded
                return df, "Dataset downloaded and cached successfully!", True, True
            except Exception as e:
                return None, f"Error downloading dataset: {e}", False, False
        except Exception as e:
            return None, f"Error loading dataset: {e}", False, False
    
    def _load_data_internal(self):
        """Internal method to load data based on the configured data source"""
        if self.data_source == "sqlite":
            return self._load_from_sqlite()
        else:  # kaggle
            return self._load_from_kaggle()
    
    def load(self):
        """Public method to load data and handle UI elements"""
        # Load data directly without caching to ensure we get the latest data
        df, status_message, success, is_new_download = self._load_data_internal()
        
        # Handle UI elements
        if df is not None and success:
            # Only show toast notification if the dataset was newly downloaded
            if is_new_download:
                auto_dismiss_toast(status_message)
            return df
        else:
            st.error(status_message)
            if self.data_source == "kaggle" and "private dataset" in status_message:
                st.error("If this is a private dataset, make sure you have access to it and your credentials are correct.")
            st.stop()
            return None

# Function to set the global default data source
def set_data_source(source):
    """Set the global default data source
    
    Args:
        source (str): Data source to use - "kaggle" or "sqlite"
    """
    global DEFAULT_DATA_SOURCE
    if source in ["kaggle", "sqlite"]:
        DEFAULT_DATA_SOURCE = source
        return True
    return False
