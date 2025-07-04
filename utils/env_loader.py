import os
import logging
from dotenv import load_dotenv
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)

def load_environment():
    """
    Load environment variables from .env file if it exists.
    
    Returns:
        bool: True if .env file was loaded, False otherwise
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    
    # Load the .env file if it exists
    if os.path.exists(env_path):
        load_dotenv(env_path)
        return True
    else:
        logging.warning("No .env file found")
        return False


# Auto-load environment variables when this module is imported
_env_loaded = load_environment()

def get_env_var(key, default=None):
    """
    Get an environment variable, with an optional default value.
    
    Args:
        key (str): The environment variable name
        default: The default value to return if the variable is not set
        
    Returns:
        The value of the environment variable, or the default value
    """
    return os.environ.get(key, default)


def print_all_env_vars():
    """
    Print all environment variables for debugging purposes
    """
    logging.info("=== Environment Variables ===")
    for key, value in os.environ.items():
        # Mask sensitive values
        if 'KEY' in key or 'SECRET' in key or 'TOKEN' in key or 'PASSWORD' in key:
            masked_value = value[:4] + '****' if value else None
            logging.info(f"{key}: {masked_value}")
        else:
            logging.info(f"{key}: {value}")
    logging.info("============================")
