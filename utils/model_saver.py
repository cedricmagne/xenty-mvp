"""
Model saving and loading utilities for Xenty ML models.
This module provides functions to save and load trained models and their associated transformers.
Uses TensorFlow's SavedModel format for unified model persistence.
"""

import os
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.base import BaseEstimator
from typing import Dict, Tuple, Any, Optional, Union, List

# Configure logging
logger = logging.getLogger(__name__)

def create_models_dir(base_dir: str = None) -> str:
    """
    Create a directory for saving models if it doesn't exist.
    
    Args:
        base_dir: Base directory path. If None, uses the project root.
        
    Returns:
        str: Path to the models directory
    """
    if base_dir is None:
        # Get the project root directory (assuming this file is in utils/)
        base_dir = str(Path(__file__).parent.parent)
    
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    logger.info(f"Models directory: {models_dir}")
    return models_dir

def save_model(
    model: BaseEstimator, 
    scaler: BaseEstimator, 
    engagement_labels: Dict[int, str],
    features: List[str],
    model_name: str = 'engagement_clustering',
    base_dir: str = None
) -> str:
    """
    Save a trained model, scaler, and associated metadata using TensorFlow's SavedModel format.
    
    Args:
        model: Trained model (e.g., KMeans)
        scaler: Fitted scaler (e.g., StandardScaler)
        engagement_labels: Dictionary mapping cluster IDs to engagement labels
        features: List of feature names used for training
        model_name: Name for the saved model files
        base_dir: Base directory path. If None, uses the project root.
        
    Returns:
        str: Path to the saved model directory
    """
    models_dir = create_models_dir(base_dir)
    model_dir = os.path.join(models_dir, model_name)
    os.makedirs(model_dir, exist_ok=True)
    
    # Create a TensorFlow wrapper for the scikit-learn model
    class XentyModel(tf.Module):
        def __init__(self, model, scaler):
            super(XentyModel, self).__init__()
            self.model = model
            self.scaler = scaler
            
        @tf.function(input_signature=[tf.TensorSpec(shape=[None, None], dtype=tf.float32)])
        def predict(self, inputs):
            # Scale the inputs
            scaled_inputs = tf.py_function(
                self.scaler.transform, 
                [inputs], 
                tf.float32
            )
            
            # Make predictions
            predictions = tf.py_function(
                self.model.predict,
                [scaled_inputs],
                tf.int32
            )
            
            return predictions
    
    # Create and save the TensorFlow model
    tf_model = XentyModel(model, scaler)
    tf_model_path = os.path.join(model_dir, "tf_model")
    tf.saved_model.save(tf_model, tf_model_path)
    logger.info(f"TensorFlow model saved to {tf_model_path}")
    
    # Save engagement labels as JSON
    labels_path = os.path.join(model_dir, "engagement_labels.json")
    # Convert int keys to strings for JSON serialization
    json_labels = {str(k): v for k, v in engagement_labels.items()}
    with open(labels_path, 'w') as f:
        json.dump(json_labels, f)
    logger.info(f"Engagement labels saved to {labels_path}")
    
    # Save feature names as JSON
    features_path = os.path.join(model_dir, "features.json")
    with open(features_path, 'w') as f:
        json.dump(features, f)
    logger.info(f"Feature names saved to {features_path}")
    
    # Save metadata as JSON
    metadata = {
        'model_type': type(model).__name__,
        'scaler_type': type(scaler).__name__,
        'num_features': len(features),
        'features': features,
        'num_clusters': len(engagement_labels),
        'engagement_levels': list(engagement_labels.values())
    }
    
    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    logger.info(f"Metadata saved to {metadata_path}")
    
    return model_dir

def load_model(
    model_name: str = 'engagement_clustering',
    base_dir: str = None
) -> Tuple[Any, Any, Dict[int, str], List[str], Dict[str, Any]]:
    """
    Load a saved model, scaler, and associated metadata from TensorFlow SavedModel format.
    
    Args:
        model_name: Name of the model to load
        base_dir: Base directory path. If None, uses the project root.
        
    Returns:
        Tuple containing:
        - model: The trained model (TensorFlow SavedModel)
        - scaler: The fitted scaler (embedded in the TensorFlow model)
        - engagement_labels: Dictionary mapping cluster IDs to engagement labels
        - features: List of feature names used for training
        - metadata: Dictionary containing model metadata
    """
    models_dir = create_models_dir(base_dir)
    model_dir = os.path.join(models_dir, model_name)
    
    if not os.path.exists(model_dir):
        raise FileNotFoundError(f"Model directory not found: {model_dir}")
    
    # Load TensorFlow model
    tf_model_path = os.path.join(model_dir, "tf_model")
    loaded_model = tf.saved_model.load(tf_model_path)
    logger.info(f"TensorFlow model loaded from {tf_model_path}")
    
    # Load engagement labels
    labels_path = os.path.join(model_dir, "engagement_labels.json")
    with open(labels_path, 'r') as f:
        json_labels = json.load(f)
        # Convert string keys back to integers
        engagement_labels = {int(k): v for k, v in json_labels.items()}
    logger.info(f"Engagement labels loaded from {labels_path}")
    
    # Load feature names
    features_path = os.path.join(model_dir, "features.json")
    with open(features_path, 'r') as f:
        features = json.load(f)
    logger.info(f"Feature names loaded from {features_path}")
    
    # Load metadata
    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    logger.info(f"Metadata loaded from {metadata_path}")
    
    # For compatibility with the existing code, we return the loaded TensorFlow model
    # The scaler is embedded in the model, but we return None for compatibility
    return loaded_model, None, engagement_labels, features, metadata

def predict_engagement(
    account_data: Dict[str, Union[float, int]],
    model: Optional[Any] = None,
    scaler: Optional[Any] = None,  # Not used with TF model
    engagement_labels: Optional[Dict[int, str]] = None,
    features: Optional[List[str]] = None,
    model_name: str = 'engagement_clustering',
    base_dir: str = None
) -> Tuple[str, int]:
    """
    Predict engagement level for a new account using the TensorFlow saved model.
    
    Args:
        account_data: Dictionary with account metrics
        model: Pre-loaded TensorFlow model (optional)
        scaler: Not used with TensorFlow model (kept for API compatibility)
        engagement_labels: Pre-loaded engagement labels (optional)
        features: List of feature names (optional)
        model_name: Name of the model to load if not provided
        base_dir: Base directory path. If None, uses the project root.
        
    Returns:
        Tuple containing:
        - engagement_level: Predicted engagement level (e.g., "Fort", "Moyen", "Faible")
        - cluster: Predicted cluster ID
    """
    # Load model components if not provided
    if model is None or engagement_labels is None or features is None:
        model, _, engagement_labels, features, _ = load_model(model_name, base_dir)
    
    # Extract or calculate features
    feature_values = {}
    
    # Handle different input formats
    if 'likes_per_views' in account_data and 'retweets_per_views' in account_data and 'replies_per_views' in account_data:
        # Direct metrics provided
        for feature in features:
            feature_values[feature] = account_data.get(feature, 0)
    else:
        # Need to calculate metrics
        total_views = account_data.get('views', 0)
        if total_views > 0:
            feature_values['likes_per_views'] = account_data.get('likes', 0) / total_views
            feature_values['retweets_per_views'] = account_data.get('retweets', 0) / total_views
            feature_values['replies_per_views'] = account_data.get('replies', 0) / total_views
        else:
            feature_values['likes_per_views'] = 0
            feature_values['retweets_per_views'] = 0
            feature_values['replies_per_views'] = 0
    
    # Create feature array in the correct order
    feature_array = np.array([[feature_values[f] for f in features]], dtype=np.float32)
    
    # Use the TensorFlow model to predict
    cluster = model.predict(feature_array).numpy()[0]
    
    # Get engagement level
    engagement_level = engagement_labels[cluster]
    
    return engagement_level, cluster
