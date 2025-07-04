import os
import pandas as pd
import streamlit as st
import kagglehub
import json
from constants.config import DATASET_NAME, DATASET_KAGGLE_SOURCE
from utils.kaggle_auth import setup_kaggle_credentials
from utils.ui_helpers import show_message, auto_dismiss_toast

def _load_data_internal():
    """
    Internal function to load data without UI elements.
    Used by the cached wrapper function.
    
    Returns:
        tuple: (DataFrame or None, status_message, success)
    """
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


# This function is cached but contains NO UI elements
@st.cache_data
def _cached_load_data():
    """
    Cached function to load data without ANY UI elements.
    
    Returns:
        tuple: (DataFrame or None, status_message, success, is_new_download)
    """
    return _load_data_internal()

# This is the public function that wraps the cached function and handles UI
def load_data():
    """
    Load the dataset from local cache or download from Kaggle if not available.
    This function handles UI elements separately from the cached logic.
    
    Returns:
        pandas.DataFrame: The loaded dataset
    """
    # Call the cached function that doesn't use any UI elements
    df, status_message, success, is_new_download = _cached_load_data()
    
    # Handle UI elements completely outside any cached function
    if df is not None and success:
        # Only show toast notification if the dataset was newly downloaded
        if is_new_download:
            auto_dismiss_toast(status_message)
        return df
    else:
        st.error(status_message)
        if "private dataset" in status_message:
            st.error("If this is a private dataset, make sure you have access to it and your credentials are correct.")
        st.stop()
        return None
