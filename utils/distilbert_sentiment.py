import logging
import re
import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFRobertaModel
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define sentiment labels
SENTIMENT_LABELS = ['bearish', 'bullish']
MODEL_NAME = "vinai/bertweet-base"

class XentySentimentAnalyzer:
    def __init__(self, model_path: str):
        """
        Initialize the DistilBERT sentiment analyzer.
        
        Args:
            model_path (str): Path to the h5 model file
        """
        try:
            # Load the tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False, normalization=True)
            
            # Load the model with custom objects
            custom_objects = {'TFRobertaModel': TFRobertaModel}
            self.model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
            
            logging.info(f"Successfully loaded model from {model_path}")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise e
    
    def preprocess_text(self, texts: List[str], max_length: int = 64) -> Dict:
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
    
    def preprocess_crypto_text(self, text: str) -> str:
        """Préprocessing spécifique au domaine crypto"""
        if not text or len(text.strip()) == 0:
            return ""
        
        text = text.strip()
        text = re.sub(r"http\S+", "http", text)
        
        # Normaliser les termes crypto spécifiques
        crypto_normalizations = {
            # Bullish terms
            r'\bto the moon\b': 'very bullish',
            r'\bmoon\b': 'bullish rising',
            r'\brocket\b': 'very bullish',
            r'\blambo\b': 'extremely bullish',
            r'\bhodl\b': 'hold bullish',
            r'\bdiamond hands\b': 'strong hold bullish',
            r'\bbull run\b': 'very bullish market',
            r'\bpump\b': 'price rising bullish',
            r'\bape\b': 'buy bullish',
            r'\blfg\b': 'lets go bullish',
            
            # Bearish terms  
            r'\brug pull\b': 'scam very bearish',
            r'\bdump\b': 'crash very bearish',
            r'\bpaper hands\b': 'weak sell bearish',
            r'\bbear market\b': 'very bearish market',
            r'\bcrash\b': 'very bearish falling',
            r'\brekt\b': 'destroyed very bearish',
            r'\bfud\b': 'fear bearish'
        }
        
        for pattern, replacement in crypto_normalizations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text.strip()

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
            texts = [self.preprocess_crypto_text(text) for text in texts]
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
