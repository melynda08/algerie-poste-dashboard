import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union, Literal
import os
import json
import pickle
import faiss
from tqdm import tqdm
import requests
from sentence_transformers import SentenceTransformer
import torch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for storing embeddings and indices
EMBEDDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'embeddings')
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

class RAGModel:
    """
    Enhanced RAG (Retrieval Augmented Generation) model using FAISS and embeddings
    Supports multiple embedding providers:
    - Sentence Transformers (local)
    - OpenAI
    - Together AI
    - Hugging Face
    """
    
    def __init__(self, 
                 embedding_provider: str = "local",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG model
        
        Args:
            embedding_provider: Which embedding provider to use: "local", "openai", "together", "huggingface"
            embedding_model: The name/ID of the embedding model to use
        """
        self.embedding_provider = embedding_provider.lower()
        self.embedding_model_name = embedding_model
        
        # Get API keys from environment
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.together_api_key = os.getenv('TOGETHER_API_KEY')
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        
        # Set default embedding dimensions based on common models
        self.embedding_dims = {
            "openai": 1536,  # For text-embedding-3-small
            "together": 1024,  # For e5-large-v2
            "huggingface": 768,  # For most base models
            "local": 384,  # For all-MiniLM-L6-v2
        }
        
        # Initialize the appropriate embedding method
        self._setup_embedding_provider()
        
        self.index = None
        self.documents = []
        self.chunk_size = 100  # Default chunk size for processing large datasets
    
    def _setup_embedding_provider(self):
        """Setup the selected embedding provider"""
        
        # Default to local if requested provider not available
        if self.embedding_provider == "openai" and not self.openai_api_key:
            logger.warning("OpenAI API key not found. Falling back to local embeddings.")
            self.embedding_provider = "local"
            
        elif self.embedding_provider == "together" and not self.together_api_key:
            logger.warning("Together AI API key not found. Falling back to local embeddings.")
            self.embedding_provider = "local"
            
        elif self.embedding_provider == "huggingface" and not self.huggingface_api_key:
            logger.warning("HuggingFace API key not found. Falling back to local embeddings.")
            self.embedding_provider = "local"
        
        # Initialize the proper embedding method based on provider
        if self.embedding_provider == "local":
            self._init_local_model()
        else:
            # For API-based providers, just set the embedding dimension
            self.embedding_dim = self.embedding_dims.get(self.embedding_provider, 768)
            logger.info(f"Using {self.embedding_provider} embeddings with model {self.embedding_model_name}")
        
    def _init_local_model(self):
        """Initialize local embedding model"""
        try:
            self.model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded local Sentence Transformer model: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            # Fall back to a basic model if the requested one fails
            try:
                self.embedding_model_name = "all-MiniLM-L6-v2"  # Default fallback model
                self.model = SentenceTransformer(self.embedding_model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info("Loaded fallback Sentence Transformer model")
            except Exception as e2:
                logger.error(f"Error loading fallback model: {str(e2)}")
                self.model = None
                self.embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
                
    def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embeddings from OpenAI API"""
        try:
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": "text-embedding-3-small"
                }
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error getting OpenAI embedding: {str(e)}")
            # Fall back to local model if OpenAI fails
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim  # Return zero vector if all else fails
    
    def _get_together_embedding(self, text: str) -> List[float]:
        """Get embeddings from Together AI API"""
        try:
            response = requests.post(
                "https://api.together.xyz/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.together_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": self.embedding_model_name or "togethercomputer/m2-bert-80M-8k-retrieval"
                }
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error getting Together AI embedding: {str(e)}")
            # Fall back to local model if Together AI fails
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim  # Return zero vector if all else fails
    
    def _get_huggingface_embedding(self, text: str) -> List[float]:
        """Get embeddings from HuggingFace Inference API"""
        try:
            api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.embedding_model_name}"
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {self.huggingface_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": text,
                    "options": {"wait_for_model": True}
                }
            )
            response.raise_for_status()
            embeddings = response.json()
            # Huggingface returns a list of lists for each token/sentence
            # When using sentence transformers, we take the first embedding which is the sentence embedding
            if isinstance(embeddings, list) and isinstance(embeddings[0], list):
                return embeddings[0]
            return embeddings
        except Exception as e:
            logger.error(f"Error getting HuggingFace embedding: {str(e)}")
            # Fall back to local model if HuggingFace fails
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim  # Return zero vector if all else fails
    
    def _get_embedding_for_text(self, text: str) -> List[float]:
        """Get embedding for a single text string based on selected provider"""
        if self.embedding_provider == "openai":
            return self._get_openai_embedding(text)
        elif self.embedding_provider == "together":
            return self._get_together_embedding(text)
        elif self.embedding_provider == "huggingface":
            return self._get_huggingface_embedding(text)
        else:  # local
            if hasattr(self, 'model') and self.model:
                return self.model.encode(text).tolist()
            return [0] * self.embedding_dim
    
    def _get_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Get embeddings for a batch of texts from selected provider"""
        embeddings = []
        
        # Process in batches
        for i in tqdm(range(0, len(texts), batch_size), desc="Getting embeddings"):
            batch_texts = texts[i:i+batch_size]
            
            try:
                if self.embedding_provider == "local" and hasattr(self, 'model') and self.model:
                    # Local SentenceTransformers - process batch at once
                    batch_embeddings = self.model.encode(batch_texts).tolist()
                    embeddings.extend(batch_embeddings)
                else:
                    # For API providers - process one at a time to handle errors gracefully
                    batch_embeddings = []
                    for text in batch_texts:
                        embedding = self._get_embedding_for_text(text)
                        batch_embeddings.append(embedding)
                    embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error getting batch embeddings: {str(e)}")
                # Return zero vectors if batch fails
                embeddings.extend([[0] * self.embedding_dim for _ in range(len(batch_texts))])
        
        return np.array(embeddings, dtype=np.float32)
    
    def _preprocess_dataframe(self, df: pd.DataFrame, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Convert DataFrame rows to text documents with metadata
        
        Args:
            df: The DataFrame to process
            max_rows: Maximum number of rows to process (for large datasets)
            
        Returns:
            List of dictionaries with text and metadata
        """
        documents = []
        df_sample = df.head(max_rows) if max_rows else df
        
        for idx, row in df_sample.iterrows():
            # Convert row to string representation
            text_parts = []
            metadata = {"row_idx": idx}
            
            for col, val in row.items():
                if pd.notna(val):
                    text_parts.append(f"{col}: {val}")
                    metadata[col] = val
            
            # Join text parts with newlines for better context
            text = "\n".join(text_parts)
            documents.append({
                "text": text,
                "metadata": metadata
            })
        
        return documents
    
    def _chunk_dataframe(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Split large DataFrame into chunks for processing
        
        Args:
            df: The DataFrame to chunk
            
        Returns:
            List of DataFrame chunks
        """
        if len(df) <= self.chunk_size:
            return [df]
        
        chunks = []
        for i in range(0, len(df), self.chunk_size):
            chunks.append(df.iloc[i:i+self.chunk_size])
        
        return chunks
    
    def index_dataframe(self, df: pd.DataFrame, file_id: str = None, force_rebuild: bool = False) -> bool:
        """
        Index DataFrame for retrieval with FAISS
        
        Args:
            df: DataFrame to index
            file_id: Optional ID to save/load embeddings and index
            force_rebuild: Force rebuild index even if cached version exists
        
        Returns:
            True if indexing was successful
        """
        # Check if we can load from cache
        if file_id and not force_rebuild:
            loaded = self._load_index(file_id)
            if loaded:
                logger.info(f"Loaded existing index for file {file_id}")
                return True
        
        # Process dataset in chunks if it's large
        if len(df) > self.chunk_size:
            logger.info(f"Processing large DataFrame with {len(df)} rows in chunks")
            chunks = self._chunk_dataframe(df)
            
            # Process each chunk
            all_documents = []
            all_embeddings = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                chunk_docs = self._preprocess_dataframe(chunk)
                all_documents.extend(chunk_docs)
                
                # Get embeddings for this chunk
                chunk_texts = [doc["text"] for doc in chunk_docs]
                chunk_embeddings = self._get_embeddings_batch(chunk_texts)
                all_embeddings.append(chunk_embeddings)
            
            # Combine all embeddings
            embeddings = np.vstack(all_embeddings)
            self.documents = all_documents
            
        else:
            # Small dataset - process all at once
            self.documents = self._preprocess_dataframe(df)
            texts = [doc["text"] for doc in self.documents]
            embeddings = self._get_embeddings_batch(texts)
        
        # Create FAISS index
        if len(embeddings) > 0:
            try:
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                
                # Create index - using IndexFlatIP for cosine similarity
                self.index = faiss.IndexFlatIP(self.embedding_dim)
                self.index.add(embeddings)
                
                logger.info(f"Created FAISS index with {len(self.documents)} documents")
                
                # Save index if file_id is provided
                if file_id:
                    self._save_index(file_id)
                
                return True
            except Exception as e:
                logger.error(f"Error creating FAISS index: {str(e)}")
                return False
        else:
            logger.error("No embeddings generated")
            return False
    
    def _save_index(self, file_id: str) -> bool:
        """
        Save FAISS index and document data to disk
        
        Args:
            file_id: ID of the file to use in naming
            
        Returns:
            True if save was successful
        """
        if not self.index or not self.documents:
            return False
            
        try:
            file_dir = os.path.join(EMBEDDINGS_DIR, file_id)
            os.makedirs(file_dir, exist_ok=True)
            
            # Save FAISS index
            index_path = os.path.join(file_dir, "index.faiss")
            faiss.write_index(self.index, index_path)
            
            # Save documents
            docs_path = os.path.join(file_dir, "documents.pkl")
            with open(docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
                
            # Save model info
            model_info = {
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                "embedding_dim": self.embedding_dim,
                "document_count": len(self.documents)
            }
            info_path = os.path.join(file_dir, "info.json")
            with open(info_path, 'w') as f:
                json.dump(model_info, f)
                
            logger.info(f"Saved index and documents for file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            return False
    
    def _load_index(self, file_id: str) -> bool:
        """
        Load FAISS index and document data from disk
        
        Args:
            file_id: ID of the file to load
            
        Returns:
            True if load was successful
        """
        file_dir = os.path.join(EMBEDDINGS_DIR, file_id)
        index_path = os.path.join(file_dir, "index.faiss")
        docs_path = os.path.join(file_dir, "documents.pkl")
        info_path = os.path.join(file_dir, "info.json")
        
        # Check if all files exist
        if not (os.path.exists(index_path) and os.path.exists(docs_path) and os.path.exists(info_path)):
            return False
            
        try:
            # Load model info first to check compatibility
            with open(info_path, 'r') as f:
                model_info = json.load(f)
            
            # Check if dimensions match current model
            # If different embedding model/provider was used, we need to rebuild
            if model_info.get("embedding_dim") != self.embedding_dim:
                logger.warning("Embedding dimension mismatch, rebuilding index")
                return False
                
            # Load index
            self.index = faiss.read_index(index_path)
            
            # Load documents
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
                
            return True
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context based on query
        
        Args:
            query: The user query
            top_k: Number of contexts to retrieve
        
        Returns:
            List of context documents with similarity scores
        """
        if not self.index or not self.documents:
            return []
        
        try:
            # Initialize exact_matches before using it
            exact_matches = []
            
            # Check if query contains specific identifiers (like mail item IDs)
            # This is a simple regex to detect alphanumeric IDs that might be in the data
            import re
            id_pattern = r'\b[A-Z0-9]{10,}\b'
            ids = re.findall(id_pattern, query)
        
            # If we found specific IDs, first try to find exact matches
            if ids:
                for doc in self.documents:
                    for id_value in ids:
                        # Check if this ID appears in the document text
                        if id_value in doc["text"]:
                            exact_matches.append({
                                'content': doc["text"],
                                'metadata': doc["metadata"],
                                'similarity': 1.0  # Give exact matches highest similarity
                            })
            
            # If we found exact matches, return them first (up to top_k)
            if exact_matches:
                return exact_matches[:top_k]
        
            # Fall back to vector search if no exact matches or no IDs in query
            # Get query embedding
            query_embedding = np.array([self._get_embedding_for_text(query)], dtype=np.float32)
        
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
        
            # Search index
            scores, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
        
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.documents):  # Skip invalid indices
                    continue
                
                doc = self.documents[idx]
                results.append({
                    'content': doc["text"],
                    'metadata': doc["metadata"],
                    'similarity': float(score)
                })
        
            return results
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    def get_context_for_query(self, df: pd.DataFrame, query: str, 
                              file_id: str = None, top_k: int = 5, 
                              force_rebuild: bool = False) -> Tuple[str, List[Dict]]:
        """
        Get context for a query from DataFrame
        
        Args:
            df: The DataFrame to search
            query: The query string
            file_id: Optional file ID for caching
            top_k: Number of results to retrieve
            force_rebuild: Force rebuilding the index
            
        Returns:
            A tuple of (formatted_context, raw_results)
        """
        # Index the DataFrame if needed
        if not self.index or force_rebuild:
            success = self.index_dataframe(df, file_id, force_rebuild)
            if not success:
                return "Could not create search index for the data.", []
        
        # Initialize direct_matches before using it
        direct_matches = []

        # Check for specific identifiers in the query
        import re
        id_pattern = r'\b[A-Z0-9]{10,}\b'
        ids = re.findall(id_pattern, query)

        # If we found specific IDs, try direct DataFrame filtering first
        if ids:
            logger.info(f"Found potential IDs in query: {ids}")
            
            for id_value in ids:
                # Try to find the ID in any column
                for col in df.columns:
                    matches = df[df[col].astype(str).str.contains(id_value, na=False)]
                    if not matches.empty:
                        logger.info(f"Found direct matches for ID {id_value} in column {col}")
                        for _, row in matches.iterrows():
                            text_parts = []
                            for c, v in row.items():
                                if pd.notna(v):
                                    text_parts.append(f"{c}: {v}")
                            
                            direct_matches.append({
                                'content': "\n".join(text_parts),
                                'metadata': {'row_idx': row.name},
                                'similarity': 1.0
                            })

        # If we found direct matches, use them
        if direct_matches:
            context_str = "Exact matches found in the data:\n\n"
            for i, ctx in enumerate(direct_matches[:top_k], 1):
                context_str += f"{i}. {ctx['content']}\n\n"
            
            return context_str, direct_matches[:top_k]
    
        # Fall back to vector search
        contexts = self.retrieve_context(query, top_k)
        
        if not contexts:
            return "No relevant context found in the data.", []
        
        # Format context as string
        context_str = "Relevant information from the data:\n\n"
        for i, ctx in enumerate(contexts, 1):
            context_str += f"{i}. {ctx['content']}\n\n"
        
        return context_str, contexts
