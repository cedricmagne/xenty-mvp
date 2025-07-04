import os
import json
import logging
import streamlit as st
from utils.env_loader import get_env_var

# Set up logging
logging.basicConfig(level=logging.INFO)

def setup_kaggle_credentials():
    """
    Set up Kaggle API credentials from environment variables or Streamlit secrets.
    This function checks for credentials in the following order:
    1. Environment variables (KAGGLE_USERNAME and KAGGLE_KEY)
    2. Streamlit secrets
    3. Prompt the user to enter credentials if not found
    """
    # Check if credentials already exist
    kaggle_dir = os.path.expanduser('~/.kaggle')
    kaggle_file = os.path.join(kaggle_dir, 'kaggle.json')
    
    # If credentials file already exists, we're good
    if os.path.exists(kaggle_file):
        return True
    
    # Try to get credentials from environment variables first
    username = get_env_var('KAGGLE_USERNAME')
    key = get_env_var('KAGGLE_KEY')
    
    # If environment variables are set, use them
    if username and key:
        logging.info(f"Using Kaggle credentials from environment variables for user: {username}")
        # Create the credentials file directly from environment variables
        try:
            os.makedirs(kaggle_dir, exist_ok=True)
            with open(kaggle_file, 'w') as f:
                json.dump({'username': username, 'key': key}, f)
            os.chmod(kaggle_file, 0o600)  # Set permissions to be user-readable only
            logging.info("Created Kaggle credentials file from environment variables")
            return True
        except Exception as e:
            st.error(f"Error creating Kaggle credentials file: {e}")
    # If not in env vars, try Streamlit secrets
    elif hasattr(st, 'secrets'):
        try:
            if 'kaggle' in st.secrets:
                logging.info("Using Kaggle credentials from Streamlit secrets")
                username = st.secrets.kaggle.username
                key = st.secrets.kaggle.key
        except Exception as e:
            logging.warning(f"Error accessing Streamlit secrets: {e}")
            # Continue with username/key as None
    
    # If still not found, prompt the user
    if not (username and key):
        st.warning("Kaggle credentials not found. Please enter your Kaggle credentials to access the dataset.")
        
        with st.form("kaggle_credentials"):
            input_username = st.text_input("Kaggle Username")
            input_key = st.text_input("Kaggle API Key", type="password")
            submitted = st.form_submit_button("Save Credentials")
            
            if submitted and input_username and input_key:
                username = input_username
                key = input_key
                st.success("Credentials saved!")
            elif submitted:
                st.error("Both username and API key are required")
                return False
            else:
                st.info("To find your Kaggle API key, go to your Kaggle account settings and click 'Create New API Token'")
                return False
    
    # Create the credentials file
    if username and key:
        try:
            os.makedirs(kaggle_dir, exist_ok=True)
            with open(kaggle_file, 'w') as f:
                json.dump({'username': username, 'key': key}, f)
            os.chmod(kaggle_file, 0o600)  # Set permissions to be user-readable only
            return True
        except Exception as e:
            st.error(f"Error setting up Kaggle credentials: {e}")
            return False
    
    return False
