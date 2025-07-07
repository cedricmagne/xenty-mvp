"""
Script to save the trained model from the xenty-ml.ipynb notebook.
This script should be run after executing the notebook to save the trained model.
Uses TensorFlow's SavedModel format for unified model persistence.
"""

import os
import sys
import logging
import tensorflow as tf
from pathlib import Path

# Import the model_saver module
from utils.model_saver import save_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_notebook_model(notebook_namespace):
    """
    Save the model from the notebook's namespace using TensorFlow's SavedModel format.
    
    Args:
        notebook_namespace: The globals() dictionary from the notebook
        
    Returns:
        str: Path to the saved model directory
    """
    # Extract required objects from the notebook namespace
    try:
        kmeans = notebook_namespace.get('kmeans')
        scaler = notebook_namespace.get('scaler')
        features = notebook_namespace.get('features')
        
        # Create engagement_labels dictionary
        engagement_labels = {
            0: "Engagement Équilibré",
            1: "Forte Attraction",
            2: "Faible Engagement",
            3: "Haute Viralité"
        }
        
        if kmeans is None or scaler is None or features is None:
            raise ValueError("Required model components not found in notebook namespace")
        
        # Check if TensorFlow is available
        try:
            import tensorflow as tf
            logger.info(f"Using TensorFlow version {tf.__version__}")
        except ImportError:
            logger.error("TensorFlow is not installed. Please install it with 'pip install tensorflow'")
            raise
        
        # Save the model
        model_dir = save_model(
            model=kmeans,
            scaler=scaler,
            engagement_labels=engagement_labels,
            features=features,
            model_name='engagement_clustering'
        )
        
        logger.info(f"Model successfully saved to {model_dir}")
        return model_dir
        
    except Exception as e:
        logger.error(f"Error saving model: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("This script should be run from within the notebook.")
    logger.info("Add the following code to your notebook:")
    logger.info("""
    # Save the trained model using TensorFlow
    import sys
    from pathlib import Path
    
    # Make sure TensorFlow is installed
    try:
        import tensorflow as tf
        print(f"Using TensorFlow version {tf.__version__}")
    except ImportError:
        !pip install tensorflow
        import tensorflow as tf
        print(f"Installed TensorFlow version {tf.__version__}")
    
    # Add the project root to the path
    project_root = str(Path().absolute())
    sys.path.append(project_root)
    
    # Import and run the save_notebook_model function
    from utils.save_notebook_model import save_notebook_model
    save_notebook_model(globals())
    """)
