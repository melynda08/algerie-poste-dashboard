"""
Configuration module for the application
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define important directories
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
EMBEDDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'embeddings')

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    # Embedding settings
    "embedding_provider": "local",  # local, openai, together, huggingface
    "local_model": "all-MiniLM-L6-v2",
    "openai_model": "text-embedding-3-small",
    "together_model": "togethercomputer/m2-bert-80M-8k-retrieval",
    "huggingface_model": "sentence-transformers/all-mpnet-base-v2",
    
    # RAG settings
    "chunk_size": 100,
    "top_k_results": 5,
    
    # API settings
    "max_upload_size_mb": 5 * 1024,  # 5GB
}

# Runtime configuration (can be modified during runtime)
_config: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults
    
    Returns:
        Dictionary of configuration values
    """
    global _config
    
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    config["embedding_provider"] = os.getenv("EMBEDDING_PROVIDER", config["embedding_provider"])
    config["local_model"] = os.getenv("LOCAL_MODEL", config["local_model"])
    config["openai_model"] = os.getenv("OPENAI_MODEL", config["openai_model"])
    config["together_model"] = os.getenv("TOGETHER_MODEL", config["together_model"])
    config["huggingface_model"] = os.getenv("HUGGINGFACE_MODEL", config["huggingface_model"])
    
    # Check for API keys
    config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    config["together_api_key"] = os.getenv("TOGETHER_API_KEY")
    config["huggingface_api_key"] = os.getenv("HUGGINGFACE_API_KEY")
    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
    
    # Store in runtime config
    _config = config
    
    return config

def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    global _config
    
    # Load config if not already loaded
    if not _config:
        load_config()
    
    return _config.get(key, default)

def set_config(key: str, value: Any) -> None:
    """
    Set a configuration value at runtime
    
    Args:
        key: Configuration key
        value: Configuration value
    """
    global _config
    
    # Load config if not already loaded
    if not _config:
        load_config()
    
    _config[key] = value
    
    # For certain keys, also set environment variable for persistence
    if key in ["embedding_provider", "local_model", "openai_model", "together_model", "huggingface_model"]:
        env_key = key.upper()
        os.environ[env_key] = str(value)

def get_embedding_config() -> Dict[str, Any]:
    """
    Get embedding-specific configuration
    
    Returns:
        Dictionary of embedding configuration
    """
    provider = get_config("embedding_provider")
    
    config = {
        "provider": provider,
        "model": get_config(f"{provider}_model"),
        "api_key": get_config(f"{provider}_api_key"),
    }
    
    return config
