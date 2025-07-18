import logging
import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFDistilBertModel
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define sentiment labels
SENTIMENT_LABELS = ['bearish', 'bullish']

class XentySentimentAnalyzer:
    def __init__(self, model_path: str):
        """
        Initialize the DistilBERT sentiment analyzer.
        
        Args:
            model_path (str): Path to the h5 model file
        """
        try:
            # Load the tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
            
            # Load the model with custom objects
            custom_objects = {'TFDistilBertModel': TFDistilBertModel}
            self.model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
            
            logging.info(f"Successfully loaded model from {model_path}")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise e
    
    def preprocess_text(self, texts: List[str], max_length: int = 256) -> Dict:
        """
        Preprocess text for DistilBERT model.
        
        Args:
            texts (List[str]): List of texts to preprocess
            max_length (int): Maximum sequence length
            
        Returns:
            Dict: Tokenized inputs
        """
        return self.tokenizer(
            texts,
            padding='max_length',
            truncation=True,
            max_length=max_length,
            return_tensors='tf'
        )
    
    def predict_sentiment(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Predict sentiment for a list of texts.
        
        Args:
            texts (List[str]): List of texts to analyze
            
        Returns:
            List[Tuple[str, float]]: List of (sentiment, confidence) tuples
        """
        try:
            # Preprocess the texts
            inputs = self.preprocess_text(texts)
            
            # Make predictions
            predictions = self.model.predict([inputs['input_ids'], inputs['attention_mask']])
            
            results = []
            for pred in predictions:
                # Get the predicted class and confidence
                probabilite = float(pred[0])
                sentiment = SENTIMENT_LABELS[1 if probabilite > 0.5 else 0]
                confidence = float(probabilite * 100)
                results.append((sentiment, confidence))
            
            return results
        except Exception as e:
            logging.error(f"Error predicting sentiment: {e}")
            return [("error", 0.0)] * len(texts)
