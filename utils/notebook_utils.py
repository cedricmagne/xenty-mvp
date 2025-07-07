"""
Utility functions for Jupyter notebooks in the xenty project.
"""

import sys
import logging
from pathlib import Path

def setup_notebook_env():
    """
    Set up the notebook environment for proper imports.
    This function should be called at the beginning of each notebook.
    
    This function configures logging and ensures the environment is properly set up.
    It will work even if the xenty package isn't formally installed.
    
    Returns:
        bool: True if setup was successful
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Add the project root to the path if needed
    import sys
    from pathlib import Path
    
    # Get the project root (parent of the directory containing this file)
    project_root = str(Path(__file__).parent.parent)
    
    # Add to path if not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added {project_root} to sys.path")
    
    try:
        # Try to import the xenty package
        import xenty
        logger.info(f"xenty package version {xenty.__version__} loaded successfully")
    except ImportError:
        # If not installed, we can still proceed since we added the project root to sys.path
        logger.info("Using xenty modules directly from the project directory")
    
    logger.info("Notebook environment setup complete")
    return True
