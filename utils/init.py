"""
Shared initialization module for Streamlit pages.
Ensures environment variables and logging are properly configured.
"""

import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import environment variables (auto-loads .env when imported)
try:
    from utils.env_loader import get_env_var
    # This import automatically loads environment variables from .env file
except ImportError:
    # Fallback if env_loader is not available
    from dotenv import load_dotenv
    load_dotenv()

# Logger for this module
logger = logging.getLogger(__name__)
logger.info("Initialization module loaded - environment variables and logging configured")
