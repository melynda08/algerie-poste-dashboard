"""
Helper module for managing local embedding models
"""
import os
import logging
from typing import Dict, List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for storing downloaded models
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# Cache for loaded models to avoid reloading
_model_cache: Dict[str, SentenceTransformer] = {}

def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> Optional[SentenceTransformer]:
    """
    Get a sentence transformer model, loading from cache if available
    
    Args:
        model_name: Name of the model to load
        
    Returns:
        SentenceTransformer model or None if loading fails
    """
    global _model_cache
    
    # Check if model is already loaded
    if model_name in _model_cache:
        logger.info(f"Using cached model: {model_name}")
        return _model_cache[model_name]
    
    # Try to load the model
    try:
        logger.info(f"Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name, cache_folder=MODELS_DIR)
        _model_cache[model_name] = model
        return model
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {str(e)}")
        
        # Try to load a fallback model if the requested one fails
        if model_name != "all-MiniLM-L6-v2":
            logger.info("Attempting to load fallback model")
            try:
                fallback_model = "all-MiniLM-L6-v2"
                model = SentenceTransformer(fallback_model, cache_folder=MODELS_DIR)
                _model_cache[fallback_model] = model
                return model
            except Exception as e2:
                logger.error(f"Error loading fallback model: {str(e2)}")
        
        return None

def get_embeddings(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Get embeddings for a list of texts using a local model
    
    Args:
        texts: List of text strings to embed
        model_name: Name of the model to use
        
    Returns:
        Numpy array of embeddings
    """
    model = get_embedding_model(model_name)
    
    if model is None:
        # Return zero vectors if model loading fails
        logger.warning("Using zero vectors as fallback")
        embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
        return np.zeros((len(texts), embedding_dim), dtype=np.float32)
    
    # Generate embeddings
    try:
        return model.encode(texts, show_progress_bar=True)
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        embedding_dim = model.get_sentence_embedding_dimension()
        return np.zeros((len(texts), embedding_dim), dtype=np.float32)

def get_embedding_for_text(text: str, model_name: str = "all-MiniLM-L6-v2") -> List[float]:
    """
    Get embedding for a single text string
    
    Args:
        text: Text string to embed
        model_name: Name of the model to use
        
    Returns:
        List of embedding values
    """
    model = get_embedding_model(model_name)
    
    if model is None:
        # Return zero vector if model loading fails
        embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
        return [0.0] * embedding_dim
    
    # Generate embedding
    try:
        return model.encode(text).tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        embedding_dim = model.get_sentence_embedding_dimension()
        return [0.0] * embedding_dim

def list_available_models() -> List[str]:
    """
    List recommended sentence transformer models for embeddings
    
    Returns:
        List of model names
    """
    return [
        "all-MiniLM-L6-v2",  # Fast, small model (384 dimensions)
        "all-mpnet-base-v2",  # Higher quality, larger model (768 dimensions)
        "all-distilroberta-v1",  # Good balance of quality and size (768 dimensions)
        "multi-qa-MiniLM-L6-cos-v1",  # Optimized for retrieval (384 dimensions)
        "paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual support (384 dimensions)
    ]
